// I2C scan - matches known-good assembly as closely as possible

void i2c_bit(unsigned char b) {
    if (b) {
        exw(0x00, 2, 0);
        exw(0x40, 2, 0);
        exw(0x00, 2, 0);
    } else {
        exw(0x80, 2, 0);
        exw(0xC0, 2, 0);
        exw(0x80, 2, 0);
    }
}

void i2c_send_byte(unsigned char b) {
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80); b = b << 1;
    i2c_bit(b & 0x80);
}

void i2c_start() {
    exw(0x40, 2, 0);
    exw(0xC0, 2, 0);
    exw(0x80, 2, 0);
}

void i2c_stop() {
    exw(0x80, 2, 0);
    exw(0xC0, 2, 0);
    exw(0x40, 2, 0);
}

void main() {
    exw(0x90, 3, 0);

    // Inline recovery: 9 SCL clocks (no loop — loop overhead causes false ACKs)
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    exw(0x00, 2, 0); exw(0x40, 2, 0);
    i2c_stop();

    // Scan 8-127
    unsigned char addr;
    for (addr = 8; addr < 128; addr++) {
        i2c_start();
        i2c_send_byte(addr << 1);

        // ACK check — match known-good: NOPs before SCL_H only, read immediately after
        exw(0x00, 2, 0);
        nop(5);
        exw(0x40, 2, 0);
        unsigned char val = exr_port_a();
        exw(0x00, 2, 0);

        i2c_stop();

        if ((val & 0x01) == 0) {
            out(addr);
            halt();
        }
    }

    out(0);
    halt();
}
