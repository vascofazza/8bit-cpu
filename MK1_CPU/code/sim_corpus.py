#!/usr/bin/env python3
"""V3 — corpus-wide simulator regression.

For every C program in MK1_CPU/programs/ that compiles cleanly: compile
→ assemble (via ESP32 DUMP path) → run on mk1sim → snapshot the
(output_history, halted, cycles) triple. Compare against a stored
baseline; any divergence is a miscompile (assuming mk1sim and the ESP32
assembler are ground truth — both are byte-exact against the MK1
microcode per project_cpu_hardware_verified.md).

This is the compounding safety net under every optimization pass we
add: you can make any compiler change, run `python3 sim_corpus.py`,
and see if the behaviour of any program changed. Size changes are
tracked by size_regression.py — this one watches CORRECTNESS.

Usage:
    python3 sim_corpus.py                    # check against baseline
    python3 sim_corpus.py --baseline         # overwrite baseline
    python3 sim_corpus.py --filter NAME      # only programs matching NAME
    python3 sim_corpus.py --cycles N         # sim cycle budget (default 500000)

Skips programs that overflow or otherwise fail to compile; they aren't
expected to run correctly. Also skips programs that don't halt in the
cycle budget (continuous loops) since there's no deterministic
end-of-program snapshot for those.
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import mk1sim
from verify_via_sim import compile_to_asm, esp32_assemble_and_dump, sim_run, PORT

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'sim_corpus_baseline.json')


def capture_snapshot(source_path, cycles=500_000, port=PORT):
    """Compile + assemble + simulate. Returns snapshot dict or None on
    failure. Snapshot keys: output_history (list), halted (bool),
    cycles_run (int). A stable hash of output_history lets the baseline
    stay compact for very-long traces."""
    asm = compile_to_asm(source_path)
    if asm is None:
        return None
    try:
        pages = esp32_assemble_and_dump(asm, port=port)
    except Exception as e:
        return {'error': f'assemble: {e}'}
    try:
        out_hist, halted, cycles_run = sim_run(pages, max_cycles=cycles)
    except Exception as e:
        return {'error': f'sim: {e}'}
    # Hash the output trace so baselines stay small for long programs
    # and the comparison ignores trivial whitespace churn.
    trace_str = ','.join(str(v) for v in out_hist)
    trace_hash = hashlib.sha256(trace_str.encode()).hexdigest()[:16]
    return {
        'output_history': out_hist,
        'output_hash': trace_hash,
        'output_len': len(out_hist),
        'halted': halted,
        'cycles_run': cycles_run,
    }


def compare_snapshots(baseline, current):
    """Return list of differences. Empty = match."""
    diffs = []
    # If either failed to compile, skip — reported separately
    if baseline is None and current is None:
        return []
    if baseline is None:
        return ['new program (no baseline)']
    if current is None:
        return ['failed to compile']
    b_err = baseline.get('error')
    c_err = current.get('error')
    if b_err and c_err:
        # Both broken. Report only if the error text changed — otherwise
        # it's the same pre-existing failure (most likely: the program
        # references external symbols like `_eeprom_write` that aren't
        # intended to link as a standalone).
        if b_err != c_err:
            return [f'error changed: was {b_err!r}, now {c_err!r}']
        return []
    if c_err and not b_err:
        return [f'newly broken: {c_err}']
    if b_err and not c_err:
        return ['was broken, now compiles']
    # Compare actual results
    if baseline.get('halted') != current.get('halted'):
        diffs.append(f'halted: {baseline.get("halted")} → {current.get("halted")}')
    if baseline.get('output_hash') != current.get('output_hash'):
        b_out = baseline.get('output_history', [])[:10]
        c_out = current.get('output_history', [])[:10]
        diffs.append(f'output differs: baseline first 10={b_out}, '
                     f'current first 10={c_out} '
                     f'(lengths {baseline.get("output_len")} vs '
                     f'{current.get("output_len")})')
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', action='store_true',
                    help='overwrite baseline with current snapshots')
    ap.add_argument('--filter', default=None,
                    help='only process programs whose name contains this string')
    ap.add_argument('--cycles', type=int, default=500_000)
    ap.add_argument('--port', default=PORT)
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    programs = sorted(glob.glob(
        '/Users/gadyke/8bit-cpu/MK1_CPU/programs/*.c'))
    if args.filter:
        programs = [p for p in programs if args.filter in os.path.basename(p)]

    if os.path.exists(BASELINE) and not args.baseline:
        with open(BASELINE) as f:
            baseline = json.load(f)
    else:
        baseline = {}

    current = {}
    print(f'Running {len(programs)} programs (cycles={args.cycles})...',
          file=sys.stderr)
    t0 = time.time()
    for i, p in enumerate(programs):
        name = os.path.basename(p)[:-2]   # strip .c
        print(f'  [{i+1}/{len(programs)}] {name}...', end=' ', flush=True,
              file=sys.stderr)
        snap = capture_snapshot(p, cycles=args.cycles, port=args.port)
        current[name] = snap
        if snap is None:
            print('COMPILE-FAIL', file=sys.stderr)
        elif 'error' in snap:
            print(f'ERR ({snap["error"][:40]})', file=sys.stderr)
        else:
            print(f'halted={snap["halted"]} outlen={snap["output_len"]}',
                  file=sys.stderr)

    elapsed = time.time() - t0
    print(f'\nDone in {elapsed:.1f}s', file=sys.stderr)

    if args.baseline:
        with open(BASELINE, 'w') as f:
            json.dump(current, f, indent=2, default=list)
        print(f'Baseline written to {BASELINE}', file=sys.stderr)
        return 0

    # Compare
    changed = []
    new = []
    fixed = []
    unchanged = 0
    for name, snap in current.items():
        base = baseline.get(name)
        diffs = compare_snapshots(base, snap)
        if not diffs:
            unchanged += 1
            continue
        if base is None:
            new.append(name)
        elif snap is None or 'error' in snap:
            changed.append((name, diffs))
        elif 'error' in (base or {}):
            fixed.append(name)
        else:
            changed.append((name, diffs))

    missing_baseline = set(baseline) - set(current)
    if missing_baseline:
        print(f'\n!! {len(missing_baseline)} program(s) in baseline but missing now:',
              file=sys.stderr)
        for name in sorted(missing_baseline):
            print(f'  {name}', file=sys.stderr)

    if changed:
        print(f'\n!! {len(changed)} BEHAVIOUR CHANGE(S):', file=sys.stderr)
        for name, diffs in changed:
            print(f'  {name}:', file=sys.stderr)
            for d in diffs:
                print(f'    {d}', file=sys.stderr)

    if fixed:
        print(f'\n-- {len(fixed)} newly-compiling:', file=sys.stderr)
        for name in fixed:
            print(f'  {name}', file=sys.stderr)

    if new:
        print(f'\n?? {len(new)} new (no baseline entry):', file=sys.stderr)
        for name in new:
            print(f'  {name}', file=sys.stderr)

    print(f'\n{unchanged}/{len(current)} unchanged, '
          f'{len(changed)} changed, '
          f'{len(fixed)} fixed, '
          f'{len(new)} new',
          file=sys.stderr)

    return 1 if changed else 0


if __name__ == '__main__':
    sys.exit(main())
