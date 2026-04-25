// EEPROM end-to-end test: store a lookup table, sum all entries
// Expected output: 150 (10+20+30+40+50)

eeprom unsigned char table[] = { 10, 20, 30, 40, 50 };

void main() {
    i2c_init();
    unsigned char sum;
    unsigned char i;
    sum = 0;
    i = 0;
    while (i < 5) {
        sum = sum + table[i];
        i = i + 1;
    }
    out(sum);
    halt();
}
