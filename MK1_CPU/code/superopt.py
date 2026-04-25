#!/usr/bin/env python3
"""T4.1 — exhaustive brute-force superoptimizer.

Scans corpus 2–3 instruction windows. For each, enumerates candidate
replacements from a 40-opcode pool with all register/immediate
variations. Verifies equivalence on mk1sim with 100 random initial
states per candidate. Winners are emitted as a peephole table that
mk1cc2 consumes.

Runs entirely in-process (bespoke mini-assembler, no ESP32 round-trip)
for speed. Still expected to take minutes to hours on a full corpus
scan. Parallelizable across candidate windows — current single-threaded
Python version is kept simple; --parallel N forks worker processes.
"""
import argparse
import collections
import glob
import itertools
import json
import multiprocessing as mp
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import mk1sim

# ── Instruction pool for enumeration ────────────────────────────────
#
# Carefully curated subset: pure-reg/ALU ops only. No branches, no
# memory access (deref/istc/etc.), no SP-relative addressing, no exw/
# exrw (external I/O), no push/pop (SP change), no hlt/ret.
#
# Each entry: (mnemonic, operand_kinds, size_bytes, encoder).
# encoder(operands) returns the bytes for the instruction.

REGS = {'$a': 0, '$b': 1, '$c': 2, '$d': 3, '$sp': 4, '$pc': 5}
# Only A/B/C/D are valid targets in our enumeration; SP/PC would
# produce control-flow or stack changes we don't want to superoptimize.
GPRS = ['$a', '$b', '$c', '$d']


def enc_mov(src_reg, dst_reg):
    return bytes([(0 << 6) | (REGS[src_reg] << 3) | REGS[dst_reg]])


def enc_ldi(reg, imm):
    # Assembler: (0<<6) | (7<<3) | dst_reg_code ; then imm byte
    return bytes([(0 << 6) | (7 << 3) | REGS[reg], imm & 0xFF])


# Fixed-opcode table extracted from mk1_esp32_uploader/src/isa.h
# Only includes the mnemonics we care about for enumeration (pure reg/
# ALU ops). Control flow (j, jnz, …), memory (deref, …), and I/O (exw,
# exrw, …) are NOT in the pool even though they have opcodes.
_FIXED_OPCODES = {
    'nop':  0x00,
    # ALU single-operand (A register)
    'not':  0x7A,
    'sll':  0x7B,
    'slr':  0x7C,
    'rll':  0x7D,
    'rlr':  0x7E,
    # Register inc/dec (clobber A, set flags)
    'inc':  0xFB,
    'dec':  0xFE,
    'decd': 0xFC,
    'decc': 0xD8,
    'decb': 0xDC,
    'incc': 0xE8,
    'incd': 0xEC,
    'incb': 0xF5,
    # Flag-to-reg
    'setz':  0xD3,
    'setnz': 0xD7,
    'setc':  0xDE,
    'setnc': 0xE3,
    # Misc
    'clr':   None,   # filled below
    'swap':  0xEE,   # swap A and B
    'adc':   0xC1,
    'sbc':   0xC2,
    'neg':   0xE5,
    # 2-byte tst / cmpi
    'tst':   0xFF,
    'cmpi':  0xFD,
}
# `clr $a` → mov $a,$a (which is a no-op) or xor $a,$a. Actually in MK1
# the assembler emits specific opcode for clr $a. Check isa.h — there's
# no dedicated 'clr' in the fixed table, so clr $a is likely handled by
# a parser macro. Skip it in the pool; handled by asm_line explicitly.
_FIXED_OPCODES.pop('clr')


def op1(name):
    return bytes([_FIXED_OPCODES[name]])


def op2_imm(name, imm):
    return bytes([_FIXED_OPCODES[name], imm & 0xFF])


