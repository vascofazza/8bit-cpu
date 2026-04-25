// I2C scan with LCD display — scans bus 8-127, shows found addresses on LCD
// Uses VIA DDR-only I2C (W65C22S)

unsigned char results[16];
unsigned char hex_val;

void scan_all() {
    unsigned char count = 0;
    unsigned char addr;
    for (addr = 8; addr < 128; addr++) {
        i2c_start();
        i2c_send_byte(addr << 1);
        // ACK check: release SDA, clock SCL, read
        exw(0x02, 2, 0);   // SDA high, SCL low
        nop(5);
        exw(0x00, 2, 0);   // SDA high, SCL high
        nop(5);
        unsigned char val = via_read_portb();
        exw(0x02, 2, 0);   // SCL low
        i2c_stop();
        if ((val & 0x01) == 0) {
            results[count] = addr;
            count++;
        }
    }
    results[count] = 0;  // sentinel
}

void show_hex() {
    unsigned char hi = hex_val >> 4;
    unsigned char lo = hex_val & 0x0F;
    if (hi > 9) {
        lcd_char(hi + 55);  // 'A'-'F'
    } else {
        lcd_char(hi + 48);  // '0'-'9'
    }
    if (lo > 9) {
        lcd_char(lo + 55);
    } else {
        lcd_char(lo + 48);
    }
}

void main() {
    nop(3);
    // VIA init
    exw(0x00, 0, 0);   // ORB = 0
    exw(0x00, 2, 0);   // DDRB = 0 (idle)
    exw(0x03, 2, 0);   // both LOW
    exw(0x01, 2, 0);   // SCL HIGH
    exw(0x00, 2, 0);   // idle

    lcd_init();

    lcd_char('I');
    lcd_char('2');
    lcd_char('C');

    scan_all();

    // Display found addresses
    unsigned char i;
    unsigned char count = 0;
    for (i = 0; i < 16; i++) {
        if (results[i] == 0) break;
        lcd_char(' ');
        hex_val = results[i];
        show_hex();
        count++;
    }

    out(count);
    halt();
}
