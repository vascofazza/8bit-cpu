/* Write overlay 1 to EEPROM at 0x0110: D1 BB 6C (out_imm 0xBB; ret) */
void main(void) {
    i2c_init();
    eeprom_write_byte(0x0110, 0xD1);
    eeprom_write_byte(0x0111, 0xBB);
    eeprom_write_byte(0x0112, 0x6C);
    out(0xDD);
    halt();
}
