/* MK1 C Example — compiled with vbcc */

/* Inline assembly for hardware I/O */
void out(void) = "\tout\n";
void halt(void) = "\thlt\n";

/* Find the larger of two values */
unsigned char max(unsigned char a, unsigned char b) {
    if (a >= b) return a;
    return b;
}

/* Count how many values in a sequence are above a threshold */
unsigned char count_above(unsigned char threshold,
                          unsigned char a, unsigned char b,
                          unsigned char c, unsigned char d) {
    unsigned char n;
    n = 0;
    if (a > threshold) n = n + 1;
    if (b > threshold) n = n + 1;
    if (c > threshold) n = n + 1;
    if (d > threshold) n = n + 1;
    return n;
}

void main() {
    unsigned char result;

    /* max(10, 25) → displays 25 */
    result = max(10, 25);
    out();

    /* max(200, 150) → displays 200 */
    result = max(200, 150);
    out();

    /* count values above 50 in {20, 75, 100, 30} → displays 2 */
    result = count_above(50, 20, 75, 100, 30);
    out();

    halt();
}
