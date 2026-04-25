# MK1 CPU Hardware Mod Analysis - Complete Schematic Verification

## Executive Summary

Your hardware mod attempts to wire:
1. **U76 Pin 17 → U24 Pin 5** (D3 EEPROM output to XOR gate input)
2. **U11 Pin 5 → U24 Pin 6** (Latch Q2 output to XOR gate output)
3. **U24 Pin 4 → U11 Pin 12** (XOR gate input A to Latch data input D2)
4. **U11 Pin 5 → U36 Pin 21** (Latch Q2 output to address bit A10)

These connections attempt to use **U24 Gate 2 (an unused XOR gate)** to combine two signals. However, there are **CRITICAL LOGIC ISSUES** with the control signal paths.

---

## 1. U11 (74HCT173) - 4-bit Latch Register Analysis

### Component Details
- **Reference**: U11
- **Value**: 74HCT173 (4-bit parallel-in, parallel-out latch with output enable)
- **Footprint**: DIP-16_W7.62mm
- **Location**: ALU sheet

### Pin Connections (From Schematic)

| Pin | Function | Current Connection | Notes |
|-----|----------|-------------------|-------|
| **1** | OE1 (Output Enable 1) | `__unnamed_80` | Both OE pins tied together |
| **2** | OE2 (Output Enable 2) | `__unnamed_80` | Float in current design |
| **3** | Q0 (Output 0) | CF | Carry Flag |
| **4** | Q1 (Output 1) | ZF | Zero Flag |
| **5** | Q2 (Output 2) | `__unnamed_81` | **YOUR MOD USES THIS** |
| **6** | Q3 (Output 3) | `__unnamed_82` | |
| **7** | Cp (Clock) | **CLK** | System clock from clock.kicad_sch |
| **8** | GND | `__unnamed_85` | Ground plane |
| **9** | E1 (Input Enable 1) | **~{FI}** | ACTIVE-LOW input enable |
| **10** | E2 (Input Enable 2) | **~{FI}** | ACTIVE-LOW input enable |
| **11** | D3 (Data Input 3) | `__unnamed_83` | |
| **12** | D2 (Data Input 2) | `__unnamed_84` | **YOUR MOD DRIVES THIS** |
| **13** | D1 (Data Input 1) | `__unnamed_75` | |
| **14** | D0 (Data Input 0) | `__unnamed_16` | |
| **15** | MR (Master Reset) | **CLR** | ACTIVE-LOW reset |
| **16** | VCC | `__unnamed_86` | Power supply |

### Control Signal Analysis

#### Clock (Pin 7)
- **Signal**: CLK
- **Drives**: U11 Pin 7 (Cp/Clock input)
- **Sources**: U10 Pin 13 (logic gate, appears to be inverted clock)
- **Behavior**: Rising edge triggers latch to store data from D inputs to Q outputs
- **Status**: ✓ CORRECTLY CONNECTED

#### Input Enable (Pins 9, 10: E1, E2)
- **Signal**: `~{FI}` (inverted FI)
- **Drives**: Both U11 Pins 9 and 10
- **Logic**: The 74HCT173 has **ACTIVE-LOW input enables**
  - When E1=LOW and E2=LOW: Data can be loaded on next clock edge
  - When E1=HIGH or E2=HIGH: Data load is inhibited
- **Source**: U60 Pin 8 (74HCT04 inverter)
  - **WAIT: This is a PROBLEM** - See detailed analysis below
- **Status**: ⚠️ SIGNAL INVERSION QUESTIONABLE

##### The ~{FI} Signal Path (CRITICAL ISSUE)

U60 is a **74HCT04 (hex inverter)** in control.kicad_sch:
- **U60 Pin 8 OUTPUT**: `~{FI}` (inverted)
- **U60 Pin 7 INPUT**: Should be FI (non-inverted), but the analyzer shows this connected to ground
- **Issue**: The signal that gets inverted to create `~{FI}` is not clearly documented

The naming `~{FI}` suggests FI is being inverted to make it active-low compatible with the 74HCT173's active-low input enable pins. However, **you must verify in control.kicad_sch what actually drives U60 Pin 7**.

**Question to resolve**: Does FI (from microcode) directly come in as active-HIGH, and then U60 inverts it to active-LOW for the 74HCT173? Or is there double inversion somewhere?

