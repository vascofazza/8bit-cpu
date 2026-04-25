# Investigation Status - April 8, 2026 (updated)

## FOUND: First jal after upload needs stack warmup
The very first `jal` instruction after upload hangs on LEDC. Adding `push $a; pop $a` 
before the first `jal` fixes it. Likely caused by STK pin (released to INPUT by ESP32) 
not being stable for the first stack page access.

**Proof:**
- `jal __i2c_st` as FIRST jal: HANGS on LEDC
- Same code with `push $a; pop $a` before first jal: WORKS (halted, OI=2)
- Inline START (no jal): WORKS
- Stopwatch works because inline START happens before first `jal __i2c_sb`

## REMAINING: PB0 (SDA) reads 0 via exrw 0
Even with the stack warmup fix, the combined EEPROM program hangs because I2C 
data reads return 0. All `exrw 0` reads show PB0=0 (SDA stuck LOW).

Verified on:
- run_cycles at all speeds (us=1 to us=100): PB0=0
- All firmware versions (old and new): PB0=0
- With and without I2C operations: PB0=0
- With ORB=0x03 set before DDRB=0: PB0=0

Works:
- VIA can DRIVE PB0 HIGH (ORB=1, DDRB=1 → reads 1)
- exrw 1 (port A) works (stopwatch SQW calibration: 1.0/s)
- exrw 2 (DDRB readback) works (0xAA)
- SCL (PB1) reads correctly (1 from pull-up)

## Combined program: 256 bytes (with warmup), ready
File: `/tmp/eeprom_combined_v2.asm`
Will work once PB0/SDA reads correctly.

## Files
- `/tmp/eeprom_combined_v2.asm` — 256B combined with stack warmup
- `/tmp/ee_diag_inline.asm` — 145B diagnostic (works on LEDC, outputs PB value)
- `/tmp/ee_diag_warmup.asm` — 150B diagnostic with stack warmup (works on LEDC)

## Summary for user

### What's working:
- Stopwatch: 1.0/s on LEDC, SQW calibration correct
- Combined EEPROM program: 256 bytes, fits, calibration works
- Stack warmup found and fixed (`push $a; pop $a` before first jal)

### What's blocked:
- PB0 (SDA) reads 0 in ALL tests — via run_cycles AND LEDC
- This causes ALL I2C data reads to return 0
- EEPROM write+read cannot complete
- Tested across all firmware versions, all clock speeds, all methods

### What to check physically:
- SDA (PB0 / VIA pin 10) pull-up resistor: is it actually pulling to VCC?
- Measure voltage on PB0 with multimeter when VIA is idle (DDRB=0)
- If PB0 measures LOW, something on the I2C bus is pulling SDA down
- Try disconnecting EEPROM module from SDA — does PB0 go HIGH?
- Try disconnecting DS3231 from SDA — does PB0 go HIGH?
