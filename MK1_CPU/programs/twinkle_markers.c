// Twinkle Twinkle Little Star — overlay system with heartbeat markers
// On auto clock: cnt tracks progress (can't read values, only count).
// Full run = cnt 8. If cnt < 8 on reset, page3 corruption likely.
void phrase1() {
  tone(262, 400); silence(100);
  tone(262, 400); silence(100);
  tone(392, 400); silence(100);
  tone(392, 400); silence(100);
}

void phrase2() {
  tone(440, 400); silence(100);
  tone(440, 400); silence(100);
  tone(392, 800); silence(200);
}

void phrase3() {
  tone(349, 400); silence(100);
  tone(349, 400); silence(100);
  tone(330, 400); silence(100);
  tone(330, 400); silence(100);
}

void phrase4() {
  tone(294, 400); silence(100);
  tone(294, 400); silence(100);
  tone(262, 800); silence(200);
}

void main() {
  i2c_init();
  delay_calibrate();
  out(1);       // cnt=1: init done
  phrase1();
  out(2);       // cnt=2
  phrase2();
  out(3);       // cnt=3
  phrase3();
  out(4);       // cnt=4
  phrase4();
  out(5);       // cnt=5
  phrase1();
  out(6);       // cnt=6
  phrase2();
  out(7);       // cnt=7
  halt();       // cnt=7 = full completion
}
