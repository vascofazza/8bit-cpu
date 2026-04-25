#!/usr/bin/env python3
"""Regression test: parse/serialize every corpus program's asm and
verify byte-for-byte identity. Any mismatch is a T1.1 parser bug."""
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from mk1ir import round_trip_identical

COMPILER = 'mk1cc2.py'


def main():
    programs = sorted(glob.glob(
        '/Users/gadyke/8bit-cpu/MK1_CPU/programs/*.c'))
    passed = 0
    failed = 0
    skipped = 0
    failures = []
    for p in programs:
        name = os.path.basename(p)
        r = subprocess.run(
            ['python3', COMPILER, p, '-o', '/tmp/_rt.asm'],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            skipped += 1
            continue
        with open('/tmp/_rt.asm') as f:
            lines = f.readlines()
        ok, diff = round_trip_identical(lines)
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append((name, diff))

    print(f'parsed: {passed + failed}')
    print(f'  round-trip identical: {passed}')
    print(f'  mismatches: {failed}')
    print(f'  skipped (compile-fail): {skipped}')
    for name, diff in failures[:20]:
        print(f'  {name}: {diff}')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
