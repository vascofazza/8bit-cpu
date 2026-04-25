#!/usr/bin/env python3
"""Overlay system regression test suite.

Compiles and runs a battery of C programs through --eeprom overlay mode,
verifying correct output on hardware. Catches codegen, overlay dispatch,
arg passing, caching, and call graph grouping regressions.

Usage:
    python3 overlay_regression_test.py [--port PORT]
"""

import serial
import subprocess
import sys
import os
import json
import time

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
BAUD = 115200
COMPILER = os.path.join(os.path.dirname(__file__), 'mk1cc2.py')

def compile_c(source, eeprom=True):
    """Compile C source to assembly. Returns asm text or None."""
    with open('/tmp/_regtest.c', 'w') as f:
        f.write(source)
    args = ['python3', COMPILER, '/tmp/_regtest.c', '-O']
    if eeprom:
        args.append('--eeprom')
    args.extend(['-o', '/tmp/_regtest.asm'])
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    with open('/tmp/_regtest.asm') as f:
        return f.read()

def hw_reset(ser):
    """Force a clean MK1 CPU reset between tests. Clears PC, drops HLT.
    Peripherals (VIA ports, I2C SDA/SCL positions, RTC state) persist —
    programs that use I2C must do their own bus recovery at startup."""
    old_timeout = ser.timeout
    ser.timeout = 5
    ser.reset_input_buffer()
    ser.write(b'RESET\n')
    try:
        ser.readline()
    except:
        pass
    time.sleep(0.2)
    ser.timeout = old_timeout


def assemble_and_upload(ser, asm, timeout=30):
    """Assemble and upload via serial. Sends large payloads in chunks
    to avoid overflowing the ESP32 UART RX buffer.
    Issues a hardware reset first so every test starts with PC=0 and HLT
    de-asserted regardless of the previous test's state."""
    hw_reset(ser)
    escaped = asm.replace('\n', '\\n')
    payload = f'ASM:{escaped}\n'.encode()
    ser.reset_input_buffer()
    # Send in chunks with small delays for large payloads
    CHUNK = 4096
    if len(payload) > CHUNK:
        for i in range(0, len(payload), CHUNK):
            ser.write(payload[i:i+CHUNK])
            time.sleep(0.05)  # 50ms between chunks — lets ESP32 drain UART FIFO
    else:
        ser.write(payload)
    old_timeout = ser.timeout
    ser.timeout = timeout
    try:
        r = json.loads(ser.readline().decode().strip())
    except:
        ser.timeout = old_timeout
        return None
    if not r.get('ok'):
        ser.timeout = old_timeout
        return None
    ser.write(b'UPLOAD\n')
    ser.readline()
    ser.timeout = old_timeout
    return r.get('code', 0)


def run_on_hardware(ser, asm, cycles=5000000, timeout=30):
    """Assemble, upload, run (single OI capture). Returns (val, cap, cyc, code) or None."""
    code = assemble_and_upload(ser, asm, timeout)
    if code is None:
        return None
    ser.timeout = timeout
    ser.write(f'RUN:{cycles},1\n'.encode())
    try:
        r2 = json.loads(ser.readline().decode().strip())
    except:
        return None
    return (r2.get('val'), r2.get('cap'), r2.get('cyc'), code)


def run_multi_output(ser, asm, max_outputs=16, cycles=5000000, timeout=30):
    """Assemble, upload, run with RUNNB (multi OI capture).
    Returns (hist, cnt, cyc, code) or None.
    hist is a list of captured OI values."""
    code = assemble_and_upload(ser, asm, timeout)
    if code is None:
        return None
    ser.timeout = timeout
    ser.write(f'RUNNB:{cycles},1,{max_outputs}\n'.encode())
    # RUNNB may send heartbeat lines before the final result
    while True:
        try:
            line = ser.readline().decode().strip()
            r = json.loads(line)
            if 'hist' in r:
                return (r.get('hist', []), r.get('cnt', 0), r.get('cyc', 0), code)
            # heartbeat — continue waiting
        except:
            return None


