/* Display RTC temperature on LCD as "NN°C".
 * Uses inline digit extraction (not printf) because this single-number
 * display would pay ~60B for __print_u8_dec just for one call. */
void main() {
    i2c_init();
    lcd_init();
    unsigned char temp;
    temp = rtc_read_temp();
    i2c_bus_reset();
    unsigned char tens;
    tens = 0;
    while (temp >= 10) {
        temp = temp - 10;
        tens = tens + 1;
    }
    lcd_char(tens + 48);
    lcd_char(temp + 48);
    lcd_char(0xDF);
    lcd_char('C');
    out(temp);
    halt();
}
