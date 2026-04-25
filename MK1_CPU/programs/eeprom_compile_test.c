void main() {
  i2c_init();
  delay_calibrate();
  // Write 0x42 to EEPROM address 0x0000
  eeprom_write(0x00, 0x00, 0x42);
  delay(100);  // wait for write cycle
  // Read it back
  u8 val = eeprom_read(0x00, 0x00);
  out(val);
  halt();
}