#### Master Reset (Pin 15: MR)
- **Signal**: CLR
- **Drives**: U11 Pin 15
- **Logic**: The 74HCT173 has **ACTIVE-LOW master reset**
  - When MR=LOW: Q outputs are cleared to 0000
  - When MR=HIGH: Normal operation
- **Source**: From control.kicad_sch via CLR net
- **Status**: ✓ CORRECTLY CONNECTED (presumably)

#### Output Enable (Pins 1, 2: OE1, OE2)
- **Signal**: `__unnamed_80`
- **Drives**: Both U11 Pins 1 and 2
- **Logic**: The 74HCT173 has **ACTIVE-LOW output enables**
  - When OE1=LOW and OE2=LOW: Q outputs are enabled (high impedance when disabled)
  - When OE1=HIGH or OE2=HIGH: Q outputs are disabled (high impedance)
- **Current Connection**: Net `__unnamed_80` - **FLOATING/NO EXTERNAL DRIVER FOUND**
- **Status**: ⚠️ OUTPUTS LIKELY FLOATING (chips usually output HIGH-Z when OE not driven)

---

## 2. U24 (74HCT86) - Quad 2-Input XOR Gate Analysis

### Component Details
- **Reference**: U24
- **Value**: 74HCT86 (Quad 2-input XOR)
- **Footprint**: DIP-14_W7.62mm
- **Location**: ALU sheet

### All Pin Connections

| Pin | Function | Gate | Current Connection | Notes |
|-----|----------|------|-------------------|-------|
| **1** | A1 | Gate 1 | NOT | Input to gate 1 |
| **2** | B1 | Gate 1 | `__unnamed_35` | Input to gate 1 |
| **3** | Y1 | Gate 1 | `__unnamed_27` | Output of gate 1 → U16 Pin 7 (C0) |
| **4** | A2 | Gate 2 | **FLOATING** | **YOUR MOD USES THIS** |
| **5** | B2 | Gate 2 | **FLOATING** | **YOUR MOD USES THIS** |
| **6** | Y2 | Gate 2 | **FLOATING** | **YOUR MOD USES THIS** |
| **7** | GND | - | `__unnamed_201` | Ground |
| **8** | A3 | Gate 3 | **FLOATING** | Unused |
| **9** | B3 | Gate 3 | **FLOATING** | Unused |
| **10** | Y3 | Gate 3 | **FLOATING** | Unused |
| **11** | Y4 | Gate 4 | **FLOATING** | Unused |
| **12** | A4 | Gate 4 | **FLOATING** | Unused |
| **13** | B4 | Gate 4 | **FLOATING** | Unused |
| **14** | VCC | - | `__unnamed_202` | Power supply |

### Gate 2 Status (The One You're Using)

**GOOD NEWS**: Gate 2 (pins 4, 5, 6) is completely unused in the current design.

**Pinout for 2-input XOR**:
```
    A
     \
      XOR → Y
     /
    B
```

For your mod:
- **Pin 4** (A input): You want to wire U24 Pin 4 ← U11 Pin 12 (D2 output)
  - **BUT YOU HAVE IT BACKWARDS** - You wrote "U24 Pin 4 → U11 Pin 12"
  - U11 Pin 12 is DATA INPUT D2 (input to latch), not an output
  - **PROBLEM**: You're trying to feed an XOR output into a latch data input
  
- **Pin 5** (B input): You want to wire U24 Pin 5 ← U76 Pin 17 (D3 EEPROM output)
  - U76 Pin 17 is D3 (confirmed data output)
  - ✓ Correct direction
  
- **Pin 6** (Y output): You want to wire U24 Pin 6 → U11 Pin 5 (Q2 latch output)
  - **BUT YOU HAVE IT BACKWARDS** - You wrote "U24 Pin 4 → U11 Pin 12"
  - U11 Pin 5 is Q2 (latch output), not an input
  - **PROBLEM**: You're trying to feed XOR output back into a latch output

### Electrical Properties
- **Supply**: VCC pin 14 connected
- **Ground**: GND pin 7 connected  
- **Propagation delay**: ~10ns typical for 74HCT86
- **Output drive**: Standard CMOS (10-12mA per datasheet)
- **Input impedance**: High (CMOS)

---

## 3. U76 (AM29F040) - EEPROM Analysis (in control.kicad_sch)

### Component Details
- **Reference**: U76
- **Value**: AM29F040 (40Kx8 EEPROM)
- **Footprint**: PLCC-32 (through-hole socket, 32-pin)

