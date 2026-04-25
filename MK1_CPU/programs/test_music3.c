void play() {
    tone(523, 300);
    tone(659, 300);
    tone(784, 600);
}

void main() {
    i2c_init();
    delay_calibrate();
    play();
    out(42);
    halt();
}
