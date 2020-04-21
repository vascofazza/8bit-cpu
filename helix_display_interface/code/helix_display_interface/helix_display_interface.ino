#include <LiquidCrystal.h>
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

#define CLK PB7
#define CLR PB6
#define SIG1 13
#define SIG0 10
#define EN 9
#define IRQ 8

#define read_clock PINB & 0x80
#define read_mode ((PINB & 0x4) >> 2) + ((PINB & 0x20) >> 4)
#define read_bus (PINC & 0x3F) | (PIND & 0xC0)
#define disable_signal PORTB &= 0xfe
#define enable_signal PORTB |= 0x1
#define read_enable PINB & 2
#define read_clear PINB & B01000000

volatile boolean data_available = false;
volatile byte data = 0;
volatile byte mode = 0;
int written_bytes = 0;
char buf[4];
char line1[17];
char line2[17];
int cursor = 0;
int curr_line = 0;

void setup() {
  lcd.begin(16, 2);
  lcd.setCursor(0, 0);
  lcd.clear();

  Serial.begin(9600);

  pinMode(SIG0, INPUT);
  pinMode(SIG1, INPUT);
  pinMode(EN, INPUT);
  pinMode(IRQ, OUTPUT);

  set_bus_input();
  DDRB &= ~B11000000;

  lcd.print(" Helix  Display");
  delay(1000);
  lcd.clear();
  lcd.blink();
  enable_signal;
}

void set_bus_input()
{
  DDRC &= ~B00111111;
  DDRD &= ~B11000000;
}

void set_bus_output()
{
  DDRC |= B00111111;
  DDRD |= B11000000;
}
void write_bus(byte data)
{
  PORTC = (PORTC & 0xC0) | (data & 0x3f);
  PORTD = (PORTD & 0x3F) | (data & 0xC0);
}
void scroll_line()
{
  if (curr_line == 0)
  {
    curr_line = 1;
    lcd.setCursor(0, 1);
  }
  else
  {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(line2);
    strcpy(line1, line2);
    lcd.setCursor(0, 1);
    curr_line = 1;
  }
}

void update_display(char data[])
{
  int count = 0;
  char* line = curr_line == 0 ? line1 : line2;
  while (data[++count] != 0);
  if (cursor + count > 16 || (mode == 2 && data[0] == '\n')) {
    scroll_line();
    cursor = 0;
    line = line2;
  }
  if (mode == 2 && buf[0] == '\n')
    return;
  strcpy(line + cursor, data);
  cursor += count;
  lcd.print(buf);
  written_bytes++;
}

void loop() {
  mode = read_mode;
  data = read_bus;
  if (read_enable)
  {
    disable_signal;
    data_available = mode > 0;
  }

  if (data_available)
  {
    //INTEGER
    if (mode == 1)
    {
      itoa(data, buf, 10);
      update_display(buf);
    }
    //CHAR
    else if (mode == 2)
    {
      buf[0] = data;
      buf[1] = 0;
      update_display(buf);
      Serial.print((char)data);
    }
    else if (mode == 3)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      written_bytes = 0;
      cursor = 0;
    }
    data_available = false;
    delay(25);
    enable_signal;
  }
  else if (read_clear)
  {
    lcd.home();
    lcd.clear();
    written_bytes = 0;
    Serial.println();
    cursor = 0;
    enable_signal;
  }
}
