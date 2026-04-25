/* EEPROM overlay demo — functions that call each other.
 * compute_chain calls multiply, add_offset, double_it.
 * The compiler should group them into ONE overlay slot.
 *
 * Computes: ((input * 3) + 10) * 2 where input = peek3(0)
 */

unsigned char multiply(unsigned char a, unsigned char b) {
    unsigned char result = 0;
    while (b > 0) {
        result = result + a;
        b = b - 1;
    }
    return result;
}

unsigned char add_offset(unsigned char x, unsigned char offset) {
    return x + offset;
}

unsigned char double_it(unsigned char x) {
    return x + x;
}

unsigned char compute_chain(unsigned char input) {
    unsigned char step1 = multiply(input, 3);
    unsigned char step2 = add_offset(step1, 10);
    unsigned char step3 = double_it(step2);
    return step3;
}

void main(void) {
    i2c_init();
    unsigned char input = peek3(0);
    unsigned char result = compute_chain(input);
    out(result);
    halt();
}
