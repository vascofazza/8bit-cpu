/* EEPROM-backed overlay tier test.
 * 6 computation functions + 200B globals → forces EEPROM tier.
 * ESP32 page3 patching: overlay data written to page3 after init self-copy.
 * Tests: page3 + page1 + page2 + EEPROM tiers.
 */
unsigned char buf[200];
void process0(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 0;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 3;
        prev = acc;
        buf[j] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void process1(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 7;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 4;
        prev = acc;
        buf[j + 10] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void process2(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 14;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 5;
        prev = acc;
        buf[j + 20] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void process3(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 21;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 6;
        prev = acc;
        buf[j + 30] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void process4(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 28;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 7;
        prev = acc;
        buf[j + 40] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void process5(unsigned char n) {
    unsigned char j; j = 0; unsigned char acc; acc = 35;
    unsigned char prev; prev = 1;
    while (j < n) {
        acc = acc + prev + 8;
        prev = acc;
        buf[j + 50] = acc;
        out(acc);
        j = j + 1;
    }
    out(acc + prev);
}
void main() {
    i2c_init();
    process0(4);
    process1(4);
    process2(4);
    process3(4);
    process4(4);
    process5(4);
    halt();
}
