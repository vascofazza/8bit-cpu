#!/usr/bin/env python3
"""LCD output regression test.

Compiles a set of programs in different modes (flat / init extraction / overlay)
and uploads each to hardware. Prompts the user to confirm whether the LCD
displays the expected output.

This catches the class of bugs where I2C "succeeds" (no error from __i2c_sb)
but the PCF8574/LCD doesn't actually receive/display the data — which the
existing OI-based regression tests do NOT detect.

Usage:
    python3 lcd_regression_test.py
"""
import os
import subprocess
import sys
import time
import json
import serial

PORT = '/dev/cu.usbmodem3C8427C2E7C82'
COMPILER = os.path.join(os.path.dirname(__file__), 'mk1cc2.py')
PROG_DIR = os.path.join(os.path.dirname(__file__), '..', 'programs')


def compile_c(source, eeprom=False):
    """Compile C source to assembly. Returns (asm_text, mode_str) or (None, err)."""
    src_path = '/tmp/_lcd_regtest.c'
    asm_path = '/tmp/_lcd_regtest.asm'
    with open(src_path, 'w') as f:
        f.write(source)
    args = ['python3', COMPILER, src_path, '-O']
    if eeprom:
        args.append('--eeprom')
    args.extend(['-o', asm_path])
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr
    with open(asm_path) as f:
        asm = f.read()
    # Detect mode from compiler stderr
    mode = 'flat'
    if 'two-stage boot (overlay system)' in r.stderr:
        mode = 'overlay'
    elif 'two-stage boot (init extraction)' in r.stderr:
        mode = 'init-extraction'
    return asm, mode


def drain(ser, settle_secs=0.5):
    """Drain everything from serial buffer until quiet for `settle_secs`."""
    ser.timeout = 0.1
    quiet_start = None
    while True:
        data = ser.read(8192)
        if data:
            quiet_start = None
        else:
            if quiet_start is None:
                quiet_start = time.time()
            elif time.time() - quiet_start > settle_secs:
                return


def send_command(ser, cmd_bytes, response_timeout=30):
    """Send a command, wait for one JSON response line. Returns dict or None.

    Tolerates non-JSON heartbeat lines and accumulated garbage from previous
    commands (e.g. when a long-running RUN was still printing when the user
    was reading the LCD).
    """
    ser.write(cmd_bytes)
    deadline = time.time() + response_timeout
    while time.time() < deadline:
        ser.timeout = max(0.5, deadline - time.time())
        line = ser.readline().decode(errors='replace').strip()
        if not line:
            continue
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue  # garbage, keep reading
    return None


def upload_and_run(ser, asm, cycles=5000000):
    """Upload and run an assembly program. Returns RUN response dict or None.

    Resilient to: garbage in the serial buffer left from previous slow-response
    interactions, mid-stream heartbeat lines, partial output from prior RUNs.
    """
    # First, kill anything still running and drain everything
    ser.write(b'\n')   # break any pending input on ESP32 side
    drain(ser, settle_secs=0.5)

    # Send ASM. Chunked to avoid overflowing the ESP32 UART RX buffer.
    escaped = asm.replace('\n', '\\n')
    payload = f'ASM:{escaped}\n'.encode()
    CHUNK = 4096
    for i in range(0, len(payload), CHUNK):
        ser.write(payload[i:i+CHUNK])
        time.sleep(0.05)

    # Wait for ASM response — large programs can take a few seconds to assemble.
    resp = None
    deadline = time.time() + 30
    while time.time() < deadline:
        ser.timeout = max(0.5, deadline - time.time())
        line = ser.readline().decode(errors='replace').strip()
        if line.startswith('{'):
            try:
                resp = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if resp is None or not resp.get('ok'):
        return None

    # UPLOAD then RUN
    upload_resp = send_command(ser, b'UPLOAD\n', response_timeout=20)
    if upload_resp is None or not upload_resp.get('ok'):
        return None
    return send_command(ser, f'RUN:{cycles},1\n'.encode(), response_timeout=30)


