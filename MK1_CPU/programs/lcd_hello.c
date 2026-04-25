// LCD1602 "Hi" via I2C at 0x27 through 82C55 PPI
// PCF8574 mapping: P0=RS, P1=RW, P2=EN, P3=BL, P4-P7=D4-D7

// I2C bus control via 82C55 Port C
// PC7 = SDA drive (2N7000 MOSFET, inverted: 1=LOW)
// PC6 = SCL
// PA0 = SDA read-back

// Port C values:
// 0x00 = SDA released, SCL LOW
// 0x40 = SDA released, SCL HIGH
// 0x80 = SDA LOW, SCL LOW
// 0xC0 = SDA LOW, SCL HIGH

void i2c_start() {
    exw(0x40, 2, 0);  // SDA HIGH, SCL HIGH
    exw(0xC0, 2, 0);  // SDA LOW, SCL HIGH = START
    exw(0x80, 2, 0);  // SDA LOW, SCL LOW
}

void i2c_stop() {
    exw(0x80, 2, 0);  // SDA LOW, SCL LOW
    exw(0xC0, 2, 0);  // SDA LOW, SCL HIGH
    exw(0x40, 2, 0);  // SDA HIGH, SCL HIGH = STOP
}

void i2c_send_byte(unsigned char b) {
    unsigned char i;
    for (i = 0; i < 8; i++) {
        if (b & 0x80) {
            exw(0x00, 2, 0);  // SDA HIGH, SCL LOW
            exw(0x40, 2, 0);  // SDA HIGH, SCL HIGH
            exw(0x00, 2, 0);  // SDA HIGH, SCL LOW
        } else {
            exw(0x80, 2, 0);  // SDA LOW, SCL LOW
            exw(0xC0, 2, 0);  // SDA LOW, SCL HIGH
            exw(0x80, 2, 0);  // SDA LOW, SCL LOW
        }
        b = b << 1;
    }
    // ACK clock (don't check)
    exw(0x00, 2, 0);  // SDA released, SCL LOW
    exw(0x40, 2, 0);  // SCL HIGH
    exw(0x00, 2, 0);  // SCL LOW
}

void i2c_write(unsigned char data) {
    i2c_start();
    i2c_send_byte(0x4E);  // address 0x27 write
    i2c_send_byte(data);
    i2c_stop();
}

void lcd_nibble(unsigned char val) {
    // 3 writes per nibble: data, data|EN, data
    i2c_write(val);
    i2c_write(val | 0x04);
    i2c_write(val);
}

void lcd_cmd(unsigned char cmd) {
    // High nibble (RS=0, BL=1)
    lcd_nibble((cmd & 0xF0) | 0x08);
    // Low nibble
    lcd_nibble(((cmd << 4) & 0xF0) | 0x08);
}

void lcd_char(unsigned char ch) {
    // High nibble (RS=1, BL=1)
    lcd_nibble((ch & 0xF0) | 0x09);
    // Low nibble
    lcd_nibble(((ch << 4) & 0xF0) | 0x09);
}

void delay() {
    unsigned char i = 1;
    do { i++; } while (i != 0);
}

void long_delay() {
    unsigned char j;
    for (j = 0; j < 70; j++) {
        delay();
    }
}

void main() {
    // Init 82C55: PA=input, PB=output, PC upper=output, PC lower=output
    exw(0x90, 3, 0);

    // Bus recovery
    unsigned char k;
    for (k = 0; k < 9; k++) {
        exw(0x00, 2, 0);
        exw(0x40, 2, 0);
    }
    i2c_stop();

    // Initial backlight + 1s delay
    i2c_write(0x08);
    long_delay();

    // 3x reset nibble (0x30 = data, BL on)
    lcd_nibble(0x38);
    delay(); delay(); delay();
    lcd_nibble(0x38);
    delay();
    lcd_nibble(0x38);

    // Switch to 4-bit mode
    lcd_nibble(0x28);

    // Function set: 2 lines, 5x8
    lcd_cmd(0x28);
    // Display on, cursor off
    lcd_cmd(0x0C);
    // Clear display
    lcd_cmd(0x01);
    delay(); delay();
    // Entry mode: left to right
    lcd_cmd(0x06);
    // Home
    lcd_cmd(0x02);
    delay(); delay();

    // Write "Hi"
    lcd_char('H');
    lcd_char('i');

    halt();
}
