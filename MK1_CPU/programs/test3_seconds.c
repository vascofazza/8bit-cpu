unsigned char read_sec() {
    unsigned char s;
    s = rtc_read_seconds();
    return s;
}

void show_sec(unsigned char bcd) {
    lcd_cmd(0x01);
    lcd_print("Sec: ");
    lcd_char((bcd >> 4) + 48);
    lcd_char((bcd & 0x0F) + 48);
}

void main() {
    i2c_init();
    lcd_init();
    unsigned char s;
    s = read_sec();
    out(s);
    show_sec(s);
    halt();
}
