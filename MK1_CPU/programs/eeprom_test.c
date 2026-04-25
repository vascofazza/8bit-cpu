// EEPROM write+read test via C compiler
// Write 0x42 to address 0x0A00, read back, display

void main(void) {
    i2c_init();
    
    // Write 0x42 to EEPROM address 0x0A00
    i2c_start();
    i2c_send_byte(0xAE);
    i2c_send_byte(0x0A);
    i2c_send_byte(0x00);
    i2c_send_byte(0x42);
    i2c_stop();
    
    // Write cycle delay (~20ms)
    unsigned char i = 0;
    do {
        unsigned char j = 255;
        do {
            j = j - 1;
        } while (j);
        i = i + 1;
    } while (i < 3);
    
    // Set read address
    i2c_start();
    i2c_send_byte(0xAE);
    i2c_send_byte(0x0A);
    i2c_send_byte(0x00);
    i2c_stop();
    
    // Read byte
    i2c_start();
    i2c_send_byte(0xAF);
    unsigned char val = i2c_read_byte();
    i2c_nack();
    i2c_stop();
    
    out(val);
    halt();
}
