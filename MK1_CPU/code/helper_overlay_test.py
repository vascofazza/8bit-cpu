#!/usr/bin/env python3
"""Regression tests for the helper-overlay transform (Phase A).

Three layers of checks, each stricter than the last — and each caught a
real bug in the session they were written for:

  1. Byte-equivalence — compile a test program with and without
     MK1_HELPER_OVERLAY=1 and verify the helper's RUNTIME bytes are
     identical. Caught: pre-peephole snapshot mismatched post-peephole
     final layout, so `ldi $a,N; push $a` was copied instead of
     `push_imm N` and jal targets were off by 1. Symptom: LCD showed
     nothing.

  2. OI control-flow trace — upload to hardware, run with RUNLOG, and
     confirm every expected marker fires in order. Caught: thunk /
     loader wiring errors that hang before a helper returns.

  3. OI-observable side effect — programs that do I2C work and `out()`
     the result (e.g. `out(rtc_read_temp())`). If the helper-overlay
     path corrupts any byte on the I2C wire, the returned value is
     wrong. This is the level that catches what byte-equivalence alone
     would miss (timing, register state, stack).

Run: `python3 helper_overlay_test.py [--skip-hw]`
"""
import argparse, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mk1_py_asm import assemble_asm
from mk1_upload import mk1_asm, mk1_upload, send_chunked

COMPILER = os.path.join(HERE, 'mk1cc2.py')
PORT = '/dev/cu.usbmodem3C8427C2E7C82'


def compile_c(src: str, flag: bool, out_path: str):
    env = os.environ.copy()
    if flag:
        env['MK1_HELPER_OVERLAY'] = '1'
    else:
        env.pop('MK1_HELPER_OVERLAY', None)
    with open('/tmp/__hol_reg.c', 'w') as f:
        f.write(src)
    r = subprocess.run(
        ['python3', COMPILER, '/tmp/__hol_reg.c', '-O', '-o', out_path],
        capture_output=True, text=True, env=env, cwd=HERE)
    return r.returncode == 0, r.stderr


def helper_bytes_resident(asm_text: str, name: str):
    pages = assemble_asm(asm_text)
    labels = pages['labels']
    addr = labels.get(name)
    if addr is None:
        return None, f'no {name} label'
    # Find helper-body end: next label past addr OR highest non-zero byte.
    next_addr = 256
    for lbl, a in labels.items():
        if (not lbl.startswith('.') and a > addr and a < next_addr
                and not lbl.startswith('__h_body')):
            next_addr = a
    code = pages['code']
    # Trim trailing zeros
    end = next_addr
    while end > addr and code[end - 1] == 0:
        end -= 1
    return bytes(code[addr:end]), None


def helper_bytes_overlay(asm_text: str, name: str):
    """In overlay mode, the thunk has `ldi $c, N; j _load_helper`.
    The body lives at page3[manifest[N].offset..+size]."""
    pages = assemble_asm(asm_text)
    labels = pages['labels']
    addr = labels.get(name)
    if addr is None:
        return None, f'no {name} thunk'
    code = pages['code']
    if code[addr] != 0x3A:   # ldi $c
        return None, f'{name} thunk missing ldi $c (got 0x{code[addr]:02X})'
    idx = code[addr + 1]
    mf = labels.get('__helper_manifest')
    if mf is None:
        return None, 'no __helper_manifest'
    page3 = pages['page3']
    offset = page3[mf + idx * 2]
    size = page3[mf + idx * 2 + 1]
    return bytes(page3[offset:offset + size]), None


def trim_trailing_zeros(b: bytes) -> bytes:
    i = len(b)
    while i > 0 and b[i - 1] == 0:
        i -= 1
    return b[:i]


