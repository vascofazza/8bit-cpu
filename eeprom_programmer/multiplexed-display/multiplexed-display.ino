#define SHIFT_DATA 2
#define SHIFT_CLK 3
#define SHIFT_LATCH 4
#define EEPROM_D0 5
#define EEPROM_D7 12
#define WRITE_EN 13
#define READ_LED A1
#define WRITE_LED A0

/*
   Output the address bits and outputEnable signal using shift registers.
*/
void setAddress(int address, bool outputEnable) {
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, (address >> 8) | (outputEnable ? 0x00 : 0x80));
  shiftOut(SHIFT_DATA, SHIFT_CLK, MSBFIRST, address);

  digitalWrite(SHIFT_LATCH, LOW);
  digitalWrite(SHIFT_LATCH, HIGH);
  digitalWrite(SHIFT_LATCH, LOW);
}


/*
   Read a byte from the EEPROM at the specified address.
*/
byte readEEPROM(int address) {
  digitalWrite(READ_LED, HIGH);
  for (int pin = EEPROM_D0; pin <= EEPROM_D7; pin += 1) {
    pinMode(pin, INPUT);
  }
  setAddress(address, /*outputEnable*/ true);

  byte data = 0;
  for (int pin = EEPROM_D7; pin >= EEPROM_D0; pin -= 1) {
    data = (data << 1) + digitalRead(pin);
  }
  digitalWrite(READ_LED, LOW);
  return data;
}


/*
   Write a byte to the EEPROM at the specified address.
*/
void writeEEPROM(int address, byte data) {
  digitalWrite(WRITE_LED, HIGH);
  setAddress(address, /*outputEnable*/ false);
  for (int pin = EEPROM_D0; pin <= EEPROM_D7; pin += 1) {
    pinMode(pin, OUTPUT);
  }

  for (int pin = EEPROM_D0; pin <= EEPROM_D7; pin += 1) {
    digitalWrite(pin, data & 1);
    data = data >> 1;
  }
  digitalWrite(WRITE_EN, LOW);
  delayMicroseconds(1);
  digitalWrite(WRITE_EN, HIGH);
  delay(10);
  digitalWrite(WRITE_LED, LOW);
}


/*
   Read the contents of the EEPROM and print them to the serial monitor.
*/
void printContents() {
  for (int base = 0; base <= 255; base += 16) {
    byte data[16];
    for (int offset = 0; offset <= 15; offset += 1) {
      data[offset] = readEEPROM(base + offset);
    }

    char buf[80];
    sprintf(buf, "%03x:  %02x %02x %02x %02x %02x %02x %02x %02x   %02x %02x %02x %02x %02x %02x %02x %02x",
            base, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
            data[8], data[9], data[10], data[11], data[12], data[13], data[14], data[15]);

    Serial.println(buf);
  }
}


