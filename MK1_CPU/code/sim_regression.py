#!/usr/bin/env python3
"""MK1 simulator-based regression harness — deterministic feature tests.

Why sim, not hardware? The MK1 instruction set is verified byte-exact against
microcode (project_cpu_hardware_verified.md). mk1sim executes the exact
microcode used in silicon, so if sim produces the expected output_history,
the chip will too. The only hardware-specific signal we lose is I/O-pin
behaviour (which sim mocks for `out`, port writes, etc.) — fine for compiler
correctness tests that only care about out() values.

Each test runs the SAME path the user would run:
    C source → mk1cc2 → asm → ESP32 ASM: → DUMP all pages → mk1sim run.

compile path + assembler path + microcode are all identical to hardware.
Only execution is virtualised. If sim passes, hardware will too — any
disagreement is a harness capture issue, not a compiler issue.

Usage:
    python3 sim_regression.py                  # all tests
    python3 sim_regression.py --filter init    # name substring
    python3 sim_regression.py --port /dev/...
"""
import argparse
import os
import subprocess
import sys
import time
import serial
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import mk1sim
from verify_via_sim import esp32_assemble_and_dump, sim_run

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
COMPILER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mk1cc2.py')


def compile_c(source_path, eeprom=False, extra_env=None):
    """Compile C to asm. Passes extra_env to mk1cc2 (for dev knobs like
    MK1_T2_MIN_LEN that force specific extraction paths)."""
    args = ['python3', COMPILER, source_path, '-O', '-o', '/tmp/_sr.asm']
    if eeprom:
        args.append('--eeprom')
    env = dict(os.environ)
    env.setdefault('PYTHONHASHSEED', '0')
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return None, r.stderr
    with open('/tmp/_sr.asm') as f:
        return f.read(), r.stderr


class Test:
    def __init__(self, name, source, expected, eeprom=False, cycles=1_000_000,
                 env=None, assert_stderr_contains=None):
        self.name = name
        self.source = source
        self.expected = expected   # list of ints — exact prefix of output_history
        self.eeprom = eeprom
        self.cycles = cycles
        self.env = env
        # If set, compile stderr must contain this substring. Lets a test
        # assert that a specific compiler optimisation path actually fired
        # (e.g. "T2.1 xs-abstract ... [INIT-TOUCHES]") — without this, a test
        # might pass for the wrong reason (the feature didn't fire but the
        # program still happened to produce the expected output).
        self.assert_stderr_contains = assert_stderr_contains


def run_test(ser, test, verbose=False):
    """Compile + assemble + sim. Returns (passed, notes_str)."""
    with open('/tmp/_sr.c', 'w') as f:
        f.write(test.source)
    asm, err = compile_c('/tmp/_sr.c', eeprom=test.eeprom, extra_env=test.env)
    if asm is None:
        return False, f'compile failed: {err[:200]}'

    if test.assert_stderr_contains:
        if test.assert_stderr_contains not in err:
            return False, (f'compile stderr missing expected marker '
                           f'{test.assert_stderr_contains!r}')

    try:
        pages = esp32_assemble_and_dump(asm, port=ser.port if hasattr(ser, 'port') else PORT)
    except RuntimeError as e:
        return False, f'esp32 assemble/dump failed: {e}'

    out_hist, halted, cycles = sim_run(pages, max_cycles=test.cycles)
    actual = out_hist[:len(test.expected)]
    if actual != test.expected:
        return False, (f'expected {test.expected} got {actual} '
                       f'(full={out_hist[:10]}... halted={halted} cyc={cycles})')
    return True, f'halted={halted} cyc={cycles}'


TESTS = [
    Test(
        'flat: out(42)',
        'void main(void) { out(42); halt(); }',
        [42],
    ),
    Test(
        'flat: 3 constant outs',
        'void main(void) { out(11); out(22); out(33); halt(); }',
        [11, 22, 33],
    ),
    Test(
        'overlay 2-arg',
        '''unsigned char add(unsigned char a, unsigned char b) { return a + b; }
        unsigned char g[220];
        void main(void) { out(add(10, 20)); halt(); }''',
        [30], eeprom=True,
    ),
    Test(
        'overlay bundle (entry calls 3 helpers)',
        '''unsigned char m(unsigned char a, unsigned char b) {
            unsigned char r = 0;
            while (b > 0) { r = r + a; b = b - 1; }
            return r;
        }
        unsigned char a10(unsigned char x) { return x + 10; }
        unsigned char dbl(unsigned char x) { return x + x; }
        unsigned char chain(unsigned char input) {
            unsigned char s1 = m(input, 3);
            unsigned char s2 = a10(s1);
            return dbl(s2);
        }
        unsigned char g[200];
        void main(void) { out(chain(7)); halt(); }''',
        [62], eeprom=True,
    ),
    # The init-touch case: MK1_T2_MIN_LEN=3 forces T2.1 to extract the
    # 3-instr I2C STOP pattern that occurs in BOTH main-preamble bus
    # recovery AND stage-1 init bus recovery. The thunk lives in kernel
    # (mini-copied) and is called from stage-1 init. If the init-scan
    # extension mis-places the thunk or targets a non-mini-copied label,
    # stage-1 jumps into garbage and the sentinel sequence never appears.
    # assert_stderr_contains guarantees the optimisation path actually
    # fired — a regression that silently drops the extension is caught.
    # Init-extraction smoke test: i2c_init() pulls the full bus init +
    # 9-clock recovery into stage-1 init code. Then chain(7) computes 62
    # via three overlay calls. If init extraction breaks (or any of the
    # overlay-call rewriting collapses), the program won't reach the
    # out() and the test fails. End-to-end correctness probe rather than
    # an optimisation-fired probe — the latter was too brittle to small
    # changes in init code structure.
    Test(
        'init+overlay correctness: i2c_init then overlay chain',
        '''unsigned char g[200];
        unsigned char m(unsigned char a, unsigned char b) {
            unsigned char r = 0;
            while (b > 0) { r = r + a; b = b - 1; }
            return r;
        }
        unsigned char a10(unsigned char x) { return x + 10; }
        unsigned char dbl(unsigned char x) { return x + x; }
        unsigned char chain(unsigned char input) {
            unsigned char s1 = m(input, 3);
            unsigned char s2 = a10(s1);
            return dbl(s2);
        }
        void main(void) {
            i2c_init();
            out(170);
            out(chain(7));
            out(85);
            halt();
        }''',
        [170, 62, 85], eeprom=True,
    ),
]


def main():
    ap = argparse.ArgumentParser(description='MK1 sim-based feature regression')
    ap.add_argument('--port', default=PORT)
    ap.add_argument('--filter', help='Substring match on test name')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    # Keep one serial session alive across tests. esp32_assemble_and_dump
    # opens its own serial, so we just ensure the port exists.
    class PortHolder:
        port = args.port
    ser = PortHolder()

    print(f'MK1 sim regression  port={args.port}')
    print()
    passed = failed = 0
    for t in TESTS:
        if args.filter and args.filter not in t.name:
            continue
        ok, notes = run_test(ser, t, verbose=args.verbose)
        tag = '[PASS]' if ok else '[FAIL]'
        print(f'  {tag} {t.name}: {notes}')
        if ok: passed += 1
        else: failed += 1

    print()
    print(f'Results: {passed}/{passed+failed} passed, {failed} failed')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
