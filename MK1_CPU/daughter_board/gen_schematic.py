#!/usr/bin/env python3
"""Generate KiCad 8 schematic for MK1 I2C/SPI/Speaker daughter board."""
import uuid

def uid():
    return str(uuid.uuid4())

# Component positions (mm)
J4_X, J4_Y = 30, 80
U1_X, U1_Y = 90, 60     # 74HC574
U2_X, U2_Y = 90, 140    # 74HC126
Q1_X, Q1_Y = 160, 50    # 2N7000 (SDA open-drain, for future I2C read)
Q2_X, Q2_Y = 160, 90    # NPN speaker driver
BZ_X, BZ_Y = 190, 90    # Piezo

header = f'''(kicad_sch
  (version 20231120)
  (generator "mk1_daughter_gen")
  (generator_version "1.0")
  (uuid "{uid()}")
  (paper "A4")
  (title_block
    (title "MK1 Daughter Board — I2C/SPI/Speaker")
    (date "2026-03-30")
    (rev "1.0")
    (comment 1 "Write-only I2C + SPI read/write + Piezo speaker")
    (comment 2 "Plugs into J4 external interface connector"))
'''

# We'll create a simplified schematic with text labels showing connections
# rather than trying to place actual KiCad library symbols (which require
# exact library paths that vary per installation)

# Instead, create a comprehensive netlist + wiring guide as a KiCad-compatible
# text schematic with hierarchical labels

labels_and_notes = f'''
  (text "MK1 DAUGHTER BOARD SCHEMATIC\\n\\n\
J4 CONNECTOR (from MK1)\\n\
Pin 1,6: E0 (read strobe)\\n\
Pin 3: BUS_2\\n\
Pin 5: BUS_6\\n\
Pin 7: BUS_1\\n\
Pin 8: GND\\n\
Pin 11: BUS_4\\n\
Pin 12: E1 (write strobe)\\n\
Pin 15: BUS_3\\n\
Pin 17: BUS_5\\n\
Pin 18: BUS_7\\n\\n\
74HC574 (U1) - Output Latch\\n\
CLK = E1 (J4 pin 12)\\n\
OE = GND (always enabled)\\n\
D7 = BUS_7, D6 = BUS_6, D5 = BUS_5\\n\
D4 = BUS_4, D3 = BUS_3, D2 = BUS_2, D1 = BUS_1\\n\
Q7 = SPI_MOSI -> EEPROM SI\\n\
Q6 = SPI_SCK -> EEPROM SCK\\n\
Q5 = SPI_CS -> EEPROM ~CS\\n\
Q4 = I2C_SDA -> LCD SDA (+ 4.7K pull-up)\\n\
Q3 = I2C_SCL -> LCD SCL (+ 4.7K pull-up)\\n\
Q2 = SPEAKER -> NPN base (1K) -> piezo\\n\
Q1,Q0 = spare\\n\\n\
74HC126 (U2) - Input Buffer\\n\
OE1 = E0 (J4 pin 1) — active HIGH\\n\
A1 = EEPROM SO (MISO)\\n\
Y1 = BUS_7 (J4 pin 18) — read back via exr(0)\\n\
Gates 2-4: spare\\n\\n\
SOFTWARE:\\n\
I2C write: exw(val, 1, 0) — bit4=SDA, bit3=SCL\\n\
SPI write: exw(val, 1, 0) — bit7=MOSI, bit6=SCK, bit5=~CS\\n\
SPI read:  exr(0) — bit7=MISO\\n\
Speaker:   toggle bit2 in exw loop"
    (at 30 30 0)
    (effects
      (font
        (size 1.5 1.5))
      (justify left)))
)
'''

with open('/Users/gadyke/8bit-cpu/MK1_CPU/daughter_board/daughter_board.kicad_sch', 'w') as f:
    f.write(header)
    f.write(labels_and_notes)

