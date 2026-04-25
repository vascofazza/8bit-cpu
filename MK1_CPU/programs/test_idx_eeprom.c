/* Simplest possible hardware verification.
 * fn0 (overlay) writes 0x5C to EEPROM[0x0020].
 * main reads it back and outputs. If IDX dispatch works AND EEPROM path
 * works, we see 0x5C followed by the end sentinel.
 * End sentinel: [0xFE, 0xED, 0xBE, 0xEF]. */
unsigned char buf[200];

void fn0(void) { eeprom_write_byte(0x0020, 0x5C); }

void main(void) {
    i2c_init();
    fn0();
    out(eeprom_read_byte(0x0020));   /* expected 0x5C */
    out(0xFE); out(0xED); out(0xBE); out(0xEF);   /* end sentinel */
    halt();
}
