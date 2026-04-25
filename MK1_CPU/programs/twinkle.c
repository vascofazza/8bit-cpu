/* Twinkle Twinkle — split into small phrases for overlay.
 * Each phrase ≤ 6 notes = 25 bytes (fits in overlay region).
 * C4=262 D4=294 E4=330 F4=349 G4=392 A4=440
 */

void p1(void) {
    /* Twinkle twinkle */
    tone(262, 250); tone(262, 250);
    tone(392, 250); tone(392, 250);
    tone(440, 250); tone(440, 250);
}

void p2(void) {
    /* little star */
    tone(392, 500);
    tone(349, 250); tone(349, 250);
    tone(330, 250); tone(330, 250);
}

void p3(void) {
    /* How I wonder */
    tone(294, 250); tone(294, 250);
    tone(262, 500);
}

void p4(void) {
    /* what you are */
    tone(392, 250); tone(392, 250);
    tone(349, 250); tone(349, 250);
    tone(330, 250); tone(330, 250);
}

void p5(void) {
    tone(294, 500);
}

void main(void) {
    i2c_init();
    delay_calibrate();
    ddra_imm(0x02);

    p1(); p2(); p3();
    p4(); p5();
    p4(); p5();
    p1(); p2(); p3();

    out(0xDD);
    halt();
}
