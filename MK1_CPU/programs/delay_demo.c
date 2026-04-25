void main(void) {
    i2c_init();
    delay_calibrate();
    delay(10);
    out(10);
    delay(100);
    out(100);
    halt();
}
