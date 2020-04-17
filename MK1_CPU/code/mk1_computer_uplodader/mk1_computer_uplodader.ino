#define MI 10
#define HL 11
#define RI 12
#define EN 13
#define CLK A0
#define RST A1
#define CU_EN A2

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  //Serial.setTimeout(5000);
  pinMode(MI, OUTPUT);
  pinMode(HL, OUTPUT);
  pinMode(RI, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(CLK, INPUT);
  pinMode(RST, INPUT);
  pinMode(CU_EN, OUTPUT);

  DDRD &= ~B11111100;
  DDRB &= ~B00000011;
}

void reset()
{
  pinMode(RST, OUTPUT);
  digitalWrite(RST, HIGH);
  delay(10);
  digitalWrite(RST, LOW);
  pinMode(RST, INPUT);
}

void clock()
{
  pinMode(CLK, OUTPUT);
  digitalWrite(CLK, HIGH);
  delay(1);
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

void setAddress(byte address)
{
  putOut(address);
  delay(1);
  enableOutput();
  digitalWrite(MI, HIGH);
  delay(1);
  digitalWrite(MI, LOW);
  delay(1);
  disableOutput();
}

void putOut(byte data)
{
  PORTD = (PORTD & 0x3) | (data << 2);
  PORTB = (PORTB & 0xFC) | (data >> 6 & 0x3);
  delay(1);
}

void writeInstruction(byte instr, byte data)
{
  digitalWrite(HL, LOW);
  putOut(instr);
  enableOutput();
  digitalWrite(RI, HIGH);
  delay(1);
  digitalWrite(RI, LOW);
  delay(1);
  digitalWrite(HL, HIGH);
  putOut(data);
  digitalWrite(RI, HIGH);
  delay(1);
  digitalWrite(RI, LOW);
  delay(1);
  digitalWrite(HL, LOW);
  disableOutput();
  
}

byte buffer[512];

void loop() {
  if (Serial.available()) {

    int p_size = Serial.readBytes(buffer, sizeof(buffer));
    Serial.write(0);

    reset();
    disable_cu();
    for (int i = 0; i < 5; i++)
      clock();

    delay(1);
    enableClock();
    delay(1);
    for (int i = 0; i < p_size; i += 2)
    {
      setAddress(i / 2);
      delay(1);
      writeInstruction(buffer[i], buffer[i + 1]);
      delay(1);
    }

    disableClock();
    reset();
    enable_cu();
  }
  disableOutput();

}
