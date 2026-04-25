// MK1 EEPROM + RTC demo
// Read temperature, store in EEPROM, read back, display

void main(void) {
    i2c_init();
    
    unsigned char temp = rtc_read_temp();
    eeprom_write_byte(0x0B00, temp);
    unsigned char val = eeprom_read_byte(0x0B00);
    
    out(val);
    halt();
}
