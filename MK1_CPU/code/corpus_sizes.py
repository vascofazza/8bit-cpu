#!/usr/bin/env python3
"""Corpus-wide size breakdown.

For every C program in MK1_CPU/programs/:
  - Compile with --metrics-out to capture structured size data.
  - Print a table: program | stage1 | kernel | loader | main | helpers | overlays.

Usage:
    python3 corpus_sizes.py                 # print table, one row per program
    python3 corpus_sizes.py --failing       # only show programs that overflow
    python3 corpus_sizes.py --json out.json # dump full structured data

Depends on the --metrics-out + --why-not-smaller breakdown added in Phase 0.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PROGRAMS = sorted(glob.glob('/Users/gadyke/8bit-cpu/MK1_CPU/programs/*.c'))


def compile_one(cfile, metrics_path):
    """Compile `cfile`, writing structured metrics to metrics_path. Returns
    (compile_ok: bool, metrics: dict or None)."""
    args = ['python3', 'mk1cc2.py', cfile, '-o', '/tmp/_cs.asm',
            '--metrics-out', metrics_path,
            '--why-not-smaller']
    r = subprocess.run(args, capture_output=True, text=True)
    ok = (r.returncode == 0)
    try:
        with open(metrics_path) as f:
            m = json.load(f)
    except Exception:
        m = None
    return ok, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--failing', action='store_true',
                    help='only show programs that overflow or fail')
    ap.add_argument('--json', help='dump full structured data to this path')
    ap.add_argument('--filter', help='substring filter on program name')
    args = ap.parse_args()

    rows = []
    full = {}
    for cfile in PROGRAMS:
        name = os.path.basename(cfile)[:-2]
        if args.filter and args.filter not in name:
            continue
        ok, m = compile_one(cfile, '/tmp/_cs.json')
        if not ok:
            rows.append({'name': name, 'status': 'FAIL', 'm': m})
        else:
            rows.append({'name': name, 'status': 'ok', 'm': m})
        full[name] = {'ok': ok, 'metrics': m}

    # Print table
    hdr = f'{"program":<32} {"stage1":>7} {"kernel":>7} {"loader":>7} {"main":>5} {"helpers":>8} {"#ov":>4} {"largest":>8}'
    print(hdr)
    print('-' * len(hdr))
    shown = 0
    for row in rows:
        m = row['m']
        name = row['name']
        if args.failing and row['status'] != 'FAIL':
            # include near-limit too
            if m is None:
                continue
            s1 = (m.get('stage1_total') or 0)
            ker = (m.get('kernel') or 0)
            if s1 < 240 and ker < 240:
                continue
        if m is None:
            print(f'{name:<32} {"(no metrics)":>40}')
            shown += 1
            continue
        s1 = m.get('stage1_total') or 0
        ker = m.get('kernel') or 0
        br = m.get('breakdown') or {}
        ld = br.get('loader') or 0
        mn = br.get('main') or 0
        hl = br.get('helpers_total') or 0
        ovs = len(br.get('overlay_slots') or [])
        largest = max((s['size'] for s in br.get('overlay_slots') or []), default=0)
        tag = '' if row['status'] == 'ok' else '  FAIL'
        print(f'{name:<32} {s1:>7} {ker:>7} {ld:>7} {mn:>5} {hl:>8} {ovs:>4} {largest:>8}{tag}')
        shown += 1

    print()
    # Summary
    fails = [r for r in rows if r['status'] == 'FAIL']
    print(f'Total: {len(rows)}  compiling-ok: {len(rows) - len(fails)}  failing: {len(fails)}')
    if fails:
        print('Failing:')
        for r in fails:
            m = r['m'] or {}
            s1 = m.get('stage1_total') or 0
            ker = m.get('kernel') or 0
            print(f'  {r["name"]}  stage1={s1} kernel={ker}')

    if args.json:
        with open(args.json, 'w') as f:
            json.dump(full, f, indent=2)
        print(f'Full data → {args.json}', file=sys.stderr)


if __name__ == '__main__':
    main()