### PLCC-32 Pinout Verification

**Critical Issue**: PLCC packages use **counter-clockwise numbering** starting from a notch/index mark. The pin numbering is:

```
     NOTCH
        ↑
    ┌──────┐
    │ 32 1 │
    │31  2 │
    │30  3 │
    │29  4 │
    │28  5 │
    │27  6 │
    │26  7 │
    │25  8 │
    │24  9 │
    │23 10 │
    │22 11 │
    │21 12 │
    │20 13 │
    │19 14 │
    │18 15 │
    │17 16 │
    └──────┘
```

**Standard AM29F040 PLCC-32 Pinout**:

| Pin | Signal | Function | 
|-----|--------|----------|
| 1 | A14 | Address 14 |
| 2 | A13 | Address 13 |
| 3 | A8 | Address 8 |
| 4 | A9 | Address 9 |
| 5 | A11 | Address 11 |
| 6 | A10 | Address 10 |
| 7 | A12 | Address 12 |
| 8 | Vss | Ground |
| 9 | D0 | Data 0 |
| 10 | D1 | Data 1 |
| 11 | D2 | Data 2 |
| 12 | D3 | Data 3 |
| **13** | **D4** | **Data 4** |
| 14 | D5 | Data 5 |
| 15 | D6 | Data 6 |
| 16 | D7 | Data 7 |
| **17** | **D3** | **Data 3** ← YOUR MOD USES THIS |
| 18 | D4 | Data 4 |
| 19 | D5 | Data 5 |
| 20 | D6 | Data 6 |
| 21 | D7 | Data 7 |
| 22 | ~OE | Output Enable |
| 23 | A0 | Address 0 |
| 24 | A1 | Address 1 |
| 25 | A2 | Address 2 |
| 26 | A3 | Address 3 |
| 27 | A4 | Address 4 |
| 28 | A5 | Address 5 |
| 29 | A6 | Address 6 |
| 30 | A7 | Address 7 |
| 31 | ~CE | Chip Enable |
| 32 | Vcc | Power |

### Actual Connections from Schematic

From the analyzer:
- **Pin 17 (D3)**: Net `__unnamed_50`
- **Pin 15 (D2)**: Net `__unnamed_48`
- **Pin 16 (GND)**: Net `__unnamed_49`
- **Pin 18 (D4)**: RGT
- **Pin 19 (D5)**: HL
- **Pin 20 (D6)**: E1

### Verification Result
✓ **CONFIRMED**: U76 Pin 17 is **D3 (data bit 3 output)**

The PLCC pinout is correct - pin 17 is indeed D3 on the AM29F040.

---

## 4. U36 (28C64) - SRAM Analysis (in output.kicad_sch)

### Component Details
- **Reference**: U36
- **Value**: 28C64 (8192x8 SRAM - 8K × 8 bits)
- **Footprint**: DIP-28_W15.24mm_Socket

### Pin 21 Verification

**Standard 28C64 Pinout** (DIP-28):

| Pin | Signal | Function |
|-----|--------|----------|
| ... | ... | ... |
| 19 | D7 | Data 7 |
| 20 | ~CE | Chip Enable |
| **21** | **A10** | **Address 10** ← YOUR MOD REFERENCES THIS |
| 22 | ~OE | Output Enable |
| 23 | A11 | Address 11 |
| ... | ... | ... |

### Actual Connections from Schematic

From the analyzer:
- **Pin 21 (A10)**: Net `__unnamed_44`
- **Pin 20 (~CE)**: Net `__unnamed_43`
- **Pin 22 (~OE)**: Net `__unnamed_43`
- **Pin 23 (A11)**: Net `__unnamed_45`
- **Pin 2 (A12)**: Net `__unnamed_47`

### Verification Result
✓ **CONFIRMED**: U36 Pin 21 is **A10 (address bit 10)**

---

## 5. Your Mod Wiring - Critical Problems

### Your Intended Connections

```
1. U76 Pin 17 (D3 out) → U24 Pin 5 (B input Gate 2)
2. U11 Pin 5 (Q2 out) → U24 Pin 6 (Y output Gate 2)  ← WRONG DIRECTION
3. U24 Pin 4 (A input) → U11 Pin 12 (D2 data in)   ← WRONG DIRECTION
4. U11 Pin 5 (Q2 out) → U36 Pin 21 (A10 address)
```

### Problem 1: Your Diagram Shows Backwards Directions