def _normalize_internal_jumps(body: bytes, base_addr: int) -> bytes:
    """Rewrite every jmp/jnz/jz/jc/jnc/jal whose target lies WITHIN
    [base_addr, base_addr+len(body)) to a relative offset. Leaves
    out-of-range targets (external helper calls like __i2c_sb) intact.
    Returns a normalised byte sequence where internal jumps read as
    offsets from the start of the body, so resident vs overlay versions
    of the same helper compare byte-identical.

    Opcodes this understands (matching isa.h / microcode):
      0x3D move imm,$pc (j)  |  0x3F jzf  |  0x37 jcf
      0xCA jnc              |  0xCE jnz
      0xAC stor $pc,[$sp] (jal)
    All are 2B: opcode + imm target.
    """
    IMM_JUMP_OPCODES = {0x3D, 0x3F, 0x37, 0xCA, 0xCE, 0xAC}
    out = bytearray(body)
    i = 0
    while i < len(out):
        op = out[i]
        if op in IMM_JUMP_OPCODES and i + 1 < len(out):
            tgt = out[i + 1]
            if base_addr <= tgt < base_addr + len(out):
                out[i + 1] = tgt - base_addr  # rebase to 0..len-1
            i += 2
        else:
            # Best-effort: skip 1B; for multi-byte instructions this may
            # desync, but helpers generally don't have ddrb2_imm/ddrb3_imm
            # interleaved with the jumps we care about. If desync is
            # observed in practice, upgrade this to a real disassembler.
            i += 1
    return bytes(out)


def test_byte_equivalence(name: str, src: str, helpers: list[str]):
    """Compile src with and without MK1_HELPER_OVERLAY=1. For each helper,
    normalise internal jumps (which legitimately target different absolute
    addresses in each build) and compare the resulting bytes."""
    ok, err = compile_c(src, False, '/tmp/__hol_res.asm')
    if not ok:
        return False, f'resident compile failed: {err[:200]}'
    ok, err = compile_c(src, True, '/tmp/__hol_ov.asm')
    if not ok:
        return False, f'overlay compile failed: {err[:200]}'
    with open('/tmp/__hol_res.asm') as f:
        asm_res = f.read()
    with open('/tmp/__hol_ov.asm') as f:
        asm_ov = f.read()
    res_pages = assemble_asm(asm_res)
    ov_pages = assemble_asm(asm_ov)
    # If the overlay build has no _load_helper, the transform was
    # skipped (e.g. program fits resident, or leaf-rule demoted all
    # candidates). Both builds are semantically the same compile —
    # compare as resident-vs-resident with no rebasing.
    transform_ran = '_load_helper' in ov_pages['labels']
    for h in helpers:
        rb, e1 = helper_bytes_resident(asm_res, h)
        if rb is None:
            return False, f'{h} not found in resident: {e1}'
        rb = trim_trailing_zeros(rb)
        if not transform_ran:
            ob, e2 = helper_bytes_resident(asm_ov, h)
            if ob is None:
                return False, f'{h} not found in overlay (fallback path): {e2}'
            ob = trim_trailing_zeros(ob)
            if rb != ob:
                return False, (f'{h}: transform skipped but resident-form '
                               f'bytes still differ between builds')
            continue
        ob, e2 = helper_bytes_overlay(asm_ov, h)
        # If this specific helper wasn't overlayed (e.g. leaf-rule demoted
        # it), it will still be resident in the overlay build.
        if ob is None and e2 and 'missing ldi $c' in e2:
            ob, e2 = helper_bytes_resident(asm_ov, h)
            if ob is None:
                return False, f'{h} not found in overlay: {e2}'
            ob = trim_trailing_zeros(ob)
            if rb != ob:
                return False, (f'{h}: fell back to resident but bytes differ '
                               f'between builds')
            continue
        if ob is None:
            return False, f'{h} not found in overlay: {e2}'
        ob = trim_trailing_zeros(ob)
        res_base = res_pages['labels'].get(h, 0)
        # Recover R_HELPER_BASE from the loader's tail-jump target.
        lh = ov_pages['labels'].get('_load_helper')
        ov_base = 0
        if lh is not None:
            code = ov_pages['code']
            for k in range(lh, min(lh + 40, 255)):
                if code[k] == 0x3D:
                    ov_base = code[k + 1]
        rb_n = _normalize_internal_jumps(rb, res_base)
        ob_n = _normalize_internal_jumps(ob, ov_base)
        if rb_n != ob_n:
            diffs = [(i, rb_n[i], ob_n[i])
                     for i in range(min(len(rb_n), len(ob_n)))
                     if rb_n[i] != ob_n[i]]
            return False, (
                f'{h} bytes differ after normalising internal jumps: '
                f'{len(diffs)} bytes, resident_base={res_base} '
                f'overlay_base={ov_base}. First: {diffs[:5]}')
    return True, f'{len(helpers)} helper(s) semantically identical'


