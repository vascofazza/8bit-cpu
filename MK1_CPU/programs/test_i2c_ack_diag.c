/* I2C ACK diagnostic test.
 *
 * In init extraction mode, RTC reads succeed but PCF8574 writes silently
 * fail (LCD doesn't display). This test outputs the ACK bit after each
 * I2C send so we can see at what point the slave stops responding.
 *
 * Forced into init extraction by padding with arithmetic.
 *
 * OI output sequence (read with RUNNB:n,1,16):
 *   0xA1   sentinel: starting PCF8574 write attempt
 *   ack    ACK after sending 0x4E (PCF8574 write addr)  — 0=ACK, 1=NAK
 *   ack    ACK after sending 0x08 (data: backlight only)
 *   0xA2   sentinel: starting RTC write attempt (control)
 *   ack    ACK after sending 0xD0 (RTC write addr)
 *   ack    ACK after sending 0x11 (register pointer)
 *   0xA3   sentinel: starting RTC read attempt
 *   ack    ACK after sending 0xD1 (RTC read addr)
 *   0xFF   sentinel: end
 *
 * Expected if PCF8574 is responding: all ACKs should be 0.
 * If PCF8574 is silently broken: first two ACKs (PCF8574) will be 1.
 */
void main() {
    i2c_init();
    lcd_init();   /* matches lcd_temp.c structure - lcd_init runs in stage 1 */

    /* === STAGE 2 begins after self-copy === */

    unsigned char ack;

    out(0xA1);
    i2c_start();
    ack = i2c_send_byte(0x4E);
    out(ack);
    ack = i2c_send_byte(0x08);
    out(ack);
    i2c_stop();

    out(0xA2);
    i2c_start();
    ack = i2c_send_byte(0xD0);
    out(ack);
    ack = i2c_send_byte(0x11);
    out(ack);
    i2c_stop();

    out(0xA3);
    i2c_start();
    ack = i2c_send_byte(0xD1);
    out(ack);
    i2c_stop();

    out(0xFF);

    /* Padding to force init extraction */
    unsigned char p; p = 1;
    p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1;
    p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1; p=p+1;

    halt();
}
