unsigned char rtc_reg(unsigned char reg) {
    i2c_start();
    i2c_send_byte(0xD0);
    i2c_send_byte(reg);
    i2c_stop();
    i2c_start();
    i2c_send_byte(0xD1);
    unsigned char v;
    v = i2c_read_byte();
    i2c_nack();
    i2c_stop();
    return v;
}

void show_time(unsigned char h, unsigned char m, unsigned char s) {
    lcd_cmd(0x80);
    lcd_char((h >> 4) + 48);
    lcd_char((h & 0x0F) + 48);
    lcd_char(':');
    lcd_char((m >> 4) + 48);
    lcd_char((m & 0x0F) + 48);
    lcd_char(':');
    lcd_char((s >> 4) + 48);
    lcd_char((s & 0x0F) + 48);
}

void show_temp(unsigned char t) {
    lcd_cmd(0xC0);
    unsigned char tens;
    unsigned char ones;
    tens = 0;
    ones = t;
    while (ones >= 10) { ones = ones - 10; tens = tens + 1; }
    if (tens > 0) { lcd_char(tens + 48); }
    lcd_char(ones + 48);
    lcd_char(0xDF);
    lcd_char('C');
}

void main() {
    i2c_init();
    lcd_init();
    lcd_cmd(0x01);
    unsigned char h;
    unsigned char m;
    unsigned char s;
    unsigned char t;
    h = rtc_reg(2);
    m = rtc_reg(1);
    s = rtc_reg(0);
    t = rtc_reg(0x11);
    out(t);
    show_time(h, m, s);
    show_temp(t);
    halt();
}
