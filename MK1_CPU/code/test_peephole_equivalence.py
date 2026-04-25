#!/usr/bin/env python3
"""Equivalence test for peephole register inc/dec collapse.

Runs each `mov $X,$a; inc|dec; mov $a,$X` 3-instruction pattern and its
single-byte counterpart (incX/decX) through the simulator and compares
(A, B, C, D, ZF, CF) state after execution.

Covers boundary values (0, 1, 127, 128, 254, 255) for all three
registers and both operations — 48 check cases total.

Guards against microcode errors in the new opcodes: if simulator
output diverges from the expanded form, the peephole collapse is
unsound and the compiler must not emit the new opcode for that case.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mk1sim import MK1, assemble_simple, ucode_template

DECODE = {v[0]: k for k, v in ucode_template.items()}


def run_sequence(init_regs, instrs):
    cpu = MK1()
    for r, v in init_regs.items():
        setattr(cpu, r, v)
    code = assemble_simple(instrs + [DECODE['hlt']])
    cpu.load_program(code)
    cpu.run(max_cycles=200)
    return (cpu.A, cpu.B, cpu.C, cpu.D, cpu.ZF, cpu.CF)


def main():
    pairs = [
        ('B', 'move $b, $a', 'move $a, $b', 'decb', 'incb'),
        ('C', 'move $c, $a', 'move $a, $c', 'decc', 'incc'),
        ('D', 'move $d, $a', 'move $a, $d', 'decd', 'incd'),
    ]
    boundary = [0, 1, 5, 127, 128, 200, 254, 255]

    total = 0
    failed = 0
    for reg, mvTo, mvFrom, cDec, cInc in pairs:
        for op_name, collapsed in [('dec', cDec), ('inc', cInc)]:
            for v in boundary:
                init = {reg: v, 'A': 99}  # 99 = detectable garbage in A
                expanded = run_sequence(init, [DECODE[mvTo], DECODE[op_name],
                                               DECODE[mvFrom]])
                single = run_sequence(init, [DECODE[collapsed]])
                total += 1
                if expanded != single:
                    failed += 1
                    print(f'MISMATCH {reg}={v} {op_name}')
                    print(f'  expanded  (A,B,C,D,Z,C) = {expanded}')
                    print(f'  collapsed (A,B,C,D,Z,C) = {single}')

    print(f'{total - failed}/{total} equivalence checks pass')
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
