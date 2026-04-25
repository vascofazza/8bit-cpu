unsigned char read_temp() {
    unsigned char t;
    t = rtc_read_temp();
    return t;
}

void info_screen(unsigned char t) {
    lcd_cmd(0x01);
    lcd_print("MK1 8-bit CPU");
    lcd_cmd(0xC0);
    printf("%d\xDFC  Running!", t);
}

void main() {
    i2c_init();
    lcd_init();
    unsigned char t;
    t = read_temp();
    out(t);
    info_screen(t);
    halt();
}
