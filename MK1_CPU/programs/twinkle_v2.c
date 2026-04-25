// Twinkle Twinkle Little Star — overlay architecture demo
// Compiles with: python3 mk1cc2.py twinkle_v2.c --eeprom -O -o twinkle_v2.asm
//
// Uses the multi-page overlay system:
//   - Init overlay: delay_cal + I2C helpers (runs once)
//   - Tone library overlay: play_note + tone_setup + tone + delay_Nms
//   - User overlay: phrase functions (call tone library via nesting)

void phrase1() {
  tone(262, 400); silence(100);  // C4
  tone(262, 400); silence(100);  // C4
  tone(392, 400); silence(100);  // G4
  tone(392, 400); silence(100);  // G4
}

void phrase2() {
  tone(440, 400); silence(100);  // A4
  tone(440, 400); silence(100);  // A4
  tone(392, 800); silence(200);  // G4 (long)
}

void phrase3() {
  tone(349, 400); silence(100);  // F4
  tone(349, 400); silence(100);  // F4
  tone(330, 400); silence(100);  // E4
  tone(330, 400); silence(100);  // E4
}

void phrase4() {
  tone(294, 400); silence(100);  // D4
  tone(294, 400); silence(100);  // D4
  tone(262, 800); silence(200);  // C4 (long)
}

void main() {
  i2c_init();
  delay_calibrate();

  // Verse 1: Twinkle twinkle little star
  phrase1();
  phrase2();

  // Verse 2: How I wonder what you are
  phrase3();
  phrase4();

  // Repeat verse 1
  phrase1();
  phrase2();

  halt();
}