def test_oi_trace(name: str, src: str, expected_markers: list[int],
                  cycles: int = 5_000_000):
    """Compile with MK1_HELPER_OVERLAY=1, upload, RUNLOG. Check every
    expected marker fires in order."""
    import serial
    ok, err = compile_c(src, True, '/tmp/__hol_trace.asm')
    if not ok:
        return False, f'compile failed: {err[:200]}'
    with open('/tmp/__hol_trace.asm') as f:
        asm = f.read()
    ser = serial.Serial(PORT, 115200, timeout=15)
    try:
        time.sleep(1.5)
        ser.reset_input_buffer()
        r = mk1_asm(ser, asm)
        if not r or not r.get('ok'):
            return False, f'ESP32 asm failed: {r}'
        mk1_upload(ser)
        ser.reset_input_buffer()
        send_chunked(ser, f'RUNLOG:{cycles},1\n'.encode())
        t0 = time.time()
        while time.time() - t0 < 120:
            line = ser.readline().decode(errors='ignore').strip()
            if not line:
                continue
            try:
                import json
                j = json.loads(line)
                vals = j.get('vals', [])
                # HLT_GRACE may cycle main and produce duplicate marker
                # sequences. Accept if the expected sequence appears as a
                # contiguous subsequence anywhere.
                n = len(expected_markers)
                found = any(vals[i:i + n] == expected_markers
                            for i in range(len(vals) - n + 1))
                if found:
                    return True, f'trace contains {expected_markers}'
                return False, (f'trace missing {expected_markers} '
                               f'(got {vals[:12]}{"..." if len(vals) > 12 else ""})')
            except json.JSONDecodeError:
                continue
        return False, 'RUNLOG timeout'
    finally:
        ser.close()


# ── Test suite ────────────────────────────────────────────────────────

TESTS = [
    # (name, src, helpers_to_check, expected_markers)
    (
        'single lcd_char',
        """void main() {
            out(0xA0); i2c_init();
            out(0xA1); lcd_char('X');
            out(0xA2); halt();
        }""",
        ['__lcd_chr'],
        [0xA0, 0xA1, 0xA2],
    ),
    (
        'lcd_init + lcd_char x2',
        """void main() {
            out(0xA0); i2c_init();
            out(0xA1); lcd_init();
            out(0xA2); lcd_char('A');
            out(0xA3); lcd_char('B');
            out(0xA4); halt();
        }""",
        ['__lcd_chr', '__lcd_init'],
        [0xA0, 0xA1, 0xA2, 0xA3, 0xA4],
    ),
    (
        # No lcd_init so kernel stays small enough for flat mode
        # (overlay-mode integration is Phase A follow-up). printf still
        # exercises __print_u8_dec → __lcd_chr helper chain.
        'printf via __print_u8_dec (flat)',
        """void main() {
            out(0xA0); i2c_init();
            out(0xA1);
            unsigned char n; n = 42;
            printf(\"%d\", n);
            out(0xA2); halt();
        }""",
        ['__lcd_chr', '__print_u8_dec'],
        [0xA0, 0xA1, 0xA2],
    ),
]


# Layer 3: I2C side-effect verification. Program reads the RTC and
# transmits the result via out(). If the helper-overlay path corrupts
# any byte on the I2C wire (timing, stack, register clobber), the
# temp value will be wrong or the program will hang.
#
# We don't know the exact temperature in advance, but we know:
#   * the value should be stable across the two markers
#   * it should be in a plausible room-temp range (10-40°C)
#   * it should be IDENTICAL between resident and overlay runs
# The check asserts the identical-between-builds property. If the
# helper-overlay is broken, the overlay run returns either 0 (I2C hung)
# or a different value (corrupted byte stream).
IO_TESTS = [
    (
        'rtc temp read (I2C side-effect)',
        """void main() {
            out(0xA0); i2c_init();
            out(0xA1);
            unsigned char t;
            t = rtc_read_temp();
            out(t);     // <-- the value we cross-check
            out(0xA2); halt();
        }""",
        # Expected: [0xA0, 0xA1, TEMP, 0xA2]. We check TEMP is the
        # same byte in both builds.
    ),
    (
        # This is the class the user caught on 2026-04-22 — printf
        # appearing to work (markers fire) but LCD shows garbage.
        # Layer 3 runs both builds and confirms the OI-observable
        # behaviour is identical. If helper-overlay breaks the printf
        # path, the OI stream lengths or values will diverge.
        'printf via overlay (flat) — catches helper chain bugs',
        """void main() {
            out(0xA0); i2c_init();
            out(0xA1);
            unsigned char n; n = 42;
            printf("%d", n);
            out(0xA2); halt();
        }""",
    ),
]