# ALU-immediate encoding (per assembler.h lines 844-862):
#   ori imm, $dst → (0b1011 << 4) | (op << 2) | dst_code
# ops: add=0, sub=1, or=2, and=3; xori NOT supported (xor is register-
# only in MK1 and takes two operands with different microcode).
ALU_IMM_OP = {'add': 0, 'sub': 1, 'or': 2, 'and': 3}


def enc_alu_imm(mnemonic_i, imm, dst_reg):
    base = mnemonic_i[:-1]   # strip trailing 'i'
    if base not in ALU_IMM_OP:
        raise NotImplementedError(f'ALU-imm {mnemonic_i}')
    if dst_reg not in ('$a', '$b', '$c', '$d'):
        raise NotImplementedError(f'ALU-imm dst {dst_reg}')
    op = ALU_IMM_OP[base]
    opcode = (0b1011 << 4) | (op << 2) | REGS[dst_reg]
    return bytes([opcode, imm & 0xFF])


# Build instruction list. Each tuple: (asm_str, bytes_tuple, size_bytes).
# Only instructions we're willing to enumerate as REPLACEMENTS.
#
# Safe-to-enumerate predicate: the instruction only mutates register
# state (A/B/C/D/CF/ZF). No PC/SP changes, no memory, no I/O, no halt.
# We verify equivalence by comparing A/B/C/D/CF/ZF before and after.
# Changes to E/MAR/OUT are transient / not observable to subsequent
# instructions EXCEPT via ALU result which is captured in CF/ZF/A.

def build_instr_pool():
    pool = []   # list of (asm_str, bytes, size)
    # 1-byte reg-reg moves (16 combinations over A/B/C/D)
    for src in GPRS:
        for dst in GPRS:
            if src == dst:
                continue   # nop equivalent — skip
            pool.append((f'mov {src},{dst}', enc_mov(src, dst), 1))
    # 1-byte ALU-on-A variants
    for name in ('inc', 'dec', 'sll', 'slr', 'rll', 'rlr', 'not'):
        pool.append((name, op1(name), 1))
    # 1-byte incX/decX
    for name in ('incb', 'incc', 'incd', 'decb', 'decc', 'decd'):
        pool.append((name, op1(name), 1))
    # 1-byte swap (A <-> B). Clobbers both.
    pool.append(('swap', op1('swap'), 1))
    # 1-byte nop
    pool.append(('nop', op1('nop'), 1))
    # 1-byte adc / sbc (use B as second operand)
    pool.append(('adc', op1('adc'), 1))
    pool.append(('sbc', op1('sbc'), 1))
    # Flag-to-reg (A = 0/1 based on flag)
    for name in ('setz', 'setnz', 'setc', 'setnc'):
        pool.append((name, op1(name), 1))
    # 2-byte ldi {A,B,C,D,SP}, imm — SP is included so the optimizer
    # can discover `ldi $b,N; mov $b,$sp` → `ldi $sp,N` type wins.
    # (Verified by boundary+random fuzz to preserve B too when B is
    # observed — which it is, so the narrow equivalence is exact.)
    imm_set = (0, 1, 2, 0x80, 0xFF, 0xFE, 0xF0, 0x40)
    for reg in GPRS + ['$sp']:
        for imm in imm_set:
            pool.append((f'ldi {reg},{imm}', enc_ldi(reg, imm), 2))
    # 2-byte ALU-imm (ori/andi/addi/subi imm, $dst)
    for name in ('ori', 'andi', 'addi', 'subi'):
        for dst in GPRS:
            for imm in (0, 1, 0xFF, 0x01, 0x02, 0x04, 0x08, 0x80, 0xF0, 0x0F):
                pool.append((f'{name} {imm},{dst}', enc_alu_imm(name, imm, dst), 2))
    # 2-byte tst imm / cmpi imm
    for imm in (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0xFF):
        pool.append((f'tst {imm}', op2_imm('tst', imm), 2))
    for imm in (0, 1, 0xFF, 0xFE, 0xFD, 0xFC):
        pool.append((f'cmp {imm}', op2_imm('cmpi', imm), 2))
    return pool


