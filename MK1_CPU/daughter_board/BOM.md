# MK1 Daughter Board — BOM

## Bill of Materials

| Ref | Part | Value | Package | Notes |
|-----|------|-------|---------|-------|
| U1 | 74HC574 | — | DIP-20 | 8-bit D flip-flop (output latch) |
| Q1 | NPN transistor | BC547/2N2222 | TO-92 | Speaker driver |
| BZ1 | Piezo buzzer | — | — | Driven from Q1 collector |
| R1 | Resistor | 1K | — | MISO series (contention limiter) |
| R2 | Resistor | 1K | — | Q1 base (speaker driver) |
| R3 | Resistor | 4.7K | — | I2C SDA pull-up |
| R4 | Resistor | 4.7K | — | I2C SCL pull-up |
| C1 | Ceramic cap | 100nF | — | U1 VCC decoupling |
| C2 | Ceramic cap | 100nF | — | SPI EEPROM decoupling (if on board) |
| J1 | Pin socket | 2×9 | 2.54mm | Mates with MK1 J4 header |

## Power

VCC (5V) is NOT available on J4. Tap from MK1 board's 5V rail via a separate wire,
or bodge to J4 pin 9 (NC on MK1).