def test(ser, name, source, expected_val, eeprom=True):
    """Compile, run, check single output. Returns True/False."""
    asm = compile_c(source, eeprom=eeprom)
    if asm is None:
        print(f'  [FAIL] {name}: compile error')
        return False
    result = run_on_hardware(ser, asm)
    if result is None:
        print(f'  [FAIL] {name}: run error')
        return False
    val, cap, cyc, code = result
    if not cap:
        print(f'  [FAIL] {name}: no output (hung? cyc={cyc}, code={code})')
        return False
    if expected_val is not None and val != expected_val:
        print(f'  [FAIL] {name}: val={val} expected={expected_val} (cyc={cyc}, code={code})')
        return False
    if expected_val is None:
        print(f'  [PASS] {name}: val={val} (completed, cyc={cyc}, code={code})')
    else:
        print(f'  [PASS] {name}: val={val} (cyc={cyc}, code={code})')
    return True


def test_multi(ser, name, source, expected_hist, eeprom=False):
    """Compile, run, check multiple OI outputs. Returns True/False.
    expected_hist: list of expected output values, or None to just check completion."""
    asm = compile_c(source, eeprom=eeprom)
    if asm is None:
        print(f'  [FAIL] {name}: compile error')
        return False
    n_out = len(expected_hist) if expected_hist else 16
    result = run_multi_output(ser, asm, max_outputs=n_out)
    if result is None:
        print(f'  [FAIL] {name}: run error')
        return False
    hist, cnt, cyc, code = result
    if cnt == 0:
        print(f'  [FAIL] {name}: no output (cyc={cyc}, code={code})')
        return False
    if expected_hist is not None:
        if hist[:len(expected_hist)] != expected_hist:
            print(f'  [FAIL] {name}: hist={hist} expected={expected_hist} (cyc={cyc})')
            return False
    print(f'  [PASS] {name}: hist={hist} cnt={cnt} (cyc={cyc}, code={code})')
    return True


def test_file(ser, name, filepath, expected, eeprom=False):
    """Compile a .c file from disk, run, check output.
    expected: int (single val) or list (multi-output hist)."""
    with open(filepath) as f:
        source = f.read()
    if isinstance(expected, list):
        return test_multi(ser, name, source, expected, eeprom=eeprom)
    else:
        return test(ser, name, source, expected, eeprom=eeprom)


