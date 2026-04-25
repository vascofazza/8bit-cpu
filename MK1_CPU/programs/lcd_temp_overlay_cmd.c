unsigned char read_temp() {
    unsigned char temp;
    temp = rtc_read_temp();
    return temp;
}

void show_temp(unsigned char temp) {
    unsigned char tens;
    unsigned char ones;
    lcd_cmd(0x01);
    tens = 0;
    ones = temp;
    while (ones >= 10) {
        ones = ones - 10;
        tens = tens + 1;
    }
    if (tens > 0) {
        lcd_char(tens + 48);
    }
    lcd_char(ones + 48);
    lcd_char(0xDF);
    lcd_char('C');
}

void main() {
    i2c_init();
    lcd_init();
    unsigned char t;
    t = read_temp();
    out(t);
    show_temp(t);
    halt();
}