def prompt_user(expected, previous=None):
    """Ask user what they see on the LCD. Returns 'pass'/'fail'/'skip'.

    Take your time — the test stays paused while you read the LCD. The
    serial connection is idle (no data flowing) so it can wait indefinitely.
    """
    print(f'  Expected on LCD: {expected!r}')
    if previous is not None:
        print(f'  (Before this test, LCD was showing: {previous!r}.')
        print(f'   If you still see that, the test silently failed.)')
    print('  (take your time looking at the LCD — connection stays idle)')
    while True:
        try:
            ans = input(
                '  Enter result: [p]ass / [f]ail / [s]kip / [r]erun / '
                '<paste actual content>: '
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 'skip'
        if not ans:
            continue
        c = ans[0].lower()
        if c == 'p':
            return 'pass'
        if c == 'f':
            return 'fail'
        if c == 's':
            return 'skip'
        if c == 'r':
            return 'rerun'
        # Anything else: treat as user-pasted LCD content. Compare to expected.
        return 'pass' if ans == expected else 'fail'


# Test programs: (name, c_source, expected_lcd_output, eeprom_mode)
# IMPORTANT: each test must display a UNIQUE string. Otherwise residual content
# from a previous test could be mistaken for the current test passing.
TESTS = [
    (
        'flat-tiny: lcd_init + 4 chars (flat mode)',
        '''
void main() {
    i2c_init();
    lcd_init();
    lcd_char('F'); lcd_char('L'); lcd_char('A'); lcd_char('T');
    out(42);
    halt();
}
''',
        'FLAT',
        False,
    ),
    (
        'init-extraction: lcd_init + 4 chars + arithmetic',
        '''
void main() {
    i2c_init();
    lcd_init();
    lcd_char('I'); lcd_char('N'); lcd_char('I'); lcd_char('T');
    unsigned char a; a = 1;
    a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1;
    a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1;
    a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1; a=a+1;
    out(a);
    halt();
}
''',
        'INIT',
        False,
    ),
    (
        'init-extraction: read RTC temp + display',
        open(os.path.join(PROG_DIR, 'lcd_temp.c')).read(),
        '<temperature>°C  (e.g., "21°C" or "22°C")',
        False,
    ),
    (
        'overlay: clock display HH:MM (overlay mode)',
        open(os.path.join(PROG_DIR, 'overlay_clock.c')).read(),
        'HH:MM   (current time from RTC)',
        True,
    ),
]


def main():
    print('MK1 LCD Output Regression Test')
    print(f'Port: {PORT}')
    print()
    print('This test verifies actual LCD display output, not just I2C completion.')
    print('You must visually confirm what the LCD shows after each test.')
    print()

    ser = serial.Serial(PORT, 115200, timeout=10)
    time.sleep(2)
    ser.reset_input_buffer()

    results = []
    previous_expected = None  # what the LCD was showing before the current test
    for name, source, expected, eeprom in TESTS:
        print(f'── {name} ──')
        asm, mode = compile_c(source, eeprom=eeprom)
        if asm is None:
            print(f'  [SKIP] compile failed: {mode[:200]}')
            results.append((name, 'SKIP'))
            continue
        print(f'  Compiled in {mode} mode')

        # Loop allows the user to request a rerun if they missed the LCD update.
        while True:
            result = upload_and_run(ser, asm)
            if result is None:
                print('  [FAIL] upload/run failed')
                results.append((name, 'FAIL'))
                break
            print(f'  Run: cyc={result.get("cyc")}, val={result.get("val")}')

            verdict = prompt_user(expected, previous=previous_expected)
            if verdict == 'rerun':
                print('  Rerunning...')
                continue
            status = {'pass': 'PASS', 'fail': 'FAIL', 'skip': 'SKIP'}[verdict]
            results.append((name, status))
            print(f'  → {status}')
            # Only update "previous" if the test actually wrote something new.
            # On FAIL, the LCD likely still shows whatever it was before.
            if status == 'PASS':
                previous_expected = expected
            break
        print()

    print('── Summary ──')
    for name, status in results:
        marker = {'PASS': '✓', 'FAIL': '✗', 'SKIP': '–'}[status]
        print(f'  {marker} [{status}] {name}')
    pass_count = sum(1 for _, s in results if s == 'PASS')
    fail_count = sum(1 for _, s in results if s == 'FAIL')
    skip_count = sum(1 for _, s in results if s == 'SKIP')
    print(f'\nResults: {pass_count} pass, {fail_count} fail, {skip_count} skip '
          f'(of {len(results)} total)')
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
