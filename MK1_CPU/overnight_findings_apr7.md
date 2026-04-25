# Overnight Findings - April 7, 2026

## Combined EEPROM program: 254 bytes, FITS
File: `/tmp/eeprom_combined.asm`
- VIA init + I2C SQW config + single-phase calibration + EEPROM write+read
- Single-phase cal saves 25 bytes (HIGH phase only, D_half/2 = D/4)
- Shared `__i2c_wr_addr` subroutine saves 9 bytes
- NACK→STOP fall-through saves 2 bytes
- D/4 calibrated delay (~250ms, safe for EEPROM at any clock speed)

## I2C reads broken — SDA pull-up likely disconnected
After board cleaning, ALL I2C reads return 0:
- EEPROM data reads: 0
- DS3231 seconds register: 0
- I2C address scan: falsely reports ACK (PB0 floats LOW = always reads 0)

**Probable cause: 4.7kΩ SDA pull-up (PB0 to VCC) loose from cleaning.**
- SCL pull-up is fine (I2C clock works — devices respond)
- SQW on PA0 works fine (separate 5.1kΩ pull-up)
- VIA register reads work fine (J4 reseated earlier)

## Action needed
Check and reseat the SDA pull-up resistor (4.7kΩ from I2C SDA line to VCC)
on the VIA daughter board breadboard. Then retest the combined program.

## Beep intermittent issue
The stopwatch beep skips some ticks (hits 170, misses 150/160/180, hits 190/200).
On RUNLOG: beep works perfectly to 240+. Only on LEDC/auto clock.
Not blocking — cosmetic issue. Counter and timing are correct.
