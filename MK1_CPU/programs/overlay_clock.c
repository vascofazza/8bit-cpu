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

void show_hm(unsigned char h, unsigned char m) {
    lcd_cmd(0x01);
    lcd_char((h >> 4) + 48);
    lcd_char((h & 0x0F) + 48);
    lcd_char(':');
    lcd_char((m >> 4) + 48);
    lcd_char((m & 0x0F) + 48);
}

void main() {
    i2c_init();
    lcd_init();
    unsigned char h;
    unsigned char m;
    h = rtc_reg(2);
    m = rtc_reg(1);
    out(m);
    show_hm(h, m);
    halt();
}