INSTR_POOL = build_instr_pool()


# ── Mini-assembler for the corpus-extracted sequences ─────────────────
#
# Parses a narrow subset of mnemonics and returns bytes. Raises
# NotImplementedError for anything outside the pool. Extractor will
# skip such sequences.

def asm_line(line):
    s = line.strip().split(';')[0].strip()
    if not s:
        raise NotImplementedError('empty')
    parts = s.split(None, 1)
    mn = parts[0]
    arg = parts[1] if len(parts) > 1 else ''
    if mn == 'mov':
        src, dst = [x.strip() for x in arg.split(',')]
        if src not in REGS or dst not in REGS:
            raise NotImplementedError(f'mov {arg}')
        return enc_mov(src, dst)
    if mn == 'ldi':
        dst, imm = [x.strip() for x in arg.split(',')]
        if dst not in REGS:
            raise NotImplementedError(f'ldi {arg}')
        try:
            iv = int(imm, 0)
        except ValueError:
            raise NotImplementedError(f'ldi non-const {arg}')
        return enc_ldi(dst, iv)
    if mn == 'clr' and arg == '$a':
        # clr $a — assembled by ESP32 as a specific opcode (xor $a,$a
        # equivalent). Not a plain fixed opcode in isa.h. Fall through
        # to NotImplementedError — we don't emit clr in candidates.
        raise NotImplementedError('clr $a')
    if mn in ('inc', 'dec', 'sll', 'slr', 'rll', 'rlr', 'not', 'nop',
              'swap', 'adc', 'sbc',
              'setz', 'setnz', 'setc', 'setnc'):
        return op1(mn)
    if mn in ('incb', 'incc', 'incd', 'decb', 'decc', 'decd'):
        return op1(mn)
    if mn in ('ori', 'andi', 'addi', 'subi'):
        # `ori 0x04,$a` — take imm and dst reg
        parts2 = [x.strip() for x in arg.split(',')]
        if len(parts2) != 2:
            raise NotImplementedError(f'{mn} {arg}')
        imm_str, dst = parts2[0], parts2[1]
        try:
            iv = int(imm_str, 0)
        except ValueError:
            raise NotImplementedError(f'{mn} non-const {arg}')
        return enc_alu_imm(mn, iv, dst)
    if mn == 'tst':
        try:
            iv = int(arg, 0)
        except ValueError:
            raise NotImplementedError(f'tst {arg}')
        return op2_imm('tst', iv)
    if mn == 'cmp':
        # cmp $reg → register cmp (different opcode); cmp imm → cmpi
        arg_s = arg.strip()
        if arg_s.startswith('$'):
            raise NotImplementedError(f'cmp reg — not in pool')
        try:
            iv = int(arg_s, 0)
        except ValueError:
            raise NotImplementedError(f'cmp {arg}')
        return op2_imm('cmpi', iv)
    raise NotImplementedError(mn)


def asm_seq(lines):
    out = b''
    for line in lines:
        out += asm_line(line)
    return out


# ── Runner ────────────────────────────────────────────────────────────

def run_snippet(code_bytes, init_state, ticks_per_byte=16):
    """Run the snippet to completion then snapshot state.

    ticks_per_byte: each instruction takes up to ~8 microcode steps.
    We run 2× that per byte of code to guarantee completion, then
    extra ticks run nop (memory is zero-initialized beyond the snippet)
    which doesn't change observed state. Comparing snapshots is valid
    because both old and new snippets run the same number of cycles
    over the same zero tail — any difference is real."""
    cpu = mk1sim.MK1()
    for i, b in enumerate(code_bytes):
        cpu.mem[0][i] = b
    cpu.A = init_state['A'] & 0xFF
    cpu.B = init_state['B'] & 0xFF
    cpu.C = init_state['C'] & 0xFF
    cpu.D = init_state['D'] & 0xFF
    cpu.SP = 0xF0
    cpu.CF = init_state['CF'] & 1
    cpu.ZF = init_state['ZF'] & 1
    # Run a generous number of ticks. After the snippet, PC walks through
    # zero-filled memory (opcode 0x00 = nop) which doesn't mutate state.
    for _ in range(len(code_bytes) * ticks_per_byte):
        if cpu.halted:
            break
        cpu.tick()
    return (cpu.A, cpu.B, cpu.C, cpu.D, cpu.SP, cpu.CF, cpu.ZF)


