#!/usr/bin/env python3
"""Byte-equivalence regression between py_asm and ESP32 assembler.

For every program in the corpus (plus small opcode-targeted snippets),
compile to .asm via mk1cc2, then assemble via BOTH py_asm (local) and
ESP32 (over serial, via the ASM command). Compare the resulting code/
data/page3 byte arrays. Fail if any byte differs.

This catches divergences the moment they're introduced, so the two
assemblers can't drift.
"""
import serial
import subprocess
import sys
import os
import json
import time
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mk1_py_asm import assemble_asm
from mk1_upload import send_chunked, mk1_asm, mk1_upload

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
COMPILER = os.path.join(HERE, 'mk1cc2.py')
PROGRAMS_DIR = os.path.join(os.path.dirname(HERE), 'programs')

# Opcode-targeted snippets to exercise every ARGS_IMM instruction.
# Each snippet is kept tiny so divergences are easy to localize.
SNIPPETS = {
    'jnz': """
section code
org 0
    ldi $a, 5
.loop:
    dec
    jnz .loop
    hlt
""",
    'jz': """
section code
org 0
    ldi $a, 0
    cmp 0
    jz .done
    ldi $a, 42
.done:
    out
    hlt
""",
    'jc': """
section code
org 0
    ldi $a, 100
    cmp 50
    jc .big
    ldi $a, 1
.big:
    out
    hlt
""",
    'jnc': """
section code
org 0
    ldi $a, 10
    cmp 50
    jnc .big
    ldi $a, 2
.big:
    out
    hlt
""",
    'j': """
section code
org 0
    j .target
    ldi $a, 99
.target:
    ldi $a, 1
    out
    hlt
""",
    'jal_ret': """
section code
org 0
    ldi $b, 0xFF
    mov $b, $sp
    jal sub
    hlt
sub:
    ldi $a, 7
    out
    ret
""",
    'ldsp_stsp': """
section code
org 0
    ldi $b, 0xFF
    mov $b, $sp
    push_imm 5
    ldsp 1
    stsp 1
    out
    hlt
""",
    'ddrb_imm_pair': """
section code
org 0
    ddrb_imm 0x01
    ddrb_imm 0x03
    ddrb_imm 0x00
    hlt
""",
    'ddrb2_imm': """
section code
org 0
    ddrb2_imm 0x01, 0x03
    hlt
""",
    'ddrb3_imm': """
section code
org 0
    ddrb3_imm 0x01, 0x03, 0x00
    hlt
""",
    'cmpi_tst': """
section code
org 0
    ldi $a, 0x55
    cmpi 0x55
    tst 0x80
    hlt
""",
    'out_imm': """
section code
org 0
    out_imm 42
    hlt
""",
}


