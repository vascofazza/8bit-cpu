/* LCD + EEPROM overlay test: 3 display functions.
 * Tests EEPROM-backed overlays with LCD init + auto delay_cal.
 */
void show_greeting() {
    lcd_cmd(0x80);
    lcd_char('M'); lcd_char('K'); lcd_char('1');
    lcd_char(' '); lcd_char('C'); lcd_char('P'); lcd_char('U');
}

void show_temp() {
    unsigned char temp;
    temp = rtc_read_temp();
    lcd_cmd(0xC0);
    unsigned char tens; unsigned char ones;
    tens = 0; ones = temp;
    while (ones >= 10) { ones = ones - 10; tens = tens + 1; }
    if (tens > 0) { lcd_char(tens + 48); }
    lcd_char(ones + 48); lcd_char(0xDF); lcd_char('C');
}

void show_msg() {
    lcd_cmd(0x94);
    lcd_char('O'); lcd_char('K');
}

void main() {
    i2c_init();
    lcd_init();
    show_greeting();
    show_temp();
    show_msg();
    out(42);
    halt();
}
