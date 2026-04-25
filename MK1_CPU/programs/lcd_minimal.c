// Turn backlight OFF to prove C-compiled I2C works

void main() {
    exw(0x90, 3, 0);

    unsigned char k;
    for (k = 0; k < 5; k++) {
        exw(0x00, 2, 0);
        exw(0x40, 2, 0);
    }
    exw(0x80, 2, 0);
    exw(0xC0, 2, 0);
    exw(0x40, 2, 0);

    // I2C write 0x00 to 0x27 (backlight off)
    exw(0x40, 2, 0);
    exw(0xC0, 2, 0);
    exw(0x80, 2, 0);

    unsigned char b = 0x4E;
    unsigned char i;
    for (i = 0; i < 8; i++) {
        if (b & 0x80) {
            exw(0x00, 2, 0);
            exw(0x40, 2, 0);
            exw(0x00, 2, 0);
        } else {
            exw(0x80, 2, 0);
            exw(0xC0, 2, 0);
            exw(0x80, 2, 0);
        }
        b = b << 1;
    }
    exw(0x00, 2, 0);
    exw(0x40, 2, 0);
    exw(0x00, 2, 0);

    b = 0x00;
    for (i = 0; i < 8; i++) {
        if (b & 0x80) {
            exw(0x00, 2, 0);
            exw(0x40, 2, 0);
            exw(0x00, 2, 0);
        } else {
            exw(0x80, 2, 0);
            exw(0xC0, 2, 0);
            exw(0x80, 2, 0);
        }
        b = b << 1;
    }
    exw(0x00, 2, 0);
    exw(0x40, 2, 0);
    exw(0x00, 2, 0);

    exw(0x80, 2, 0);
    exw(0xC0, 2, 0);
    exw(0x40, 2, 0);

    halt();
}
