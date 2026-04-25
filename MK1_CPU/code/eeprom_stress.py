#!/usr/bin/env python3
"""EEPROM stress test v3 — two-phase: calibrate once, then run tests.
Phase 1: Calibrate, store D/4 in data page addr 0.
Phase 2: Test programs read D/4 from data page, use delay_1ms."""

import requests, time, sys

BASE = "http://mk1.local"

I2C_SUBS = """
__i2c_sb:
	mov $a, $b
	ldi $a, 8
	mov $a, $c
.isb:
	mov $b, $a
	tst 0x80
	jnz .isbh
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	j .isbn
.isbh:
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	ldi $a, 0x02
	exw 0 2
.isbn:
	mov $b, $a
	sll
	mov $a, $b
	mov $c, $a
	dec
	mov $a, $c
	jnz .isb
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	exrw 0
	push $a
	ldi $a, 0x02
	exw 0 2
	pop $a
	ret
__i2c_sp:
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2
	ret
__i2c_rb:
	ldi $d, 0
	ldi $c, 8
.rb:
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	exrw 0
	push $a
	mov $d, $a
	sll
	mov $a, $d
	pop $a
	andi 0x01, $a
	or $d, $a
	mov $a, $d
	ldi $a, 0x02
	exw 0 2
	mov $c, $a
	dec
	mov $a, $c
	jnz .rb
	ret
"""

# delay_Nms: B = ms count. Reads D/4 from data[0] each iteration.
DELAY_SUBS = """
delay_Nms:
.dnms:
	clr $a
	deref		; A = data[0] = D/4
.dms:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	dec
	jnz .dms	; 13 cycles × D/4 ≈ 1ms
	mov $b, $a
	dec
	mov $a, $b
	jnz .dnms
	ret
"""

CALIBRATION_ASM = """
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0
	exw 0 2
	; Configure SQW
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xD0
	jal __i2c_sb
	ldi $a, 0x0E
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	jal __i2c_sp
	; Calibrate
.s1:
	exrw 1
	tst 0x01
	jz .s2
	j .s1
.s2:
	exrw 1
	tst 0x01
	jnz .cal
	j .s2
.cal:
	ldi $b, 0
.cal_hi_ovf:
	clr $a
.cal_hi_inner:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	dec
	jnz .cal_hi_inner
	mov $b, $a
	inc
	mov $a, $b
	exrw 1
	tst 0x01
	jz .cal_lo
	j .cal_hi_ovf
.cal_lo:
	clr $a
.cal_lo_inner:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	dec
	jnz .cal_lo_inner
	mov $b, $a
	inc
	mov $a, $b
	exrw 1
	tst 0x01
	jnz .cal_done
	j .cal_lo
.cal_done:
	; B = D. Compute D/4, store in data page addr 0.
	mov $b, $a
	slr
	slr
	ldi $b, 0
	ideref		; data[0] = D/4
	; Output D/4 for reference
	out
	clr $a
	exw 0 2
	hlt
""" + I2C_SUBS + """
	section data
	byte 0
"""


def make_write_read(addr_hi, addr_lo, value):
    """Write byte, delay 15ms, read back. Reads D/4 from data[0]."""
    return f"""
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0
	exw 0 2
	; Write
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, {addr_hi}
	jal __i2c_sb
	ldi $a, {addr_lo}
	jal __i2c_sb
	ldi $a, {value}
	jal __i2c_sb
	jal __i2c_sp
	; Delay 15ms
	ldi $b, 15
	jal delay_Nms
	; Read: set address
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, {addr_hi}
	jal __i2c_sb
	ldi $a, {addr_lo}
	jal __i2c_sb
	jal __i2c_sp
	; Read
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAF
	jal __i2c_sb
	jal __i2c_rb
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	nop
	nop
	ldi $a, 0x02
	exw 0 2
	jal __i2c_sp
	mov $d, $a
	out
	clr $a
	exw 0 2
	hlt
""" + I2C_SUBS + DELAY_SUBS + """
	section data
	byte 0
"""


