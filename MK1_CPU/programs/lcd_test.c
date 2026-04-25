/* LCD diagnostic test: init, clear, cursor home, write string.
 * lcd_init() handles: 2-line mode (0x28), display on (0x0C),
 * clear (0x01 + 5ms delay), entry mode (0x06).
 * Cursor is at 0,0 after init. We then write characters directly.
 * Expected: "MK1 TEST" on line 1, display on, out(42) on success.
 */
void main() {
    i2c_init();
    lcd_init();
    lcd_char('M');
    lcd_char('K');
    lcd_char('1');
    lcd_char(' ');
    lcd_char('T');
    lcd_char('E');
    lcd_char('S');
    lcd_char('T');
    out(42);
    halt();
}
