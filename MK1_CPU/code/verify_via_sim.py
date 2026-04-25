#!/usr/bin/env python3
"""Verify compiled program by running through the simulator.

Flow: C source → mk1cc2 → asm → ESP32 assembler (via serial ASM:) →
DUMP all 4 pages back → load into mk1sim.py → run → compare output_history.

This gives ground-truth correctness data deterministically — the
hardware's OI capture is noisy on fast programs, but the simulator is
cycle-accurate.

Usage:
    python3 verify_via_sim.py <program.c> [--eeprom] [--cycles N]
                              [--expect VAL1,VAL2,...]
    python3 verify_via_sim.py <program.asm>             # pre-assembled input
"""
import sys, os, json, time, argparse
# Run from the code/ dir so mk1sim.py finds microcode.py via relative import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import serial
import subprocess
import mk1sim

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
BAUD = 115200
COMPILER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mk1cc2.py')


def compile_to_asm(source_path, eeprom=False):
    """Run mk1cc2 to produce asm."""
    args = ['python3', COMPILER, source_path, '-O', '-o', '/tmp/_v_sim.asm']
    if eeprom:
        args.append('--eeprom')
    env = dict(os.environ); env['PYTHONHASHSEED'] = '0'
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f'Compile failed:\n{r.stderr}', file=sys.stderr)
        return None
    with open('/tmp/_v_sim.asm') as f:
        return f.read()


def esp32_assemble_and_dump(asm_text, port=PORT, timeout=15):
    """Upload asm to ESP32 (assembles into uploadBuf), then DUMP all bytes.
    Returns dict with 'code', 'data', 'stack', 'page3' as bytearrays."""
    ser = serial.Serial(port, BAUD, timeout=5)
    time.sleep(0.2)
    ser.reset_input_buffer()
    # RESET first so no stale state
    ser.write(b'RESET\n')
    try: ser.readline()
    except: pass
    time.sleep(0.2)
    # ASM — escape newlines to \\n
    esc = asm_text.replace('\n', '\\n')
    payload = f'ASM:{esc}\n'.encode()
    CHUNK = 4096
    if len(payload) > CHUNK:
        for i in range(0, len(payload), CHUNK):
            ser.write(payload[i:i+CHUNK]); time.sleep(0.05)
    else:
        ser.write(payload)
    ser.timeout = timeout
    try:
        r = json.loads(ser.readline().decode().strip())
    except Exception as e:
        ser.close()
        raise RuntimeError(f'ASM failed: {e}')
    if not r.get('ok'):
        ser.close()
        raise RuntimeError(f'ASM error: {r}')

    # DUMP all 1024 bytes of uploadBuf as hex.
    # Buffer layout: [code(256), data(256), stack(256), page3(256)]
    out = bytearray()
    BLK = 64
    for off in range(0, 1024, BLK):
        ser.reset_input_buffer()
        ser.write(f'DUMP:{off},{BLK}\n'.encode())
        line = ser.readline().decode().strip()
        toks = line.split()
        for t in toks:
            if len(t) == 2:
                out.append(int(t, 16))
    ser.close()
    if len(out) < 1024:
        raise RuntimeError(f'DUMP short: got {len(out)} bytes, expected 1024')
    return {
        'code': out[0:256],
        'data': out[256:512],
        'stack': out[512:768],
        'page3': out[768:1024],
    }


def sim_run(pages, max_cycles=1_000_000):
    """Load pages into mk1sim and run. Returns (output_history, halted, cycle)."""
    cpu = mk1sim.MK1()
    cpu.mem[0] = bytearray(pages['code'])
    cpu.mem[1] = bytearray(pages['data'])
    cpu.mem[2] = bytearray(pages['stack'])
    cpu.mem[3] = bytearray(pages['page3'])
    halted = cpu.run(max_cycles)
    return cpu.output_history, halted, cpu.cycle


def main():
    ap = argparse.ArgumentParser(description='MK1 simulator-based verifier')
    ap.add_argument('input', help='C source (.c) or asm (.asm) file')
    ap.add_argument('--eeprom', action='store_true')
    ap.add_argument('--cycles', type=int, default=1_000_000)
    ap.add_argument('--expect', help='Comma-separated expected output prefix')
    ap.add_argument('--port', default=PORT)
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    # Compile if C
    if args.input.endswith('.c'):
        asm = compile_to_asm(args.input, eeprom=args.eeprom)
        if asm is None: return 2
    else:
        with open(args.input) as f:
            asm = f.read()

    # Assemble via ESP32
    try:
        pages = esp32_assemble_and_dump(asm, port=args.port)
    except RuntimeError as e:
        print(f'ESP32 assemble/dump failed: {e}', file=sys.stderr)
        return 3

    if args.verbose:
        print(f'code: {pages["code"][:32].hex()}... ({sum(1 for b in pages["code"] if b) } non-zero / 256)')
        print(f'data: {pages["data"][:32].hex()}... ({sum(1 for b in pages["data"] if b) } non-zero / 256)')
        print(f'page3: {pages["page3"][:32].hex()}... ({sum(1 for b in pages["page3"] if b) } non-zero / 256)')

    # Simulate
    out_hist, halted, cycles = sim_run(pages, max_cycles=args.cycles)
    print(f'output_history: {out_hist}')
    print(f'halted={halted} cycles={cycles}')

    if args.expect:
        expected = [int(x) for x in args.expect.split(',')]
        actual = out_hist[:len(expected)]
        if actual == expected:
            print(f'[PASS] first {len(expected)} outputs match')
            return 0
        else:
            print(f'[FAIL] expected {expected} got {actual}')
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
