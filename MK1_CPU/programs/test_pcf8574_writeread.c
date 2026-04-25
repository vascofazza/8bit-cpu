/* PCF8574 write-then-read verification test.
 *
 * Writes pattern A (0x08 — backlight only), reads back.
 * Writes pattern B (0x00 — all low), reads back.
 *
 * If writes reach PCF8574, readback_A != readback_B (different inputs to LCD
 * circuit → different pin states observed). If writes DON'T reach (PCF8574
 * stuck), both readbacks return the same value.
 *
 * Output via OI (4 outputs):
 *   1. 0x08 (pattern A we wrote)
 *   2. readback_A
 *   3. 0x00 (pattern B we wrote)
 *   4. readback_B
 *
 * Detection: readback_A != readback_B  →  writes reached PCF8574  →  PASS
 *            readback_A == readback_B  →  writes did NOT reach    →  FAIL
 */
void main() {
    i2c_init();

    /* Pattern A: backlight on, everything else low */
    i2c_start();
    i2c_send_byte(0x4E);
    i2c_send_byte(0x08);
    i2c_stop();
    out(0x08);

    i2c_start();
    i2c_send_byte(0x4F);
    unsigned char read_a;
    read_a = i2c_read_byte();
    i2c_nack();
    i2c_stop();
    out(read_a);

    /* Pattern B: all low (backlight off too) */
    i2c_start();
    i2c_send_byte(0x4E);
    i2c_send_byte(0x00);
    i2c_stop();
    out(0x00);

    i2c_start();
    i2c_send_byte(0x4F);
    unsigned char read_b;
    read_b = i2c_read_byte();
    i2c_nack();
    i2c_stop();
    out(read_b);

    /* Restore backlight on for visibility */
    i2c_start();
    i2c_send_byte(0x4E);
    i2c_send_byte(0x08);
    i2c_stop();

    halt();
}
