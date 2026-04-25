unsigned char read_temp() {
    unsigned char t;
    t = rtc_read_temp();
    return t;
}

void display(unsigned char t) {
    lcd_cmd(0x01);
    printf("Temp: %d\xDFC", t);
}

void main() {
    i2c_init();
    lcd_init();
    unsigned char t;
    t = read_temp();
    out(t);
    display(t);
    halt();
}
