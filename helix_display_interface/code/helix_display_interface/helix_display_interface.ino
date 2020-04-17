#include <EnableInterrupt.h>
#include <LiquidCrystal.h>
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

#define CLK PB7
#define CLR PB6
#define SIG1 13
#define SIG0 10
#define EN 9
#define IRQ 8

volatile boolean data_available = false;
volatile byte data = 0;
volatile byte mode = 0;
volatile int written_bytes = 0;
char buf[256];

void setup() {
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.clear();

  Serial.begin(9600);

  //pinMode(CLR, INPUT);
  //pinMode(CLK, INPUT);
  pinMode(SIG0, INPUT);
  pinMode(SIG1, INPUT);
  pinMode(EN, INPUT);
  pinMode(IRQ, OUTPUT);

  DDRC &= ~B00111111;
  DDRD &= ~B11000000;
  DDRB &= ~B01000000;

  enableInterrupt(EN, interruptFunction, CHANGE);

  delay(500);

  lcd.print(" Helix  Display");
  delay(1000);
  lcd.clear();
}

void interruptFunction()
{
  if (digitalRead(EN))
  {
    data_available = true;
    mode = digitalRead(SIG0) + (digitalRead(SIG1) << 1);
  }
}

byte read_bus()
{
  byte b = 0;
  b |= (PINC & 0x3F);
  b |= (PIND & 0xC0);
  return b;
}

void adjust_display()
{
  if (written_bytes == 16)
  {
    lcd.setCursor(0, 1);
  }
  if (written_bytes == 32)
  {
    lcd.autoscroll();
  }
}

void loop() {
  if (data_available)
  {
    delayMicroseconds(1);
    data = read_bus();
    //INTEGER
    if (mode == 1)
    {
      itoa(data, buf, 10);
      //Serial.print(int(data));

      for (int i = 0; i < 3; i++)
      {
        if (buf[i] == 0)
          break;
        lcd.print(buf[i]);
        written_bytes++;
        adjust_display();
      }
    }
    //CHAR
    else if (mode == 2)
    {
      lcd.print((char)data);
      Serial.print((char)data);
      written_bytes++;
      adjust_display();
    }
    else
    {
      lcd.clear();
      lcd.noAutoscroll();
      lcd.setCursor(0, 0);
      written_bytes = 0;
    }
    data_available = false;
    delay(10);
  }
  else if (PINB & B01000000)
  {
    lcd.noAutoscroll();
    lcd.home();
    lcd.clear();
    written_bytes = 0;
    Serial.println();
  }
}