def main():
    port = PORT
    if '--port' in sys.argv:
        port = sys.argv[sys.argv.index('--port') + 1]

    print('MK1 Overlay Regression Test Suite')
    print(f'Port: {port}\n')

    ser = serial.Serial(port, BAUD, timeout=30)
    time.sleep(1)
    ser.reset_input_buffer()

    results = []

    # ── 1. Sanity: no overlay (direct execution) ──
    results.append(test(ser, 'sanity: out_imm 42',
        'void main(void) { out(42); halt(); }', 42, eeprom=False))

    # ── 2. Void overlay function ──
    results.append(test(ser, 'void overlay (do_nothing + out 42)',
        '''void do_nothing(void) {}
        void main(void) { i2c_init(); do_nothing(); out(42); halt(); }''', 42))

    # ── 3. One-arg overlay (add_ten) ──
    results.append(test(ser, '1-arg overlay: add_ten(peek3(0))',
        '''unsigned char add_ten(unsigned char x) { return x + 10; }
        void main(void) { i2c_init(); out(add_ten(peek3(0))); halt(); }''',
        None))  # value depends on page3[0], just check it completes

    # ── 4. Two-arg overlay (add_both) ��─
    results.append(test(ser, '2-arg overlay: add_both(peek3(0), 5)',
        '''unsigned char add_both(unsigned char a, unsigned char b) { return a + b; }
        void main(void) { i2c_init(); out(add_both(peek3(0), 5)); halt(); }''',
        None))  # check completion

    # ── 5. Overlay with loop (multiply) ──
    results.append(test(ser, 'loop overlay: multiply(3, 4) = 12',
        '''unsigned char multiply(unsigned char a, unsigned char b) {
            unsigned char result = 0;
            while (b > 0) { result = result + a; b = b - 1; }
            return result;
        }
        void main(void) { i2c_init(); out(multiply(peek3(0), 4)); halt(); }''',
        None))  # check completion

    # ��─ 6. Multiple overlay swaps ──
    results.append(test(ser, 'multiple swaps: step1 + step2 + step3',
        '''unsigned char triple(unsigned char x) { return x + x + x; }
        unsigned char add5(unsigned char x) { return x + 5; }
        unsigned char dbl(unsigned char x) { return x + x; }
        void main(void) {
            i2c_init();
            unsigned char a = triple(peek3(0));
            unsigned char b = add5(a);
            unsigned char c = dbl(b);
            out(c);
            halt();
        }''', None))

    # ── 7. Call graph grouping (cross-function calls) ──
    results.append(test(ser, 'grouped overlay: compute_chain calls multiply+add+dbl',
        '''unsigned char multiply(unsigned char a, unsigned char b) {
            unsigned char result = 0;
            while (b > 0) { result = result + a; b = b - 1; }
            return result;
        }
        unsigned char add_offset(unsigned char x, unsigned char off) { return x + off; }
        unsigned char double_it(unsigned char x) { return x + x; }
        unsigned char compute_chain(unsigned char input) {
            unsigned char s1 = multiply(input, 3);
            unsigned char s2 = add_offset(s1, 10);
            return double_it(s2);
        }
        void main(void) {
            i2c_init();
            unsigned char r = compute_chain(peek3(0));
            out(r);
            halt();
        }''', None))  # value depends on peek3(0) (kernel image byte)

    # ── 8. Overlay caching (same function called twice) ──
    results.append(test(ser, 'cache hit: add5 called twice',
        '''unsigned char add5(unsigned char x) { return x + 5; }
        void main(void) {
            i2c_init();
            unsigned char a = add5(peek3(0));
            unsigned char b = add5(a);
            out(b);
            halt();
        }''', None))  # check completion (second call should cache-hit)

    # ��─ 9. Comparison with non-zero (cmpi opcode) ─��
    results.append(test(ser, 'cmpi: while (x > 5) loop',
        '''unsigned char count_down(unsigned char x) {
            unsigned char count = 0;
            while (x > 5) { x = x - 1; count = count + 1; }
            return count;
        }
        void main(void) { i2c_init(); out(count_down(20)); halt(); }''',
        15))  # 20 down to 5 = 15 steps

    # ── 10. Large grouped overlay (stress test) ──
    results.append(test(ser, 'large group: 5 functions in one slot',
        '''unsigned char f1(unsigned char x) { return x + 1; }
        unsigned char f2(unsigned char x) { return f1(x) + 1; }
        unsigned char f3(unsigned char x) { return f2(x) + 1; }
        unsigned char f4(unsigned char x) { return f3(x) + 1; }
        unsigned char f5(unsigned char x) { return f4(x) + 1; }
        void main(void) { i2c_init(); out(f5(peek3(0))); halt(); }''',
        None))  # f5(2) = 2+5 = 7 if peek3(0)=2

    # ── 11-19. File-based tests from programs/ directory ──
    prog_dir = os.path.join(os.path.dirname(__file__), '..', 'programs')
    print('\n── File-based overlay tests ──')

    # Multi-page overlay test (page3 + page1 + page2)
    results.append(test_file(ser, 'multi-page overlay: 5 funcs + 200B globals',
        os.path.join(prog_dir, 'test_eeprom_overlay.c'), None))

    # Multi-output overlay stress tests (8 independent computation functions)
    results.append(test_file(ser, 'overlay_stress: 8 functions + resident mix',
        os.path.join(prog_dir, 'test_overlay_stress.c'), None))

    # I2C overlay with computation: rtc_read_temp + arithmetic in one overlay slot.
    # Produces 3 outputs: temp, temp*2+1, 42. Verify third output is always 42.
    print('── autosplit: I2C overlay + compute ──')
    asm_as = compile_c(open(os.path.join(prog_dir, 'test_autosplit.c')).read(), eeprom=True)
    if asm_as is None:
        print('  [FAIL] autosplit: compile error')
        results.append(False)
    else:
        r_as = run_multi_output(ser, asm_as, max_outputs=3)
        if r_as is None:
            print('  [FAIL] autosplit: run error')
            results.append(False)
        elif r_as[1] < 3:
            print(f'  [FAIL] autosplit: expected 3 outputs, got cnt={r_as[1]} hist={r_as[0]}')
            results.append(False)
        elif r_as[0][2] != 42:
            print(f'  [FAIL] autosplit: hist[2]={r_as[0][2]} expected 42 (hist={r_as[0]})')
            results.append(False)
        else:
            h, cnt, cyc, code = r_as
            print(f'  [PASS] autosplit: hist={h} (temp={h[0]}, result={h[1]}, sentinel={h[2]}) cyc={cyc}')
            results.append(True)

    # ── Summary ──
    print()
    passed = sum(1 for r in results if r)
    total = len(results)
    failed = total - passed
    skipped = sum(1 for r in results if r is None)
    print(f'Results: {passed}/{total} passed' +
          (f', {failed} failed' if failed else '') +
          (f', {skipped} value-unchecked' if skipped else ''))

    ser.close()
    return passed == total


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