void setup() {
  // put your setup code here, to run once:
  pinMode(SHIFT_DATA, OUTPUT);
  pinMode(SHIFT_CLK, OUTPUT);
  pinMode(SHIFT_LATCH, OUTPUT);
  digitalWrite(WRITE_EN, HIGH);
  pinMode(WRITE_EN, OUTPUT);
  Serial.begin(57600);


  // Bit patterns for the digits 0..F
  byte digits[] = { 0x7e, 0x30, 0x6d, 0x79, 0x33, 0x5b, 0x5f, 0x70, 0x7f, 0x7b, 0x77, 0x1f, 0x4e, 0x3d, 0x4f, 0x47 };
  byte lower[] = {0x7D, 0x1F, 0x0D, 0x3D, 0x6f, 0x47, 0x7B, 0x17, 0x10, 0x38, 0x17, 0x06, 0x55, 0x15, 0x1D, 0x67, 0x73, 0x05, 0x5B, 0x0F, 0x1C, 0x23, 0x2B, 0x25, 0x33, 0x6D };
  byte upper[] = {0x77, 0x7F, 0x4E, 0x7E, 0x4F, 0x47, 0x5E, 0x37, 0x30, 0x3C, 0x37, 0x0E, 0x55, 0x15, 0x7E, 0x67, 0x73, 0x77, 0x5B, 0x46, 0x3E, 0x27, 0x3F, 0x25, 0x3B, 0x6D };
  byte space = 0x00;

  Serial.println("Programming ones place");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value, digits[value % 10]);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value) != digits[value % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming tens place");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 256, digits[(value / 10) % 10]);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 256) != digits[(value / 10) % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming hundreds place");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 512, digits[(value / 100) % 10]);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 512) != digits[(value / 100) % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming sign");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 768, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 768) != 0)
      Serial.println("Write Error!");
  }

  Serial.println("Programming ones place (twos complement)");
  for (int value = -128; value <= 127; value += 1) {
    writeEEPROM((byte)value + 1024, digits[abs(value) % 10]);
  }
  for (int value = -128; value <= 127; value += 1) {
    if (readEEPROM((byte)value + 1024) != digits[abs(value) % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming tens place (twos complement)");
  for (int value = -128; value <= 127; value += 1) {
    writeEEPROM((byte)value + 1280, digits[abs(value / 10) % 10]);
  }
  for (int value = -128; value <= 127; value += 1) {
    if (readEEPROM((byte)value + 1280) != digits[abs(value / 10) % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming hundreds place (twos complement)");
  for (int value = -128; value <= 127; value += 1) {
    writeEEPROM((byte)value + 1536, digits[abs(value / 100) % 10]);
  }
  for (int value = -128; value <= 127; value += 1) {
    if (readEEPROM((byte)value + 1536) != digits[abs(value / 100) % 10])
      Serial.println("Write Error!");
  }

  Serial.println("Programming sign (twos complement)");
  for (int value = -128; value <= 127; value += 1) {
    if (value < 0) {
      writeEEPROM((byte)value + 1792, 0x01);
    } else {
      writeEEPROM((byte)value + 1792, 0);
    }
  }

  Serial.println("Programming ones place (HEX)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 2048, digits[value % 16]);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 2048) != digits[value % 16])
      Serial.println("Write Error!");
  }

  Serial.println("Programming tens place (HEX)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 2048 + 256, digits[(value / 16) % 16]);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 2048 + 256) != digits[(value / 16) % 16])
      Serial.println("Write Error!");
  }

  Serial.println("Programming hundreds place (HEX)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 2048 + 512, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 2048 + 512) != 0)
      Serial.println("Write Error!");
  }

  Serial.println("Programming sign (HEX)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 2048 + 768, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 2048 + 768) != 0)
      Serial.println("Write Error!");
  }



  Serial.println("Programming ones place (ASCII)");
  for (int value = 0; value <= 255; value += 1) {
    byte pattern = 0;
    if (value >= '0' && value <= '9')
    {
      pattern = digits[value - '0'];
    }
    else if (value >= 'A' && value <= 'Z')
    {
      pattern = upper[value - 'A'];
    }
    else if (value >= 'a' && value <= 'z')
    {
      pattern = lower[value - 'a'];
    }
    else if (value == ' ')
    {
      pattern = space;
    }
    writeEEPROM(value + 4096, pattern);
  }
  for (int value = 0; value <= 255; value += 1) {
    byte pattern = 0;
    if (value >= '0' && value <= '9')
    {
      pattern = digits[value - '0'];
    }
    else if (value >= 'A' && value <= 'Z')
    {
      pattern = upper[value - 'A'];
    }
    else if (value >= 'a' && value <= 'z')
    {
      pattern = lower[value - 'a'];
    }
    else if (value == ' ')
    {
      pattern = space;
    }
    if (readEEPROM(value + 4096) != pattern)
      Serial.println("Write Error!");
  }

  Serial.println("Programming tens place (ASCII)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 4096 + 256, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 4096 + 256) != 0)
      Serial.println("Write Error!");
  }

  Serial.println("Programming hundreds place (ASCII)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 4096 + 512, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 4096 + 512) != 0)
      Serial.println("Write Error!");
  }

  Serial.println("Programming sign (ASCII)");
  for (int value = 0; value <= 255; value += 1) {
    writeEEPROM(value + 4096 + 768, 0);
  }
  for (int value = 0; value <= 255; value += 1) {
    if (readEEPROM(value + 4096 + 768) != 0)
      Serial.println("Write Error!");
  }

  // Read and print out the contents of the EERPROM
  Serial.println("Done.");
}



void loop() {
  // put your main code here, to run repeatedly:

}