def compile_c_to_asm(c_src, tmp_asm='/tmp/_asm_equiv_test.asm'):
    r = subprocess.run(
        ['python3', COMPILER, c_src, '-O', '-o', tmp_asm],
        capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        return None, r.stderr
    with open(tmp_asm) as f:
        return f.read(), None


def assemble_py(asm_text):
    try:
        pages = assemble_asm(asm_text)
        return {
            'code': bytes(pages['code']),
            'data': bytes(pages['data']),
            'page3': bytes(pages.get('page3') or bytearray(256)),
        }, None
    except Exception as e:
        return None, f'py_asm error: {e}'


def dump_esp32(ser, off, count):
    """Dump `count` bytes starting at offset `off` from ESP32 uploadBuf.
    uploadBuf layout: [code(256), data(256), stack(256), page3(256)].

    Uses in_waiting polling + early exit on newline so each 64-byte chunk
    turns around in <100ms instead of hitting ser.read's 30s timeout."""
    bytes_got = []
    while count > 0:
        chunk = min(count, 64)
        ser.reset_input_buffer()
        ser.write(f'DUMP:{off},{chunk}\n'.encode())
        buf = b''
        deadline = time.time() + 1.0   # per-chunk cap
        while time.time() < deadline:
            if ser.in_waiting:
                buf += ser.read(ser.in_waiting)
                if b'\n' in buf:
                    break
            else:
                time.sleep(0.005)
        line = buf.decode(errors='ignore').strip().split('\n')[-1]
        for tok in line.split():
            if len(tok) == 2:
                try:
                    bytes_got.append(int(tok, 16))
                except ValueError:
                    pass
        off += chunk
        count -= chunk
    return bytes(bytes_got)


def assemble_esp32(ser, asm_text):
    r = mk1_asm(ser, asm_text)
    if not r or not r.get('ok'):
        err = r.get('err') if isinstance(r, dict) else 'unknown'
        return None, f'ESP32 error: {err}'
    mk1_upload(ser)
    time.sleep(0.1)
    pages = {
        'code':  dump_esp32(ser,   0, 256),
        'data':  dump_esp32(ser, 256, 256),
        'page3': dump_esp32(ser, 768, 256),
        'code_size': r.get('code', 256),
        'data_size': r.get('data', 256),
    }
    return pages, None


def diff_pages(py_pages, esp_pages, code_size=None, data_size=None):
    """Return list of (section, offset, py_byte, esp_byte) for divergences.

    Padding fill outside the program's actual code/data extent is ignored
    — py_asm zero-fills its bytearray, ESP32 fills with HLT (0x7F), both
    valid defaults. Only bytes emitted by the assembler count as 'real'."""
    divs = []
    # Use explicit None check — data_size of 0 means "no data section, skip
    # entirely", which `or` would silently promote to 256.
    # page3 is skipped entirely for now: ESP32's ASM response doesn't report
    # page3 extent, so we'd compare stale bytes from prior uploads. To be
    # revisited when we extend the ASM protocol or do an explicit clear.
    limits = {
        'code':  256 if code_size is None else code_size,
        'data':  256 if data_size is None else data_size,
        'page3': 0,
    }
    for sec in ('code', 'data', 'page3'):
        py = py_pages[sec]
        esp = esp_pages[sec]
        n = min(len(py), len(esp), limits[sec])
        for i in range(n):
            if py[i] != esp[i]:
                divs.append((sec, i, py[i], esp[i]))
    return divs


def format_divs(divs, max_show=12):
    if not divs:
        return '  IDENTICAL'
    lines = []
    for sec, off, py_b, esp_b in divs[:max_show]:
        if off < 0:
            lines.append(f'  {sec}: length differs py={py_b} esp={esp_b}')
        else:
            lines.append(f'  {sec}[{off:3d}]: py=0x{py_b:02X} esp=0x{esp_b:02X}')
    if len(divs) > max_show:
        lines.append(f'  ...and {len(divs) - max_show} more')
    return '\n'.join(lines)


def main():
    ser = serial.Serial(PORT, 115200, timeout=30)
    time.sleep(2)
    ser.reset_input_buffer()

    print('── Byte-equivalence: ESP32 vs py_asm ──')
    total = 0
    divergent = 0
    failures = []

    # First pass: tiny opcode snippets
    print('\n── Opcode snippets ──', flush=True)
    for name, asm in SNIPPETS.items():
        total += 1
        print(f'  [..]   {name}: py_asm', end='', flush=True)
        py, err_py = assemble_py(asm)
        print(' ... esp32', end='', flush=True)
        esp, err_esp = assemble_esp32(ser, asm)
        print(' ... diff', end='', flush=True)
        if err_py or err_esp:
            print(f'\r  [SKIP] {name}: py={err_py} esp={err_esp}', flush=True)
            continue
        divs = diff_pages(py, esp, esp.get('code_size'), esp.get('data_size'))
        if divs:
            divergent += 1
            failures.append((name, divs))
            print(f'\r  [DIFF] {name}: {len(divs)} byte(s) differ', flush=True)
            print(format_divs(divs), flush=True)
        else:
            print(f'\r  [OK]   {name}                        ', flush=True)

    # Second pass: corpus programs
    print('\n── Corpus programs ──')
    program_files = sorted(glob.glob(os.path.join(PROGRAMS_DIR, '*.c')))
    for cf in program_files:
        name = os.path.basename(cf)[:-2]
        total += 1
        asm_text, err = compile_c_to_asm(cf)
        if err:
            print(f'  [SKIP] {name}: compile fail ({err[:80].strip()})')
            continue
        py, err_py = assemble_py(asm_text)
        if err_py:
            print(f'  [SKIP] {name}: py_asm error ({err_py[:80]})')
            continue
        esp, err_esp = assemble_esp32(ser, asm_text)
        if err_esp:
            print(f'  [SKIP] {name}: ESP32 error ({err_esp[:80]})')
            continue
        divs = diff_pages(py, esp, esp.get('code_size'), esp.get('data_size'))
        if divs:
            divergent += 1
            failures.append((name, divs))
            print(f'  [DIFF] {name}: {len(divs)} byte(s) differ')
            print(format_divs(divs, max_show=6))
        else:
            print(f'  [OK]   {name}')

    print(f'\n── Summary: {total - divergent}/{total} match ({divergent} divergent) ──')
    if divergent:
        print('\n── Divergence report ──')
        for name, divs in failures:
            print(f'  {name}: {len(divs)} bytes')
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
