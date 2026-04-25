unsigned char count_up() {
    unsigned char sec;
    sec = 0;
    while (sec < 30) {
        out(sec);
        delay(1000);
        sec = sec + 1;
    }
    return sec;
}

void main() {
    i2c_init();
    delay_calibrate();
    count_up();
    halt();
}
