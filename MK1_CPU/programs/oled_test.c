// SSD1306 test — minimal init + render "23°C" with font glyphs

unsigned char font[] = {
    0x3E, 0x51, 0x49, 0x45, 0x3E,
    0x00, 0x42, 0x7F, 0x40, 0x00,
    0x42, 0x61, 0x51, 0x49, 0x46,
    0x21, 0x41, 0x45, 0x4B, 0x31,
    0x18, 0x14, 0x12, 0x7F, 0x10,
    0x27, 0x45, 0x45, 0x45, 0x39,
    0x3C, 0x4A, 0x49, 0x49, 0x30,
    0x01, 0x71, 0x09, 0x05, 0x03,
    0x36, 0x49, 0x49, 0x49, 0x36,
    0x06, 0x49, 0x49, 0x29, 0x1E,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x06, 0x09, 0x09, 0x06, 0x00,
    0x3E, 0x41, 0x41, 0x41, 0x22
};

void oled_glyph(unsigned char idx) {
    unsigned char base;
    unsigned char i;
    base = idx * 5;
    i2c_start();
    i2c_send_byte(0x78);
    i2c_send_byte(0x40);
    for (i = 0; i < 5; i++) {
        i2c_send_byte(font[base + i]);
    }
    i2c_send_byte(0x00);
    i2c_stop();
}

void main() {
    i2c_init();
    i2c_bus_reset();

    // Minimal SSD1306 init (skip defaults: clock, offset, contrast, etc.)
    i2c_start();
    i2c_send_byte(0x78);
    i2c_send_byte(0x00);
    i2c_send_byte(0xAE);        // display off
    i2c_send_byte(0xA8); i2c_send_byte(0x3F);  // mux 64
    i2c_send_byte(0x8D); i2c_send_byte(0x14);  // charge pump on
    i2c_send_byte(0x20); i2c_send_byte(0x02);  // page addressing
    i2c_send_byte(0xC8);        // COM scan
    i2c_send_byte(0xDA); i2c_send_byte(0x12);  // COM pins
    i2c_send_byte(0xAF);        // display on
    i2c_stop();

    // Position: page 0, column 0
    i2c_start();
    i2c_send_byte(0x78);
    i2c_send_byte(0x00);
    i2c_send_byte(0xB0);
    i2c_send_byte(0x00);
    i2c_send_byte(0x10);
    i2c_stop();

    // Render "23°C"
    oled_glyph(2);
    oled_glyph(3);
    oled_glyph(11);
    oled_glyph(12);

    out(42);
    halt();
}
