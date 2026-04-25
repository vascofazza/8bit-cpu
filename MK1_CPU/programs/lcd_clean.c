/*
 * lcd_clean.c — canonical reference: read DS3231 temperature, display on LCD.
 *
 * Writes the two-digit Celsius temperature to the top-left of a 16x2 LCD
 * connected via a PCF8574 I2C backpack, reading the DS3231 RTC on the
 * same I2C bus.
 *
 * Demonstrates the idioms the MK1 toolchain currently handles cleanly:
 *
 *   1. `i2c_init()` + `lcd_init()` once. The device-helper contract keeps
 *      the bus idle between device calls — no manual `i2c_bus_reset()`.
 *
 *   2. `rtc_read_temp()` uses repeated-START internally for an atomic
 *      register-pointer-set + data-read transaction.
 *
 *   3. Combined declaration+initialization (`unsigned char t = …;`) keeps
 *      the statement count below the Phase 7 auto-split threshold (8).
 *      Staying under the threshold matters because auto-split routes the
 *      return value of an I2C call through a data-page transfer slot; that
 *      code path still has a known gap (see pending task: register-passing
 *      overlay call convention). For a simple example, stay below 8 stmts.
 *
 *   4. Division/modulo (`/`, `%`) are NOT implemented in mk1cc2 — they
 *      silently return the operand unchanged. Use repeated subtraction
 *      in a while loop for digit extraction.
 *
 *   5. `halt()` emits `hlt` + infinite-loop trap so the display stays
 *      stable on ESP32-driven clock. On auto (555) clock, HLT gates the
 *      oscillator directly; the trap is harmless there.
 *
 * Expected LCD:  "NN"  where NN is the current temperature in °C
 */

void main() {
    i2c_init();
    lcd_init();

    unsigned char t = rtc_read_temp();

    /* Explicit clear — placed AFTER a non-lcd_init statement so the
     * peephole doesn't elide it. lcd_init() is init-only and does NOT
     * re-run on hardware reset; without this, hitting reset would
     * append to stale display content.
     *
     * Using lcd_clear() (not lcd_cmd(0x01)) because the former inlines
     * a ~5B raw post-clear delay, while the latter pulls in the full
     * ~31B __delay_Nms helper for a calibrated 2ms delay — which would
     * overflow the code page in this already-tight program. */
    lcd_clear();

    unsigned char tens = 0;

    /* Digit extraction via repeated subtraction.
     * After the loop: tens = t/10, t = t%10. */
    while (t >= 10) {
        t = t - 10;
        tens = tens + 1;
    }

    lcd_char(tens + 48);    /* 48 = ASCII '0' */
    lcd_char(t + 48);
    lcd_char(0xDF);         /* HD44780 ROM A00 degree symbol */
    lcd_char('C');

    halt();
}
