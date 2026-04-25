/* Piezo melody test - C major arpeggio, note table approach */
void main(void) {
    i2c_init();
    delay_calibrate();
    ddra_imm(0x02);

    tone(523, 200);
    tone(659, 200);
    tone(784, 200);
    tone(1047, 300);

    out(0xDD);
    halt();
}
