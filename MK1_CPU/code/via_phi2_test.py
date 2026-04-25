#!/usr/bin/env python3
"""Test suite for VIA with PHI2=NOT(CLK) via GAL.

Runs test programs via serial (manual clock via ESP32 RUN command).
Tests are ordered from simple to complex to isolate failures.
"""

import serial
import json
import time
import sys
import os

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
BAUD = 115200
PROG_DIR = os.path.join(os.path.dirname(__file__), '..', 'programs')
CHUNK_SIZE = 64
CHUNK_DELAY = 0.01

def send_chunked(ser, data):
    for i in range(0, len(data), CHUNK_SIZE):
        ser.write(data[i:i+CHUNK_SIZE])
        time.sleep(CHUNK_DELAY)

def run_test(ser, name, asm_file, expected, cycles=10000000, timeout=30):
    """Assemble, upload, run a test program. Returns (pass, actual_val)."""
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"  File: {asm_file}")
    print(f"  Expected: {expected}")

    with open(os.path.join(PROG_DIR, asm_file)) as f:
        asm = f.read()

    # Assemble
    ser.reset_input_buffer()
    escaped = asm.replace('\n', '\\n')
    cmd = f'ASM:{escaped}\n'.encode()
    send_chunked(ser, cmd)
    r = ser.readline().decode().strip()
    try:
        resp = json.loads(r)
    except:
        print(f"  ASM ERROR: {r[:200]}")
        return False, None

    if not resp.get('ok'):
        print(f"  ASM FAILED: {resp}")
        return False, None
    print(f"  Assembled: code={resp['code']}B")

    # Upload
    ser.write(b'UPLOAD\n')
    r = ser.readline().decode().strip()
    print(f"  Upload: {r[:80]}")

    # Reset
    ser.write(b'RESET\n')
    r = ser.readline().decode().strip()
    time.sleep(0.1)

    # Run
    ser.reset_input_buffer()
    ser.write(f'RUN:{cycles},1\n'.encode())
    old_timeout = ser.timeout
    ser.timeout = timeout
    r = ser.readline().decode().strip()
    ser.timeout = old_timeout

    try:
        result = json.loads(r)
    except:
        print(f"  RUN ERROR: {r[:200]}")
        return False, None

    val = result.get('val', '?')
    cyc = result.get('cyc', '?')
    aborted = result.get('aborted', False)
    print(f"  Result: val={val} cyc={cyc}{' ABORTED' if aborted else ''}")

    if isinstance(expected, list):
        passed = val in expected
    else:
        passed = (val == expected)

    if passed:
        print(f"  ✓ PASS")
    else:
        print(f"  ✗ FAIL (expected {expected}, got {val})")

    return passed, val


def run_runnb_test(ser, name, asm_file, expected_hist, maxoi=0, cycles=10000000, timeout=30):
    """Run test with RUNNB to capture multiple OI events."""
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"  File: {asm_file}")
    print(f"  Expected hist: {expected_hist}")

    with open(os.path.join(PROG_DIR, asm_file)) as f:
        asm = f.read()

    ser.reset_input_buffer()
    escaped = asm.replace('\n', '\\n')
    cmd = f'ASM:{escaped}\n'.encode()
    send_chunked(ser, cmd)
    r = ser.readline().decode().strip()
    try:
        resp = json.loads(r)
    except:
        print(f"  ASM ERROR: {r[:200]}")
        return False, None
    if not resp.get('ok'):
        print(f"  ASM FAILED: {resp}")
        return False, None
    print(f"  Assembled: code={resp['code']}B")

    ser.write(b'UPLOAD\n')
    r = ser.readline().decode().strip()
    print(f"  Upload: {r[:80]}")

    ser.write(b'RESET\n')
    r = ser.readline().decode().strip()
    time.sleep(0.1)

    ser.reset_input_buffer()
    maxoi_str = f",{maxoi}" if maxoi else ""
    ser.write(f'RUNNB:{cycles},1{maxoi_str}\n'.encode())
    old_timeout = ser.timeout
    ser.timeout = timeout
    # Read lines until we get the final result (skip heartbeats)
    result = None
    while True:
        r = ser.readline().decode().strip()
        if not r:
            print(f"  TIMEOUT")
            break
        try:
            j = json.loads(r)
            if 'hb' in j:
                print(f"  heartbeat: cyc={j['hb']} oi={j['oi']}")
                continue
            result = j
            break
        except:
            print(f"  PARSE ERROR: {r[:200]}")
            break
    ser.timeout = old_timeout

    if result is None:
        return False, None

    hist = result.get('hist', [])
    cnt = result.get('cnt', 0)
    cyc = result.get('cyc', '?')
    print(f"  Result: cnt={cnt} hist={hist} cyc={cyc}")

    passed = (hist == expected_hist)
    if passed:
        print(f"  ✓ PASS")
    else:
        print(f"  ✗ FAIL")
    return passed, hist


def main():
    print("VIA PHI2=NOT(CLK) Test Suite")
    print("="*50)
    print(f"Port: {PORT}")

    ser = serial.Serial(PORT, BAUD, timeout=10)
    time.sleep(1)
    ser.reset_input_buffer()

    # Check status
    ser.write(b'STATUS\n')
    status = ser.readline().decode().strip()
    print(f"Status: {status}")

    results = []

    # Test 1: Basic output (no VIA needed)
    p, v = run_test(ser, "Basic OUT (no VIA)", "via_test.asm", 3,
                    cycles=500000)
    # Actually via_test.asm tests VIA. Let me use a simple test.
    # Scratch that, just use via_test directly as test 1.
    results.append(("VIA DDRB write+read", p, v))

    # Test 2: Glitch test (10 iterations)
    p, v = run_test(ser, "DDRB glitch test (10 iter)", "via_glitch_test.asm", 3,
                    cycles=500000)
    results.append(("Glitch test (10)", p, v))

    # Test 3: Glitch stress (256 iterations)
    p, v = run_test(ser, "DDRB glitch stress (256 iter)", "via_glitch_stress.asm", 3,
                    cycles=5000000)
    results.append(("Glitch stress (256)", p, v))

    # Test 4: DS3231 I2C scan
    p, v = run_test(ser, "DS3231 I2C scan (0x68)", "i2c_scan_0x68.asm", 87,
                    cycles=5000000)
    results.append(("DS3231 scan", p, v))

    # Test 5: EEPROM I2C scan
    p, v = run_test(ser, "EEPROM I2C scan (0x57)", "eeprom_scan.asm", 1,
                    cycles=5000000)
    results.append(("EEPROM scan", p, v))

    # Test 6: EEPROM write with ACK check
    p, v = run_runnb_test(ser, "EEPROM write ACKs",
                          "eeprom_write_ack.asm",
                          [10, 20, 30, 40, 99],  # all ACK + done
                          maxoi=5, cycles=10000000)
    results.append(("EEPROM write ACKs", p, v))

    # Test 7: EEPROM multi write+read
    p, v = run_runnb_test(ser, "EEPROM multi write+read",
                          "eeprom_multi_test.asm",
                          [0xDE, 0xAD, 0xBE, 0xEF],
                          maxoi=4, cycles=50000000, timeout=60)
    results.append(("EEPROM multi R/W", p, v))

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    passed = 0
    total = len(results)
    for name, p, v in results:
        status = "✓ PASS" if p else "✗ FAIL"
        print(f"  {status}  {name} (val={v})")
        if p:
            passed += 1
    print(f"\n  {passed}/{total} tests passed")

    ser.close()

if __name__ == '__main__':
    main()
