#define MI 8
#define HL 9
#define RI 10
#define EN 11
#define CLK 12
#define RST 13
#define CU_EN A5

#define NEXT A4

#define DELAY 2000

byte current_bank = 0;

void setup() {
  // put your setup code here, to run once:
  pinMode(MI, OUTPUT);
  pinMode(HL, OUTPUT);
  pinMode(RI, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(CLK, INPUT);
  pinMode(RST, INPUT);
  pinMode(CU_EN, OUTPUT);
  pinMode(NEXT, INPUT_PULLUP);

  DDRD |= B11111111;
  DDRC |= B00001111;
}

void reset()
{
  pinMode(RST, OUTPUT);
  digitalWrite(RST, HIGH);
  delayMicroseconds(10);
  digitalWrite(RST, LOW);
  pinMode(RST, INPUT);
}

void clock()
{
  pinMode(CLK, OUTPUT);
  digitalWrite(CLK, HIGH);
  delayMicroseconds(1);
  digitalWrite(CLK, LOW);
  pinMode(CLK, INPUT);
}

void enableClock()
{
  pinMode(CLK, OUTPUT);
  digitalWrite(CLK, HIGH);
}

void disableClock()
{
  pinMode(CLK, OUTPUT);
  digitalWrite(CLK, LOW);
  pinMode(CLK, INPUT);
}

void disable_cu()
{
  digitalWrite(CU_EN, HIGH);
}

void enable_cu()
{
  digitalWrite(CU_EN, LOW);
}

void enableOutput()
{
  digitalWrite(EN, HIGH);
}

void disableOutput()
{
  digitalWrite(EN, LOW);
}

void set_bank(byte bank)
{
  PORTC = bank + (PORTC & 0xF0);
}

void set_address(unsigned int address)
{
  digitalWrite(HL, address > 0xFF);
  set_bank(0);
  delayMicroseconds(1);
  put_out(address % 256);
  delayMicroseconds(1);
  enableOutput();
  digitalWrite(MI, HIGH);
  delayMicroseconds(1);
  digitalWrite(MI, LOW);
  delayMicroseconds(1);
  disableOutput();
  set_bank(current_bank);
}

void put_out(byte data)
{
  PORTD = data;
}

void write_instruction(byte instr)
{
  put_out(instr % 256);
  enableOutput();
  delayMicroseconds(1);
  digitalWrite(RI, HIGH);
  delayMicroseconds(1);
  digitalWrite(RI, LOW);
  delayMicroseconds(1);
  disableOutput();

}

void handle_button()
{
  while (true)
  {
    if (!digitalRead(NEXT))
    {
      if (++current_bank > 15)
        current_bank = 1;
      set_bank(current_bank);
      delay(250);
      auto curr_time = millis();
      bool next = false;
      while (millis() - curr_time < DELAY)
      {
        if (!digitalRead(NEXT))
        {
          next = true;
          break;
        }
      }
      if (next)
        continue;
      break;
    }
  }
}

void loop() {

  handle_button();

  reset();
  disable_cu();

  delayMicroseconds(1);
  enableClock();
  delayMicroseconds(1);
  for (int i = 0; i < 512; i ++)
  {
    set_address(i);
    delayMicroseconds(1);
    write_instruction(i);
    delayMicroseconds(1);
  }

  disableClock();
  digitalWrite(HL, LOW);
  reset();
  enable_cu();
  disableOutput();

}
