#!/usr/bin/env python3
"""MK1 compiler size-regression harness (V2 of abstraction roadmap).

Compiles every program in MK1_CPU/programs/ and records per-program size
metrics (kernel, stage-1, overlay region, page 0/1/3 utilisation, EEPROM
use). Compares against a stored baseline to catch size regressions from
compiler changes.

Does NOT require hardware — pure software measurement of the compiler's
output. Catches optimisation regressions that hardware regression tests
would not notice (a program can still work correctly but take more bytes).

Usage:
    python3 size_regression.py                    # check against baseline
    python3 size_regression.py --check            # same
    python3 size_regression.py --baseline         # overwrite baseline
    python3 size_regression.py --update           # check, but save new
                                                  # values for any program
                                                  # that shrank
    python3 size_regression.py --show             # just print current sizes
    python3 size_regression.py --program NAME     # measure one program

Exit codes:
    0 — all programs within tolerance
    1 — at least one program regressed beyond tolerance
    2 — at least one program failed to compile that was previously OK
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

COMPILER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mk1cc2.py')
PROGRAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'programs'))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'size_baseline.json')

# Fields that count as "size" metrics for regression purposes. Each is a
# smaller-is-better byte count; a program is a regression if any of these
# grew beyond tolerance.
SIZE_FIELDS = [
    'stage1_total', 'kernel', 'page0_used', 'page1_allocated',
    'page3_used', 'eeprom_used', 'overlay_largest',
]

# Per-field tolerance in bytes. 0 = exact; >0 = allow that much growth
# without flagging a regression. Useful when a compiler change is
# expected to move a byte or two here and there.
TOLERANCE = 0


def compile_one(source_path, eeprom=True, optimize=True):
    """Compile a single C source. Returns (metrics_dict, stderr_tail).

    metrics_dict is None on catastrophic failure (compiler crash).
    Otherwise metrics_dict has `compile_ok: bool` and size fields.
    """
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as mf:
        metrics_path = mf.name
    with tempfile.NamedTemporaryFile(suffix='.asm', delete=False) as af:
        asm_path = af.name

    try:
        args = ['python3', COMPILER, source_path, '-o', asm_path,
                '--metrics-out', metrics_path]
        if optimize:
            args.append('-O')
        if eeprom:
            args.append('--eeprom')
        r = subprocess.run(args, capture_output=True, text=True, timeout=60)
        stderr_tail = r.stderr.splitlines()[-5:] if r.stderr else []

        # Compiler writes metrics JSON even on overflow exit, so try to
        # read it regardless of return code.
        if os.path.exists(metrics_path) and os.path.getsize(metrics_path) > 0:
            with open(metrics_path) as f:
                metrics = json.load(f)
        elif r.returncode != 0:
            # Compile failed before the metrics-write point (syntax error,
            # internal crash, etc.) — synthesise a failure record.
            metrics = {
                'compile_ok': False,
                'code_overflow': False,
                'error': '\n'.join(stderr_tail),
            }
        else:
            metrics = None

        return metrics, '\n'.join(stderr_tail)
    finally:
        for p in (metrics_path, asm_path):
            try: os.unlink(p)
            except: pass


def gather_all(verbose=False):
    """Compile every program. Returns {name: metrics_dict}."""
    results = {}
    sources = sorted(f for f in os.listdir(PROGRAMS_DIR) if f.endswith('.c'))
    for src in sources:
        name = src[:-2]
        path = os.path.join(PROGRAMS_DIR, src)
        metrics, stderr = compile_one(path)
        if metrics is None:
            # Compiler crashed. Record a placeholder.
            metrics = {'compile_ok': False, 'error': 'compiler crashed'}
        results[name] = metrics
        if verbose:
            status = 'OK' if metrics.get('compile_ok') else 'FAIL'
            kernel = metrics.get('kernel')
            print(f"  {name:30s} {status:4s}  kernel={kernel}", file=sys.stderr)
    return results


def load_baseline():
    if not os.path.exists(BASELINE):
        return {}
    with open(BASELINE) as f:
        return json.load(f)


def save_baseline(data):
    with open(BASELINE, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def compare(current, baseline, tolerance=TOLERANCE):
    """Returns (regressions, improvements, new_failures, new_programs).

    Each is a list of (name, field, baseline_val, current_val) tuples.
    """
    regressions, improvements, new_failures, new_programs = [], [], [], []

    for name, cur in current.items():
        if name not in baseline:
            new_programs.append((name, None, None, cur))
            continue
        base = baseline[name]

        # Compile status changes
        if base.get('compile_ok') and not cur.get('compile_ok'):
            new_failures.append((name, 'compile_ok', True, cur))
            continue
        if not base.get('compile_ok') and cur.get('compile_ok'):
            improvements.append((name, 'compile_ok', False, True))

        # Size-field comparisons
        for field in SIZE_FIELDS:
            b = base.get(field)
            c = cur.get(field)
            if b is None or c is None:
                continue
            if c > b + tolerance:
                regressions.append((name, field, b, c))
            elif c < b:
                improvements.append((name, field, b, c))

    return regressions, improvements, new_failures, new_programs


def fmt_row(name, field, base, cur):
    if base is None:
        return f"  {name:30s} {field:20s} <new>"
    delta = cur - base if isinstance(cur, int) and isinstance(base, int) else '?'
    sign = '+' if isinstance(delta, int) and delta > 0 else ''
    return f"  {name:30s} {field:20s} {base:>5}B → {cur:>5}B  ({sign}{delta})"


def cmd_baseline(args):
    print(f"Compiling {_count_programs()} programs to establish baseline...", file=sys.stderr)
    data = gather_all(verbose=args.verbose)
    save_baseline(data)
    ok = sum(1 for m in data.values() if m.get('compile_ok'))
    fail = len(data) - ok
    print(f"Baseline written: {BASELINE}", file=sys.stderr)
    print(f"  {ok} compiled OK, {fail} failed", file=sys.stderr)
    return 0


def cmd_check(args, update_on_improvement=False):
    baseline = load_baseline()
    if not baseline:
        print(f"No baseline at {BASELINE}. Run --baseline first.", file=sys.stderr)
        return 2

    current = gather_all(verbose=args.verbose)
    regressions, improvements, new_failures, new_programs = compare(
        current, baseline, tolerance=args.tolerance)

    # Report
    if regressions:
        print(f"\n!! {len(regressions)} SIZE REGRESSION(S):", file=sys.stderr)
        for row in regressions:
            print(fmt_row(*row), file=sys.stderr)
    if new_failures:
        print(f"\n!! {len(new_failures)} NEW COMPILE FAILURE(S):", file=sys.stderr)
        for name, _, _, cur in new_failures:
            err = cur.get('error', '(no error message)')
            overflow = cur.get('code_overflow')
            tag = 'OVERFLOW' if overflow else 'ERROR'
            print(f"  {name:30s} {tag}  {err[:80]}", file=sys.stderr)
    if improvements:
        print(f"\n-- {len(improvements)} improvement(s):", file=sys.stderr)
        for row in improvements:
            print(fmt_row(*row), file=sys.stderr)
    if new_programs:
        print(f"\n-- {len(new_programs)} new program(s) (no baseline):", file=sys.stderr)
        for name, _, _, _ in new_programs:
            print(f"  {name}", file=sys.stderr)

    # Summary
    ok = sum(1 for m in current.values() if m.get('compile_ok'))
    print(f"\n{ok}/{len(current)} compile OK  "
          f"regressions={len(regressions)}  new_failures={len(new_failures)}  "
          f"improvements={len(improvements)}", file=sys.stderr)

    if update_on_improvement and (improvements or new_programs):
        # Merge current values for improved + new programs into baseline
        updated = dict(baseline)
        for name, _, _, _ in new_programs:
            updated[name] = current[name]
        for name, field, b, c in improvements:
            if name in updated:
                updated[name][field] = c
            else:
                updated[name] = current[name]
        save_baseline(updated)
        print(f"Baseline updated with improvements/new programs.", file=sys.stderr)

    if new_failures:
        return 2
    if regressions:
        return 1
    return 0


def cmd_show(args):
    if args.program:
        path = os.path.join(PROGRAMS_DIR, args.program + '.c')
        if not os.path.exists(path):
            print(f"No such program: {path}", file=sys.stderr)
            return 2
        metrics, stderr = compile_one(path)
        print(json.dumps(metrics, indent=2))
        return 0
    data = gather_all(verbose=True)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def _count_programs():
    return sum(1 for f in os.listdir(PROGRAMS_DIR) if f.endswith('.c'))


def main():
    ap = argparse.ArgumentParser(description='MK1 compiler size-regression harness')
    sp = ap.add_mutually_exclusive_group()
    sp.add_argument('--baseline', action='store_true', help='Overwrite baseline with current sizes')
    sp.add_argument('--check', action='store_true', help='Compare current sizes to baseline (default)')
    sp.add_argument('--update', action='store_true', help='Check, and save improvements to baseline')
    sp.add_argument('--show', action='store_true', help='Print current sizes (no comparison)')
    ap.add_argument('--program', help='Measure only this program (name without .c)')
    ap.add_argument('--tolerance', type=int, default=TOLERANCE,
                    help='Bytes of growth allowed before flagging regression (default 0)')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    if args.show or args.program:
        return cmd_show(args)
    if args.baseline:
        return cmd_baseline(args)
    if args.update:
        return cmd_check(args, update_on_improvement=True)
    return cmd_check(args)


if __name__ == '__main__':
    sys.exit(main())