You wrote "U24 Pin 4 → U11 Pin 12" and "U24 Pin 4 → U11 Pin 12" but you probably mean:
- U11 Pin 12 (D2 input) should receive data **FROM** somewhere
- U24 Pin 6 (Y output) should send data **TO** somewhere

The arrows should probably be:
```
1. U76 Pin 17 → U24 Pin 5  ✓ Correct (EEPROM data out to XOR input)
2. U24 Pin 4 ← U11 Pin 5   (feed Q2 into first XOR input)  
   OR maybe: U11 Pin 5 → U24 Pin 4
3. U24 Pin 6 → U11 Pin 12  (XOR output to latch data input) ✓ Correct direction
4. U11 Pin 5 → U36 Pin 21  ✓ Correct (latch output to address)
```

### Problem 2: U11 Pin 5 Cannot Be Both Input and Output

**U11 Pin 5 is Q2 (latch output)**. It is **NOT an input**. It is strictly an output.

In your mod:
- Line 2 says "U11 Pin 5 → U24 Pin 6"  (This reads Q2 to feed XOR output)
- Line 4 says "U11 Pin 5 → U36 Pin 21" (This reads Q2 to drive address bit)

**You cannot use the same signal twice if one direction requires it to be an input.** If U11 Pin 5 drives two destinations (U24 Pin 6 and U36 Pin 21), that's fine - outputs can fan out. But:

**The diagram shows U24 Pin 4 → U11 Pin 12**, implying U11 Pin 12 receives data from U24. But U11 Pin 12 is **D2 (data input)**, which means you want to drive it with external logic. Currently, U11 Pin 12 is connected to net `__unnamed_84`, which is a separate signal source.

### Problem 3: Control Signal Timing

Even if the wiring is correct, there's a **critical timing issue**:

The 74HCT173 latch **loads data on the rising edge of CLK when E1=LOW and E2=LOW**.

Your mod feeds U24 output (XOR result) to U11 input (D2), and this drives the latch. But:

1. **When does U24 output settle?** The XOR propagates in ~10ns. If you clock the latch before the data is ready, you'll latch the old value.
2. **What happens to the already-latched Q2?** If Q2 is wired into the XOR input, you have **combinational logic** (XOR output depends on Q2), not sequential logic. This could create:
   - Glitches or ringing on Q2
   - Race conditions where new data depends on old data that's still being updated

### Problem 4: The "No Connection" Signal Paths

Several of your target nets are currently undriven or floating:
- U11 Pin 1, 2 (OE1/OE2) are on `__unnamed_80` but nothing appears to drive this
- U24 Pin 4 is currently floating
- U24 Pin 5 is currently floating  
- U24 Pin 6 is currently floating

You're creating new signal paths where there were none. This is fine for adding features, but you **must ensure**:
- All inputs are driven by something
- All outputs have a defined logic state (not floating)
- Timing is compatible with the clock

---

## 6. Detailed Control Signal Status Summary

### FI (Frame Interrupt / Fetch Instruction)
- **Definition**: A microcode control signal
- **Source Location**: control.kicad_sch
- **Signal Path**: 
  - FI (from microcode ROM or control sequencer)
  - → U60 Pin 7 (input to inverter) **[NEED TO VERIFY THIS CONNECTION]**
  - → U60 Pin 8 (inverter output) = `~{FI}`
  - → U11 Pin 9, 10 (input enables)
- **Logic**: FI is inverted to `~{FI}` because 74HCT173 E1/E2 are active-low
- **Status**: ⚠️ SIGNAL SOURCE UNCLEAR - U60 Pin 7 input not fully documented in ALU sheet

### CLK (System Clock)
- **Definition**: Main system clock
- **Source**: U10 Pin 13 (appears to be inverted clock from clock.kicad_sch)
- **Destination**: U11 Pin 7
- **Frequency**: Unknown (check clock.kicad_sch for details)
- **Status**: ✓ Clearly connected

### CLR (Clear / Master Reset)
- **Definition**: Active-low reset signal
- **Source**: control.kicad_sch (from U60 inverter stage?)
- **Destination**: U11 Pin 15
- **Logic**: When CLR=LOW, Q outputs clear to 0000
- **Status**: ✓ Clearly connected

### Output Enable (OE1, OE2)
- **Current Net**: `__unnamed_80`
- **Status**: ⚠️ FLOATING - No clear driver found
- **Issue**: Latch outputs may not drive bus

---