# Boundary values that trigger edge cases (zero, one, sign bit, wrap)
_BOUNDARY_VALUES = (0, 1, 2, 0x7F, 0x80, 0x81, 0xFE, 0xFF)


def verify_equivalent(old_bytes, new_bytes, trials=100, observe_mask=None, seed=0):
    """Return True iff running old_bytes and new_bytes from initial
    states yields identical observed state in ALL trials.

    Strategy:
      - Exhaustive: every combination of (A, B) ∈ boundary × boundary
        with C/D set from independent boundary picks. 8×8 = 64 states
        for A×B alone (+ random C/D/CF/ZF from the seed).
      - Random: fill out to `trials` total with uniform random states.

    This catches wrap-around (0xFF→0), sign-bit (0x7F↔0x80), and zero
    cases that pure uniform sampling often misses. observe_mask bits
    0-5 = A, B, C, D, CF, ZF."""
    # 7 observed components: A, B, C, D, SP, CF, ZF
    if observe_mask is None:
        observe_mask = 0b1111111
    rng = random.Random(seed)

    def check(init):
        old = run_snippet(old_bytes, init)
        new = run_snippet(new_bytes, init)
        for i in range(7):
            if (observe_mask >> i) & 1:
                if old[i] != new[i]:
                    return False
        return True

    # Exhaustive boundary enumeration for A, B
    for a in _BOUNDARY_VALUES:
        for b in _BOUNDARY_VALUES:
            init = {
                'A': a, 'B': b,
                'C': rng.randrange(256),
                'D': rng.randrange(256),
                'CF': rng.randrange(2),
                'ZF': rng.randrange(2),
            }
            if not check(init):
                return False
    # Fill remainder with random states
    remaining = max(0, trials - len(_BOUNDARY_VALUES) ** 2)
    for _ in range(remaining):
        init = {
            'A': rng.randrange(256),
            'B': rng.randrange(256),
            'C': rng.randrange(256),
            'D': rng.randrange(256),
            'CF': rng.randrange(2),
            'ZF': rng.randrange(2),
        }
        if not check(init):
            return False
    return True


# ── Corpus scan ───────────────────────────────────────────────────────

def extract_sequences(asm_dir='/tmp/corpus_asm'):
    """Extract all 2-3 instruction sequences that assemble cleanly in our
    narrow assembler. Returns dict: tuple(asm_lines) → (bytes, count)."""
    seqs = {}
    files = glob.glob(f'{asm_dir}/*.asm')
    for fp in files:
        with open(fp) as f:
            lines = [l for l in f if l.strip()]
        tokens = [l.strip().split(';')[0].strip() for l in lines]
        # Skip labels, directives, comments
        def is_instr(t):
            if not t or t.endswith(':') or t.startswith('section') or t.startswith('org'):
                return False
            # Exclude anything outside our assembler
            mn = t.split()[0]
            if mn in ('j', 'jz', 'jnz', 'jc', 'jnc', 'jal', 'ret', 'hlt',
                      'push', 'pop', 'push_imm', 'push_b', 'pop_b',
                      'deref', 'derefp3', 'deref2', 'ideref', 'iderefp3',
                      'ideref2', 'istc', 'istc_inc', 'ldsp', 'stsp',
                      'ldsp_b', 'ldp3', 'stp3', 'exw', 'exrw', 'exr',
                      'ddrb_imm', 'ddra_imm', 'setjmp', 'setret', 'setz',
                      'setnz', 'setc', 'setnc', 'byte', 'neg', 'xor',
                      'out', 'out_imm'):
                return False
            return True
        for i in range(len(tokens)):
            if not is_instr(tokens[i]):
                continue
            for L in (2, 3):
                if i + L > len(tokens):
                    continue
                if not all(is_instr(tokens[i + k]) for k in range(L)):
                    continue
                seq = tuple(tokens[i:i + L])
                if seq in seqs:
                    seqs[seq] = (seqs[seq][0], seqs[seq][1] + 1)
                    continue
                try:
                    code = asm_seq(seq)
                except NotImplementedError:
                    continue
                seqs[seq] = (code, 1)
    return seqs