def run_on_555(asm, timeout=30):
    """Assemble, upload, wait for 555 to run to HLT, read 7-seg value."""
    r = requests.post(f"{BASE}/assemble", data=asm, headers={"Content-Type": "text/plain"}).json()
    if r.get("errors"):
        return f"ASM_ERR:{r['errors']}"
    if r["code_size"] > 256:
        return f"TOO_BIG:{r['code_size']}"
    requests.post(f"{BASE}/upload")
    for _ in range(timeout):
        time.sleep(1)
        s = requests.get(f"{BASE}/status").json()
        if s["state"] == "halted":
            # Can't read OI on 555. Need user to switch to manual for that.
            # For now, trust the 7-seg.
            return None  # Can't read OI on 555 auto clock
    return "TIMEOUT"


def run_with_cycles(asm, max_cycles=5000000):
    """Assemble, upload, run via run_cycles. Returns OI value."""
    r = requests.post(f"{BASE}/assemble", data=asm, headers={"Content-Type": "text/plain"}).json()
    if r.get("errors"):
        return f"ASM_ERR:{r['errors']}"
    if r["code_size"] > 256:
        return f"TOO_BIG:{r['code_size']}"
    requests.post(f"{BASE}/upload")
    requests.post(f"{BASE}/run_cycles", params={"n": max_cycles, "us": 1})
    time.sleep(0.2)
    d = requests.get(f"{BASE}/read_output").json()
    if not d.get("captured"):
        return "NO_OI"
    return d["value"]


# ── Main ──
print("=== EEPROM Stress Test v3 ===\n")

# Check sizes
r = requests.post(f"{BASE}/assemble", data=CALIBRATION_ASM,
                   headers={"Content-Type": "text/plain"}).json()
print(f"Calibration program: {r['code_size']}B")

test_asm = make_write_read(0x03, 0x00, 42)
r = requests.post(f"{BASE}/assemble", data=test_asm,
                   headers={"Content-Type": "text/plain"}).json()
print(f"Write+read program: {r['code_size']}B")

if r['code_size'] > 256:
    print("Write+read program too big!")
    sys.exit(1)

print("\nPhase 1: Calibrate on 555 auto clock...")
print("(Waiting for calibration to complete — takes ~3 seconds)")
result = run_on_555(CALIBRATION_ASM, timeout=10)
if result == "TIMEOUT":
    print("Calibration timed out!")
    sys.exit(1)
print("Calibration done. D/4 stored in data page.")

print("\nNow switch SW3 to MANUAL so I can use run_cycles to read OI.")
print("Press Enter when ready...")
input()

print("\nPhase 2: Write/read tests via run_cycles...")
passes = 0
fails = 0
test_cases = [
    (0x03, 0x00, 0x00),
    (0x03, 0x01, 0xFF),
    (0x03, 0x02, 0xAA),
    (0x03, 0x03, 0x55),
    (0x03, 0x04, 0x01),
    (0x03, 0x05, 0x80),
    (0x03, 0x06, 0x7F),
    (0x03, 0x07, 42),
    (0x03, 0x08, 99),
    (0x03, 0x09, 200),
]
for hi, lo, val in test_cases:
    asm = make_write_read(hi, lo, val)
    r = run_with_cycles(asm)
    addr = (hi << 8) | lo
    if isinstance(r, str):
        print(f"  [FAIL] addr=0x{addr:04X} val={val}: {r}")
        fails += 1
    elif r == val:
        print(f"  [PASS] addr=0x{addr:04X} val={val}")
        passes += 1
    else:
        print(f"  [FAIL] addr=0x{addr:04X} wrote {val}, got {r}")
        fails += 1

# Re-read all to check persistence
print("\n--- Persistence check ---")
for hi, lo, val in test_cases:
    # Just read (no write) — set address then read
    read_asm = f"""
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0
	exw 0 2
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, {hi}
	jal __i2c_sb
	ldi $a, {lo}
	jal __i2c_sb
	jal __i2c_sp
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAF
	jal __i2c_sb
	jal __i2c_rb
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	nop
	nop
	ldi $a, 0x02
	exw 0 2
	jal __i2c_sp
	mov $d, $a
	out
	clr $a
	exw 0 2
	hlt
""" + I2C_SUBS
    r = run_with_cycles(read_asm)
    addr = (hi << 8) | lo
    if r == val:
        passes += 1
        print(f"  [PASS] addr=0x{addr:04X} val={val}")
    else:
        fails += 1
        print(f"  [FAIL] addr=0x{addr:04X} expected={val}, got={r}")

print(f"\n=== Results: {passes} passed, {fails} failed ===")
sys.exit(1 if fails > 0 else 0)
