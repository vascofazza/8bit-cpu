#!/usr/bin/env python3
"""Hardware smoke test for new register inc/dec opcodes.

Runs after:
  1. microcode.bin flashed to all 4 MK1 EEPROMs (T48 + minipro)
  2. ESP32 firmware rebuilt and flashed (pio run -t upload) to pick up the new
     mnemonics ('dec $b', 'dec $c', 'dec $d', 'inc $b', 'inc $c', 'inc $d')

Uploads test_new_incdec.asm, runs with multi-capture OI, verifies output.

Expected sequence:
  [4, 9, 99, 1, 43, 8, 255, 0, 77, 3, 2, 1]
  └─ dec $d: 5-1 = 4
     └─ dec $c: 10-1 = 9
        └─ dec $b: 100-1 = 99
           └─ inc $d: 0+1 = 1
              └─ inc $c: 42+1 = 43
                 └─ inc $b: 7+1 = 8
                    └─ dec $d wrap: 0-1 = 255
                       └─ inc $d wrap: 255+1 = 0
                          └─ dec $d ZF: 1-1=0 → jz fires → 77
                             └─ loop: 3, 2, 1 (dec $d; jnz)
"""

import serial, json, time, os

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
EXPECTED = [4, 9, 99, 1, 43, 8, 255, 0, 77, 3, 2, 1]

def main():
    src = open(os.path.join(os.path.dirname(__file__),
                            '..', 'programs', 'test_new_incdec.asm')).read()
    ser = serial.Serial(PORT, 115200, timeout=30)
    time.sleep(0.5)
    ser.reset_input_buffer()

    # Reset CPU
    ser.write(b'RESET\n')
    try: ser.readline()
    except: pass
    time.sleep(0.2)

    # Upload
    escaped = src.replace('\n', '\\n')
    payload = f'ASM:{escaped}\n'.encode()
    ser.reset_input_buffer()
    for i in range(0, len(payload), 4096):
        ser.write(payload[i:i+4096]); time.sleep(0.05)
    r = json.loads(ser.readline().decode().strip())
    if not r.get('ok'):
        print(f'ASSEMBLE FAILED: {r}')
        print('→ did you reflash the ESP32 after updating isa.h?')
        return False
    print(f'ASM OK, size={r.get("code", 0)}B')
    ser.write(b'UPLOAD\n'); ser.readline()

    # Run with multi-capture (up to 16 outputs)
    ser.write(b'RUNNB:50000,1,16\n')
    while True:
        try:
            line = ser.readline().decode().strip()
            r2 = json.loads(line)
            if 'hist' in r2: break
        except:
            print('RUN FAILED')
            return False
    ser.close()

    hist = r2.get('hist', [])
    cnt = r2.get('cnt', 0)
    print(f'Got {cnt} outputs: {hist[:cnt]}')
    print(f'Expected: {EXPECTED}')
    if hist[:cnt] == EXPECTED:
        print('\n✓ ALL NEW OPCODES WORKING')
        return True
    else:
        # Which test failed?
        labels = ['dec$d(5→4)', 'dec$c(10→9)', 'dec$b(100→99)',
                  'inc$d(0→1)', 'inc$c(42→43)', 'inc$b(7→8)',
                  'dec$d wrap(0→255)', 'inc$d wrap(255→0)',
                  'dec$d ZF(→77)', 'loop 3', 'loop 2', 'loop 1']
        for i, (got, exp, lbl) in enumerate(zip(hist[:cnt], EXPECTED, labels)):
            mark = '✓' if got == exp else '✗'
            print(f'  [{i}] {mark} {lbl}: got={got} expected={exp}')
        if cnt < len(EXPECTED):
            print(f'  missing outputs {cnt}..{len(EXPECTED)-1}')
        return False

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
