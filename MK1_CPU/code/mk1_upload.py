#!/usr/bin/env python3
"""MK1 upload helper — reliable serial communication for large programs.

Usage:
    python3 mk1_upload.py <program.asm> [--run [cycles]] [--port PORT]
    python3 mk1_upload.py <program.c> [-O] [--eeprom] [--run [cycles]] [--port PORT]

Handles: chunked serial sending, assembly, upload, run with timeout.
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
CHUNK_SIZE = 64
CHUNK_DELAY = 0.01  # 10ms between chunks


def send_chunked(ser, data):
    """Send data in small chunks to avoid UART buffer overflow."""
    for i in range(0, len(data), CHUNK_SIZE):
        ser.write(data[i:i+CHUNK_SIZE])
        time.sleep(CHUNK_DELAY)


def mk1_asm(ser, asm_text):
    """Assemble on ESP32. Returns parsed JSON response."""
    ser.reset_input_buffer()
    escaped = asm_text.replace('\n', '\\n')
    cmd = f'ASM:{escaped}\n'.encode()
    send_chunked(ser, cmd)
    r = ser.readline().decode().strip()
    try:
        return json.loads(r)
    except:
        print(f'ASM error: {r[:200]}', file=sys.stderr)
        return None


def mk1_upload(ser):
    """Upload assembled buffer to MK1."""
    ser.write(b'UPLOAD\n')
    ser.readline()


def mk1_run(ser, cycles=10000000, timeout=120):
    """Run program. Returns parsed JSON response."""
    ser.write(f'RUN:{cycles},1\n'.encode())
    old_timeout = ser.timeout
    ser.timeout = timeout
    r = ser.readline().decode().strip()
    ser.timeout = old_timeout
    try:
        return json.loads(r)
    except:
        print(f'RUN timeout or error: {r[:200]}', file=sys.stderr)
        return None


def compile_c(source_file, optimize=True, eeprom=False):
    """Compile C to assembly. Returns asm text or None."""
    args = ['python3', COMPILER, source_file]
    if optimize:
        args.append('-O')
    if eeprom:
        args.append('--eeprom')
    args.extend(['-o', '/tmp/_mk1_upload.asm'])
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'Compile error: {r.stderr[:500]}', file=sys.stderr)
        return None
    if r.stderr:
        print(r.stderr.strip(), file=sys.stderr)
    with open('/tmp/_mk1_upload.asm') as f:
        return f.read()


def main():
    import argparse
    ap = argparse.ArgumentParser(description='MK1 Upload Helper')
    ap.add_argument('input', help='Assembly (.asm) or C (.c) source file')
    ap.add_argument('-O', '--optimize', action='store_true', help='Enable optimization')
    ap.add_argument('--eeprom', action='store_true', help='EEPROM overlay mode')
    ap.add_argument('--run', nargs='?', const=10000000, type=int, help='Run after upload (optional cycle count)')
    ap.add_argument('--port', default=PORT, help=f'Serial port (default: {PORT})')
    ap.add_argument('--timeout', type=int, default=120, help='Run timeout in seconds')
    args = ap.parse_args()

    # Compile if C source
    if args.input.endswith('.c'):
        print(f'Compiling {args.input}...')
        asm = compile_c(args.input, optimize=args.optimize, eeprom=args.eeprom)
        if asm is None:
            sys.exit(1)
    else:
        with open(args.input) as f:
            asm = f.read()

    print(f'Connecting to {args.port}...')
    ser = serial.Serial(args.port, BAUD, timeout=30)
    time.sleep(1)
    ser.reset_input_buffer()

    # Assemble
    print(f'Assembling ({len(asm)} bytes of source)...')
    r = mk1_asm(ser, asm)
    if r is None or not r.get('ok'):
        if r and r.get('detail'):
            for err in r['detail']:
                print(f"  Error line {err['line']}: {err['msg']}", file=sys.stderr)
        elif r:
            print(f"  {r}", file=sys.stderr)
        ser.close()
        sys.exit(1)
    print(f'  code={r["code"]}B data={r.get("data",0)}B')

    # Upload
    print('Uploading...')
    mk1_upload(ser)

    # Run
    if args.run is not None:
        cycles = args.run
        print(f'Running ({cycles} cycles, timeout {args.timeout}s)...')
        r2 = mk1_run(ser, cycles=cycles, timeout=args.timeout)
        if r2:
            print(f'  val={r2["val"]} cap={r2["cap"]} cyc={r2["cyc"]}', end='')
            if r2.get('aborted'):
                print(' (ABORTED)', end='')
            print(f' khz={r2.get("khz","")}')
        else:
            print('  No response (program may still be running)')

    ser.close()


if __name__ == '__main__':
    main()