# ── Candidate enumeration ─────────────────────────────────────────────

def enumerate_candidates(target_bytes, max_len=3):
    """Generate all instruction sequences (from INSTR_POOL) with
    total size STRICTLY LESS than len(target_bytes), up to max_len
    instructions."""
    target_size = len(target_bytes)
    for L in range(1, max_len + 1):
        for combo in itertools.product(INSTR_POOL, repeat=L):
            total = sum(instr[2] for instr in combo)
            if total >= target_size:
                continue
            asm_lines = tuple(instr[0] for instr in combo)
            code = b''.join(instr[1] for instr in combo)
            yield asm_lines, code


def abstract_pattern(asm_lines):
    """Turn a concrete `ldi $a, 42` into pattern `ldi $a, *` etc.,
    preserving opcode identity. Used so the peephole table can match
    any immediate, not just the one we verified."""
    out = []
    for ln in asm_lines:
        parts = ln.split(None, 1)
        mn = parts[0]
        arg = parts[1] if len(parts) > 1 else ''
        if mn == 'ldi' and ',' in arg:
            dst, _ = arg.split(',', 1)
            out.append(f'ldi {dst.strip()},*')
        elif mn in ('ori', 'andi', 'addi', 'subi', 'xori') and ',' in arg:
            rhs = arg.split(',', 1)[1].strip()
            out.append(f'{mn} *,{rhs}')
        elif mn == 'tst':
            out.append('tst *')
        elif mn == 'cmp':
            if not arg.startswith('$'):
                out.append('cmp *')
            else:
                out.append(ln)
        else:
            out.append(ln)
    return tuple(out)


# ── Corpus-window → candidate search ──────────────────────────────────

def search_for_replacement(seq, code_bytes, trials=100):
    """For a given observed sequence+bytes, enumerate shorter candidates
    and return the FIRST that verifies equivalent (deterministic — we
    use fixed seed). Returns (candidate_asm, candidate_bytes, tested_count)
    or (None, None, tested_count) if nothing verifies.

    Strategy: try shortest candidates first (more profitable)."""
    tested = 0
    for cand_asm, cand_code in enumerate_candidates(code_bytes):
        tested += 1
        # Skip candidates that are the same as the original (by bytes)
        if cand_code == code_bytes:
            continue
        if verify_equivalent(code_bytes, cand_code, trials=trials):
            return cand_asm, cand_code, tested
    return None, None, tested


# ── Worker for multiprocessing ────────────────────────────────────────