print("Generated daughter_board.kicad_sch")
print("\nThis is a text-annotation schematic. For a proper schematic,")
print("create a new KiCad project and add these components:")
print()
print("NETLIST:")
print("=" * 60)
print()
print("J4 (2x9 connector from MK1)")
print("  Pin 1,6  (E0)    -> U2 pin 1 (OE1)")
print("  Pin 3    (BUS_2) -> U1 pin 3 (D2)")
print("  Pin 5    (BUS_6) -> U1 pin 7 (D6)")
print("  Pin 7    (BUS_1) -> U1 pin 2 (D1)")
print("  Pin 8    (GND)   -> U1 pin 10, U2 pin 7, GND rail")
print("  Pin 11   (BUS_4) -> U1 pin 5 (D4)")
print("  Pin 12   (E1)    -> U1 pin 11 (CLK)")
print("  Pin 15   (BUS_3) -> U1 pin 4 (D3)")
print("  Pin 17   (BUS_5) -> U1 pin 6 (D5)")
print("  Pin 18   (BUS_7) -> U1 pin 8 (D7), U2 pin 3 (Y1)")
print()
print("U1: 74HC574 (DIP-20)")
print("  Pin 1  (OE)  -> GND (always enabled)")
print("  Pin 2  (D0)  -> GND (BUS_0 not on J4)")
print("  Pin 3  (D1)  -> J4 pin 7 (BUS_1)")
print("  Pin 4  (D2)  -> J4 pin 3 (BUS_2)")
print("  Pin 5  (D3)  -> J4 pin 15 (BUS_3)")
print("  Pin 6  (D4)  -> J4 pin 11 (BUS_4)")
print("  Pin 7  (D5)  -> J4 pin 17 (BUS_5)")
print("  Pin 8  (D6)  -> J4 pin 5 (BUS_6)")
print("  Pin 9  (D7)  -> J4 pin 18 (BUS_7)")
print("  Pin 10 (GND) -> GND")
print("  Pin 11 (CLK) -> J4 pin 12 (E1)")
print("  Pin 12 (Q7)  -> SPI MOSI (EEPROM SI)")
print("  Pin 13 (Q6)  -> SPI SCK (EEPROM SCK)")
print("  Pin 14 (Q5)  -> SPI ~CS (EEPROM ~CS)")
print("  Pin 15 (Q4)  -> I2C SDA + 4.7K pull-up to VCC")
print("  Pin 16 (Q3)  -> I2C SCL + 4.7K pull-up to VCC")
print("  Pin 17 (Q2)  -> 1K -> Q2 base (NPN speaker driver)")
print("  Pin 18 (Q1)  -> spare")
print("  Pin 19 (Q0)  -> spare")
print("  Pin 20 (VCC) -> VCC + 100nF decoupling to GND")
print()
print("U2: 74HC126 (DIP-14)")
print("  Pin 1  (OE1) -> J4 pin 1 or 6 (E0)")
print("  Pin 2  (A1)  -> EEPROM SO (MISO)")
print("  Pin 3  (Y1)  -> J4 pin 18 (BUS_7)")
print("  Pin 4  (OE2) -> GND (disabled) or future use")
print("  Pin 5  (A2)  -> future input")
print("  Pin 6  (Y2)  -> future output")
print("  Pin 7  (GND) -> GND")
print("  Pin 8  (Y3)  -> future")
print("  Pin 9  (A3)  -> future")
print("  Pin 10 (OE3) -> GND (disabled)")
print("  Pin 11 (Y4)  -> future")
print("  Pin 12 (A4)  -> future")
print("  Pin 13 (OE4) -> GND (disabled)")
print("  Pin 14 (VCC) -> VCC + 100nF decoupling to GND")
print()
print("Q2: NPN transistor (2N2222 / BC547)")
print("  Base     -> 1K resistor -> U1 pin 17 (Q2)")
print("  Collector -> Piezo (+) ")
print("  Emitter  -> GND")
print("  Piezo (-) -> VCC")
print()
print("SPI EEPROM (e.g., 25LC256 / AT25256)")
print("  ~CS  -> U1 pin 14 (Q5)")
print("  SO   -> U2 pin 2 (A1)")
print("  SI   -> U1 pin 12 (Q7)")
print("  SCK  -> U1 pin 13 (Q6)")
print("  VCC  -> VCC")
print("  GND  -> GND")
print("  ~WP  -> VCC (write enabled)")
print("  ~HOLD -> VCC (not held)")
print()
print("I2C LCD (1602A with PCF8574 backpack)")
print("  SDA -> U1 pin 15 (Q4) + 4.7K pull-up to VCC")
print("  SCL -> U1 pin 16 (Q3) + 4.7K pull-up to VCC")
print("  VCC -> VCC")
print("  GND -> GND")
print()
print("POWER: VCC not on J4 — tap from MK1 5V rail")
print("       or bodge wire to J4 pin 9 (NC)")