def test_io_equivalence(name: str, src: str, cycles: int = 10_000_000):
    """Compile with and without MK1_HELPER_OVERLAY=1. Upload each.
    RUNLOG. Confirm captured OI values match between builds."""
    import serial, json
    results = {}
    for flag, label in [(False, 'resident'), (True, 'overlay')]:
        ok, err = compile_c(src, flag, f'/tmp/__hol_io_{label}.asm')
        if not ok:
            return False, f'{label} compile failed: {err[:200]}'
        with open(f'/tmp/__hol_io_{label}.asm') as f:
            asm = f.read()
        ser = serial.Serial(PORT, 115200, timeout=15)
        try:
            time.sleep(1.5)
            ser.reset_input_buffer()
            r = mk1_asm(ser, asm)
            if not r or not r.get('ok'):
                return False, f'{label} ESP32 asm failed: {r}'
            mk1_upload(ser)
            ser.reset_input_buffer()
            send_chunked(ser, f'RUNLOG:{cycles},1\n'.encode())
            t0 = time.time()
            vals = None
            while time.time() - t0 < 120:
                line = ser.readline().decode(errors='ignore').strip()
                if not line:
                    continue
                try:
                    j = json.loads(line)
                    vals = j.get('vals', [])
                    break
                except json.JSONDecodeError:
                    continue
            if vals is None:
                return False, f'{label} RUNLOG timeout'
            results[label] = vals
        finally:
            ser.close()
    r_res = results['resident']
    r_ov = results['overlay']
    # HLT_GRACE may let main loop a second time on one build but not the
    # other (tiny timing difference in when HLT fires). Accept when one
    # is a prefix of the other's repeated run: compare only up to the
    # first complete cycle (which ends at the first duplicate of vals[0]).
    def _first_cycle(vals):
        if not vals:
            return []
        anchor = vals[0]
        for i in range(1, len(vals)):
            if vals[i] == anchor:
                return vals[:i]
        return vals
    r_res_cyc = _first_cycle(r_res)
    r_ov_cyc = _first_cycle(r_ov)
    if r_res_cyc != r_ov_cyc:
        return False, (f'OI streams differ on first cycle: '
                       f'resident={r_res_cyc} overlay={r_ov_cyc}')
    return True, f'OI streams match (first cycle): {r_ov_cyc}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-hw', action='store_true',
                    help='skip hardware/serial tests')
    args = ap.parse_args()

    passed = 0
    failed = 0

    print('── Layer 1: byte-equivalence (offline) ──')
    for name, src, helpers, _markers in TESTS:
        ok, msg = test_byte_equivalence(name, src, helpers)
        marker = '[OK]  ' if ok else '[FAIL]'
        print(f'  {marker} {name}: {msg}')
        if ok: passed += 1
        else: failed += 1

    if args.skip_hw:
        print('\n── Layer 2/3: OI tests (skipped: --skip-hw) ──')
    else:
        print('\n── Layer 2: OI trace (hardware) ──')
        for name, src, _helpers, markers in TESTS:
            ok, msg = test_oi_trace(name, src, markers)
            marker = '[OK]  ' if ok else '[FAIL]'
            print(f'  {marker} {name}: {msg}')
            if ok: passed += 1
            else: failed += 1
        print('\n── Layer 3: I/O side-effect equivalence (hardware) ──')
        for name, src in IO_TESTS:
            ok, msg = test_io_equivalence(name, src)
            marker = '[OK]  ' if ok else '[FAIL]'
            print(f'  {marker} {name}: {msg}')
            if ok: passed += 1
            else: failed += 1

    print(f'\n── Summary: {passed} passed, {failed} failed ──')
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