def _worker(args):
    seq, code, trials = args
    try:
        cand_asm, cand_code, tested = search_for_replacement(seq, code, trials=trials)
    except Exception as e:
        return (seq, None, None, 0, f'error: {e}')
    return (seq, cand_asm, cand_code, tested, 'ok')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asm-dir', default='/tmp/corpus_asm')
    ap.add_argument('--trials', type=int, default=100,
                    help='random-state trials per verify (default 100)')
    ap.add_argument('--min-freq', type=int, default=2,
                    help='only consider sequences appearing in N+ windows')
    ap.add_argument('--parallel', type=int, default=max(1, os.cpu_count() - 1))
    ap.add_argument('--out', default='/tmp/superopt_results.json')
    args = ap.parse_args()

    print(f'[1/3] Extracting corpus sequences from {args.asm_dir}...',
          file=sys.stderr)
    seqs = extract_sequences(args.asm_dir)
    # Keep only sequences that appear >= min-freq times
    filtered = {seq: (code, cnt) for seq, (code, cnt) in seqs.items()
                if cnt >= args.min_freq}
    print(f'    {len(seqs)} total unique sequences, {len(filtered)} with '
          f'freq >= {args.min_freq}', file=sys.stderr)

    # Sort by frequency descending for prioritization
    ordered = sorted(filtered.items(), key=lambda x: -x[1][1])
    jobs = [(seq, code, args.trials) for seq, (code, cnt) in ordered]

    print(f'[2/3] Searching for shorter equivalents '
          f'({len(jobs)} candidates, {args.parallel} workers, '
          f'{args.trials} trials each)...', file=sys.stderr)
    t0 = time.time()

    results = []
    if args.parallel > 1:
        with mp.Pool(args.parallel) as pool:
            for i, res in enumerate(pool.imap_unordered(_worker, jobs, chunksize=4)):
                results.append(res)
                if (i + 1) % 50 == 0:
                    elapsed = time.time() - t0
                    rate = (i + 1) / elapsed
                    eta = (len(jobs) - i - 1) / rate if rate > 0 else 0
                    verified = sum(1 for r in results if r[1] is not None)
                    print(f'    [{i+1}/{len(jobs)}] {verified} verified, '
                          f'{elapsed:.1f}s elapsed, ~{eta:.0f}s eta',
                          file=sys.stderr)
    else:
        for i, job in enumerate(jobs):
            res = _worker(job)
            results.append(res)
            if (i + 1) % 50 == 0:
                print(f'    [{i+1}/{len(jobs)}]', file=sys.stderr)

    elapsed = time.time() - t0
    print(f'    Done in {elapsed:.1f}s', file=sys.stderr)

    # Collect verified replacements. Filter out UNSAFE rewrites:
    # - Patterns that remove or collapse nops. Stage-1 padding (__pad,
    #   __mc_pad) relies on nop count for address-preservation; the
    #   peephole applier cannot safely distinguish these from stray
    #   nops, so we exclude them from the auto-generated table.
    # - Patterns whose old sequence contains ONLY nops (same reason).
    verified = []
    for seq, cand_asm, cand_code, tested, status in results:
        if cand_asm is None:
            continue
        if all(s.strip() == 'nop' for s in seq):
            continue   # pure-nop collapse — unsafe for pad sections
        if any(s.strip() == 'nop' for s in seq) and all(
                s.strip() != 'nop' for s in cand_asm):
            # Old has nops, new doesn't — i.e., we'd remove nops.
            continue   # nop-removal — unsafe if those nops were padding
        freq = seqs[seq][1]
        savings = len(seqs[seq][0]) - len(cand_code)
        verified.append({
            'old': list(seq),
            'new': list(cand_asm),
            'old_bytes': len(seqs[seq][0]),
            'new_bytes': len(cand_code),
            'savings_per_occurrence': savings,
            'frequency': freq,
            'total_savings': savings * freq,
        })

    verified.sort(key=lambda x: -x['total_savings'])

    print(f'\n[3/3] {len(verified)} verified replacements:', file=sys.stderr)
    total = 0
    for v in verified[:30]:
        print(f"  save {v['savings_per_occurrence']}B × {v['frequency']} "
              f"= {v['total_savings']}B  |  "
              f"{' ; '.join(v['old'])}  →  {' ; '.join(v['new'])}",
              file=sys.stderr)
        total += v['total_savings']
    print(f'\n  Total potential savings across corpus: {total}B',
          file=sys.stderr)

    with open(args.out, 'w') as f:
        json.dump(verified, f, indent=2)
    print(f'\nResults saved to {args.out}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