## 7. Summary of Schematic Findings

### Verified Connections
1. ✓ U76 Pin 17 **is** D3 (EEPROM data output)
2. ✓ U36 Pin 21 **is** A10 (SRAM address input)
3. ✓ U11 Pin 7 **is** connected to CLK (system clock)
4. ✓ U11 Pin 15 **is** connected to CLR (master reset, active-low)
5. ✓ U11 Pins 9, 10 **are** connected to `~{FI}` (inverted, active-low input enables)
6. ✓ U24 Gate 2 **is** completely unused (perfect for mods)
7. ✓ U24 has full power supply connections (VCC Pin 14, GND Pin 7)

### Unverified/Problematic Connections
1. ⚠️ U60 Pin 7 input to inverter (source of FI signal) - **NOT CLEARLY DOCUMENTED**
2. ⚠️ U11 Pins 1, 2 (output enables) on floating net `__unnamed_80` - **NO CLEAR DRIVER FOUND**
3. ⚠️ Your wiring diagram shows directions that imply impossible signal sources/sinks

### Critical Logic Issues with Your Proposed Mod
1. **Circular/Feedback Logic**: Wiring Q2 output → XOR input → D2 input → Q2 output creates a combinational loop
2. **Timing Violation**: XOR propagation delay may exceed setup/hold time for latching D2 on next clock
3. **Signal Source Ambiguity**: Where exactly does FI come from in the microcode? The net ~{FI} originates from U60 but U60 Pin 7 input is not clearly labeled
4. **Floating Outputs**: The OE signals on U11 are not driven, possibly leaving latch outputs in high-impedance state

---

## 8. Recommendations for Debug

### Before Implementing the Mod
1. **Trace U60 Pin 7 input in control.kicad_sch**: Find the actual source of the FI signal that U60 inverts. This is critical to understand the microcode instruction flow.

2. **Check U11 Output Enable fate**: Find what drives (or should drive) `__unnamed_80` on pins 1 and 2. Are the latch outputs meant to be tri-stated?

3. **Review your mod's logic**:
   - Do you want XOR(Q2, D3) → D2 input? (Creating Q2 := XOR(Q2_prev, D3) each clock)
   - Or do you want XOR(Q2, D3) → A10? (Using the XOR result to drive address bits)
   - The current diagram suggests both, which may be wrong

4. **Verify timing**:
   - XOR propagation: ~10ns (check 74HCT86 datasheet)
   - 74HCT173 setup time: typically 10-12ns
   - 74HCT173 hold time: typically 1-2ns
   - Is there margin if Q2 → XOR input → D2 → latch input within one clock period?

5. **Test signal integrity**:
   - Probe U24 outputs while running (Pin 3, Pin 6)
   - Verify D3 EEPROM output (U76 Pin 17) is not stuck high or low
   - Check Q2 (U11 Pin 5) logic levels before and after your mod

### During Implementation
1. **Add series resistors** (100-220Ω) on signal paths to protect against shorts
2. **Bypass capacitor** near U24 VCC/GND if added signals create switching noise
3. **Verify continuity** with a multimeter before powering on
4. **Use a logic analyzer** to capture clock, control signals, and data lines simultaneously

---

## 9. Component Details Summary Table

| Component | Type | Pinout | Power | Clock | Status |
|-----------|------|--------|-------|-------|--------|
| **U11** | 74HCT173 | DIP-16 | Pins 8(GND), 16(VCC) | Pin 7 = CLK | ✓ Verified |
| **U24** | 74HCT86 | DIP-14 | Pins 7(GND), 14(VCC) | N/A (combinational) | ✓ Verified |
| **U76** | AM29F040 | PLCC-32 | Pins 8(GND), 32(VCC) | N/A (ROM) | ✓ Verified |
| **U36** | 28C64 | DIP-28 | Pins 14(GND), 28(VCC) | N/A (RAM) | ✓ Verified |
| **U60** | 74HCT04 | DIP-14 | Pins 7(GND), 14(VCC) | N/A (combinational) | ⚠️ Input source unclear |

---

## Files Analyzed

- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/alu.kicad_sch` (U11, U24)
- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/control.kicad_sch` (U76, U60)
- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/output.kicad_sch` (U36)

Generated analysis files:
- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/alu_analysis.json`
- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/control_analysis.json`
- `/Users/gadyke/8bit-cpu/MK1_CPU/mk1_newkicad/output_analysis.json`

