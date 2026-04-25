from copy import deepcopy
import argparse
from io import BytesIO
import sys
from functools import reduce

_VERSION = "2.0d"

HLT = 0b10000000000000000000000000000000  # Halt clock
STK = 0b01000000000000000000000000000000  # Memory Stack address space
PE  = 0b00100000000000000000000000000000  # Program counter enable
AI  = 0b00010000000000000000000000000000  # A register in
BI  = 0b00001000000000000000000000000000  # B register in
CI  = 0b00011000000000000000000000000000  # C register in
DI  = 0b00000100000000000000000000000000  # D register in
SI  = 0b00010100000000000000000000000000  # StakPointer register in
EI  = 0b00001100000000000000000000000000  # ALU register in
PI  = 0b00011100000000000000000000000000  # Program counter in
MI  = 0b00000010000000000000000000000000  # Memory address register in
RI  = 0b00000001000000000000000000000000  # RAM data in
II  = 0b00000000100000000000000000000000  # Instruction register in
OI  = 0b00000000010000000000000000000000  # Output register in
XI  = 0b00000000001000000000000000000000  # External Interface in
AO  = 0b00000000000100000000000000000000  # A register out
BO  = 0b00000000000010000000000000000000  # B register out
CO  = 0b00000000000110000000000000000000  # C register out
DO  = 0b00000000000001000000000000000000  # D register out
PO  = 0b00000000000101000000000000000000  # Program Counter out
SO  = 0b00000000000011000000000000000000  # StackPointer register out
EO  = 0b00000000000111000000000000000000  # ALU register out
RO  = 0b00000000000000100000000000000000  # RAM data out
_IO = 0b00000000000000010000000000000000  # Instruction register out
SUB = 0b00000000000000001000000000000000  # ALU subtract mode
OR  = 0b00000000000000000100000000000000  # ALU OR mode
AND = 0b00000000000000001100000000000000  # ALU AND mode
SHF = 0b00000000000000000010000000000000  # REG A SHIFT mode
ROT = 0b00000000000000001010000000000000  # REG A ROTATE mode
RGT = 0b00000000000000000000000000010000  # Right SHIFT or ROTATE
NOT = 0b00000000000000001110000000000000  # ALU NOT mode
FI  = 0b00000000000000000001000000000000  # Flags in
SU  = 0b00000000000000000000100000000000  # StackPointer count UP
SD  = 0b00000000000000000000010000000000  # StackPointer count DOWN
U0  = 0b00000000000000000000001000000000  # X-USR sig 0
U1  = 0b00000000000000000000000100000000  # X-USR sig 1
E0  = 0b00000000000000000000000010000000  # X-Enable 0
E1  = 0b00000000000000000000000001000000  # X-Enable 1
HL  = 0b00000000000000000000000000100000  # HL address mode
CINV= 0b00000000000000000000000000000010  # Carry invert (INC/DEC) — U76 D1
SETPG=0b00000000000000000000000000000100  # Code page toggle — U76 D2 (reserved for code banking)
DISP= 0b00000000000000000000000000001000  # Display mode latch — U76 D3 (reserved for display control)
RST = 0b00000000000000000000000000000001  # Reset step counter

signals = {HLT : "HLT", STK: "STK", PE: "PE" , AI: "AI", BI: "BI", CI: "CI", DI: "DI", SI: "SI", EI: "EI", PI: "PI", MI: "MI", RI: "RI", II: "II", OI: "OI", XI: "XI", AO: "AO", BO: "BO", CO: "CO", DO: "DO", PO: "PO", SO: "SO", EO: "EO", RO: "RO", _IO: "IO", SUB: "SUB", OR: "OR", AND: "AND", SHF: "SHF", ROT: "SHF", RGT: "RGT", NOT: "NOT", FI: "FI", SU: "SU", SD: "SD", U0: "U0", U1: "U1", E0: "E0", E1: "E1", HL: "HL", DISP: "DISP", SETPG: "SETPG", CINV: "CINV", RST: "RST"}

register_map = {0: ('$a', AI, AO),
                1: ('$b', BI, BO),
                2: ('$c', CI, CO),
                3: ('$d', DI, DO),
                4: ('$sp', SI, SO),
                5: ('$pc', PI, PO),
                6: ('$out', OI, 0),
                7: ('imm', 0, RO)}

alu_op_map = {0: ('add', 0), 1: ('sub', SUB), 2: ('or', OR), 3: ('and', AND)}

ucode_template = dict()

#MOV
#move $a $b
#nop = move $a $a
#jmp = move imm $pc
#--- specials ---
#exw 0 0 = move $a imm
#exw 0 1 = move $b imm
#exw 1 0 = move $c imm
#exw 1 1 = move $d imm
#je0 = move $sp imm
#je1 = move $pc imm
#jcf = move $spp imm
#jzf = move $imm imm
ucode_template.update({
    (0b00 << 6) + (first << 3) + second : ('move %s, %s'%(register_map[first][0], register_map[second][0]), [MI|PO, RO|II|PE, register_map[first][2]|register_map[second][1], RST, RST, RST, RST, RST] if first != 7 else
    [MI|PO, RO|II|PE, PO|MI, PE|register_map[first][2]|register_map[second][1], RST, RST, RST, RST], (second == 7 or first == 7))
    for first in range(8) for second in range(8)})

#LOAD
#loadi $a imm
#load $a [$b]
#pop $a = load $a [$spp]
#ret = load $pc [$spp]
#-- specials --
#exr 0 = load imm $a
#exr 1 = load imm $b
# 3: ('not', NOT), 4: ('sll', SHF), 5: ('srl', SHF|RGT), 6: ('rll', ROT), 7: ('rlr', ROT|RGT)
#not = load imm $c
#sll = load imm $d
#srl = load imm $sp
#rll = load imm $pc
#rlr = load imm $spp
#out = load imm imm

#6: ('$spp', SO|SD, SO|SU)
ucode_template.update({
    (0b01 << 6) + (first << 3) + second : ('load %s, [%s]'%(register_map[first][0], register_map[second][0]),
    [MI|PO, RO|II|PE, SU,register_map[second][2]|MI, STK|register_map[first][1]|RO, (PE if first == 5 else RST), RST, RST] if second == 4 else
    [MI|PO, RO|II|PE, register_map[second][2]|MI, HL|register_map[first][1]|RO, RST, RST, RST, RST], (second == 7 or first == 7))
    for first in range(7) for second in range(7)})

ucode_template.update({
    (0b01 << 6) + (first << 3) + second : ('load %s, [%s]'%(register_map[first][0], register_map[second][0]),
    [MI|PO, RO|II|PE, PO|MI|SU,PE|register_map[second][2]|MI, STK|register_map[first][1]|RO, (PE if first == 5 else RST), RST, RST] if second == 4 else
    [MI|PO, RO|II|PE, PO|MI, PE|register_map[second][2]|MI, HL|register_map[first][1]|RO, RST, RST, RST], (second == 7 or first == 7))
    for first in range(7) for second in range(7,8)})

#STORE
#store $a imm
#store $a [$b]
#push $a = store $a [$spp]
#jal imm = stor $pc, $spp
#-- specials --
#op_i x $b = 10 - 11 - op - $b -> immediate operation on $a, result on $b
#hlt = store $a [$sp]

#6: ('$spp', SO|SD, SO|SU)
ucode_template.update({
    (0b10 << 6) + (first << 3) + second : ('stor %s, [%s]'%(register_map[first][0], register_map[second][0]), [MI|PO, RO|II|PE, register_map[second][2]|MI, (STK|SD if second == 4 else HL)|register_map[first][2]|RI, RST, RST, RST, RST], (second == 7 or first == 7))
    for first in range(6) for second in range(7)})

ucode_template.update({
    (0b10 << 6) + (first << 3) + second : ('stor %s, [%s]'%(register_map[first][0], register_map[second][0]), [MI|PO, RO|II|PE, PO|MI, PE|register_map[second][2]|MI, (STK|SD if second == 4 else HL)|register_map[first][2]|RI, RST, RST, RST], (second == 7 or first == 7))
    for first in range(6) for second in range(7,8)})

ucode_template.update({
    (0b1011 << 4) + (op << 2) + second : ('%s imm, %s'%(alu_op_map[op][0], register_map[second][0]), [MI|PO, RO|II|PE,  PO|MI,  PE|RO|EI, register_map[second][1]|EO|FI|alu_op_map[op][1], RST, RST, RST], True)
    for second in range(4) for op in range(4)})

ucode_template[0b01111111] = ('hlt', [MI|PO, RO|II|PE,  HLT, RST, RST, RST, RST, RST], False)
#ALU
#op $a $b
#11 - op - rs - rd
ucode_template.update({
    (0b11 << 6) + (op << 4) + (first << 2) + second : ('%s %s, %s'%(alu_op_map[op][0], register_map[first][0], register_map[second][0]), [MI|PO, RO|II|PE, register_map[first][2]|EI, register_map[second][1]|EO|FI|alu_op_map[op][1], RST, RST, RST, RST], False)
    for first in range(4) for second in range(4) for op in range(4)})

ucode_template[0b01111000] = ('exr 0 0', [MI|PO, RO|II|PE, XI|E0|AI, RST, RST, RST, RST, RST], False)
ucode_template[0b01111001] = ('exr 1 0', [MI|PO, RO|II|PE, XI, XI|E1|AI, RST, RST, RST, RST], False)

ucode_template[0b01111010] = ('not', [MI|PO, RO|II|PE,  AO|EI, AI, NOT|EO|AI, RST, RST, RST], False)
ucode_template[0b01111011] = ('sll', [MI|PO, RO|II|PE,  SHF|AI|FI, RST,     RST, RST, RST, RST], False)

# sllb: shift B left by 1, result stored in both A and B, flags from shift.
# Equivalent to `mov $b,$a; sll; mov $a,$b` (3B) in a single byte.
# Retires 0x22 (move $sp, $c) — 0 uses across the 42-program corpus.
# Corpus scan identified 65 occurrences of the shift-B triple; sllb saves
# 2B per use = ~130B corpus-wide.
ucode_template[0b00100010] = ('sllb', [MI|PO, RO|II|PE, BO|AI, SHF|AI|FI, AO|BI, RST, RST, RST], False)
ucode_template[0b01111100] = ('slr', [MI|PO, RO|II|PE,  SHF|RGT|AI|FI, RST, RST, RST, RST, RST], False)
ucode_template[0b01111101] = ('rll', [MI|PO, RO|II|PE,  ROT|AI|FI, RST,     RST, RST, RST, RST], False)
ucode_template[0b01111110] = ('rlr', [MI|PO, RO|II|PE,  ROT|RGT|AI|FI, RST, RST, RST, RST, RST], False)

# exw: external write with pre-settle step
# Step 2: AO + register select (data on bus, register selected, NO enable yet)
# Step 3: AO + enable + register select (VIA latches with stable signals)
# This prevents data bus glitches from coupling into register select lines.
ucode_template[0b00000111] = ('exw 0 0', [MI|PO, RO|II|PE, AO, AO|E0, RST, RST, RST, RST], False)
ucode_template[0b00001111] = ('exw 0 1', [MI|PO, RO|II|PE, AO|U0, AO|E0|U0, RST, RST, RST, RST], False)
ucode_template[0b10001110] = ('exw 0 2', [MI|PO, RO|II|PE, AO|U1, AO|E0|U1, RST, RST, RST, RST], False)
ucode_template[0b10010110] = ('exw 0 3', [MI|PO, RO|II|PE, AO|U1|U0, AO|E0|U1|U0, RST, RST, RST, RST], False)
ucode_template[0b00010111] = ('exw 1 0', [MI|PO, RO|II|PE, AO, AO|E1, RST, RST, RST, RST], False)
ucode_template[0b00011111] = ('exw 1 1', [MI|PO, RO|II|PE, AO|E1, AO|E1|E0, RST, RST, RST, RST], False)
ucode_template[0b10011110] = ('exw 1 2', [MI|PO, RO|II|PE, AO|U1, AO|E1|U1, RST, RST, RST, RST], False)
ucode_template[0b10100110] = ('exw 1 3', [MI|PO, RO|II|PE, AO|U1|U0, AO|E1|U1|U0, RST, RST, RST, RST], False)

ucode_template[0b10101110] = ('cmp $b', [MI|PO, RO|II|PE, BO|EI, SUB|FI, RST, RST, RST, RST], False)
ucode_template[0b01000110] = ('cmp $c', [MI|PO, RO|II|PE, CO|EI, SUB|FI, RST, RST, RST, RST], False)
ucode_template[0b01001110] = ('cmp $d', [MI|PO, RO|II|PE, DO|EI, SUB|FI, RST, RST, RST, RST], False)
ucode_template[0b10000110] = ('cmp imm', [MI|PO, RO|II|PE,  PO|MI, PE|RO|EI, SUB|FI, RST, RST, RST], False)

ucode_template[0b00100111] = ('je0', [MI|PO, RO|II|PE, PE, RST, RST, RST, RST, RST], False)
ucode_template[0b00101111] = ('je1', [MI|PO, RO|II|PE, PE, RST, RST, RST, RST, RST], False)
ucode_template[0b00110111] = ('jcf', [MI|PO, RO|II|PE, PE, RST, RST, RST, RST, RST], False)
ucode_template[0b00111111] = ('jzf', [MI|PO, RO|II|PE, PE, RST, RST, RST, RST, RST], False)

# ── Phase 1 new instructions (reclaim redundant self-OR and exotic C/D opcodes) ──

# XOR: A = A XOR B (clobbers D)
# XOR(A,B) = (A OR B) - (A AND B)
# Step 2: E=B, Step 3: D=A AND B, Step 4: A=A OR B, Step 5: E=D, Step 6: A=(A OR B)-(A AND B)
ucode_template[0xE0] = ('xor', [MI|PO, RO|II|PE, BO|EI, DI|EO|AND, AI|EO|OR, DO|EI, AI|EO|SUB|FI, RST], False)

# NEG: A = -A (two's complement negate)
# Step 2: E=A, Step 3: A=A-A=0, Step 4: A=0-E=-A_orig
ucode_template[0xE5] = ('neg', [MI|PO, RO|II|PE, AO|EI, SUB|EO|AI, SUB|EO|AI|FI, RST, RST, RST], False)

# LDP3: A = page3[imm] (load from page 3 data)
# Step 2: MAR=PC, Step 3: PC++, MAR=mem[PC] (address), Step 4: A=SRAM[STK|HL|addr]
ucode_template[0xEA] = ('ldp3', [MI|PO, RO|II|PE, PO|MI, PE|RO|MI, STK|HL|RO|AI, RST, RST, RST], True)

# STP3: page3[imm] = A (store to page 3 data)
ucode_template[0xEF] = ('stp3', [MI|PO, RO|II|PE, PO|MI, PE|RO|MI, STK|HL|AO|RI, RST, RST, RST], True)

# LDSP: A = stack[SP + imm] (stack-relative load)
# Step 2: E=SP, Step 3: MAR=PC, Step 4: A=offset+PC++, Step 5: MAR=A+E=SP+offset, Step 6: A=stack[addr]
ucode_template[0xEB] = ('ldsp', [MI|PO, RO|II|PE, SO|EI, PO|MI, PE|RO|AI, EO, EO|MI, STK|RO|AI], True)

# INC: A = A + 1 (single byte, sets flags)
# CINV=1, SUB=0: carry-in XOR'd to 1, B not inverted. A + 0 + 1 = A + 1.
# E must be 0: we use SUB to compute A-A=0 into E first, then add with CINV.
# Step 2: AO|EI (E=A), Step 3: SUB|EO|EI (E=A-A=0), Step 4: CINV|EO|AI|FI (A=A+0+1)
ucode_template[0xFB] = ('inc', [MI|PO, RO|II|PE, AO|EI, SUB|EO|EI, CINV|EO|AI|FI, RST, RST, RST], False)

# DEC: A = A - 1 (single byte, sets flags)
# CINV=1, SUB=1: carry-in XOR'd to 0, B inverted. A + 0xFF + 0 = A - 1.
# E must be 0 (same trick), then SUB inverts it to 0xFF with carry=0.
ucode_template[0xFE] = ('dec', [MI|PO, RO|II|PE, AO|EI, SUB|EO|EI, CINV|SUB|EO|AI|FI, RST, RST, RST], False)

# ── INC/DEC on non-A registers (generic, used for any loop counter) ──
# Pattern: route REG → A, run A's dec/inc microcode, route A → REG.
# Clobbers A with the new register value. Sets flags.
# Replaces 3-byte pattern `mov $X,$a; dec|inc; mov $a,$X` with 1 byte.
# Reclaims opcodes NOT emitted by the compiler (verified against mk1cc2.py).
# Uses only existing micro-signals (DO/DI/BO/BI/CO/CI/AI/AO/EI/EO/SUB/CINV/FI) —
# no new hardware wiring. CINV was added for A's inc/dec bodge; these reuse it.

# DEC $b (replaces sub $d,$a — auto-gen ALU, not emitted)
ucode_template[0xDC] = ('decb', [MI|PO, RO|II|PE, BO|AI, AO|EI, SUB|EO|EI, CINV|SUB|EO|AI|FI, AO|BI, RST], False)
# DEC $c (replaces sub $c,$a — auto-gen ALU, not emitted)
ucode_template[0xD8] = ('decc', [MI|PO, RO|II|PE, CO|AI, AO|EI, SUB|EO|EI, CINV|SUB|EO|AI|FI, AO|CI, RST], False)
# DEC $d (replaces and $d,$a — auto-gen ALU, not emitted).
# Moved off 0xCC because the compiler's register allocator DOES emit
# `add $d,$a` (0xCC) when a variable ends up in D.
ucode_template[0xFC] = ('decd', [MI|PO, RO|II|PE, DO|AI, AO|EI, SUB|EO|EI, CINV|SUB|EO|AI|FI, AO|DI, RST], False)
# INC $b (replaces and $b,$b — auto-gen ALU, not emitted).
# Keeping jal_r at 0xE1 intact — it's the only primitive for indirect calls
# (function pointers, jump tables) and we may want it for future C features.
ucode_template[0xF5] = ('incb', [MI|PO, RO|II|PE, BO|AI, AO|EI, SUB|EO|EI, CINV|EO|AI|FI, AO|BI, RST], False)
# INC $c (replaces or $c,$a — auto-gen ALU, not emitted)
ucode_template[0xE8] = ('incc', [MI|PO, RO|II|PE, CO|AI, AO|EI, SUB|EO|EI, CINV|EO|AI|FI, AO|CI, RST], False)
# INC $d (replaces or $d,$a — auto-gen ALU, not emitted)
ucode_template[0xEC] = ('incd', [MI|PO, RO|II|PE, DO|AI, AO|EI, SUB|EO|EI, CINV|EO|AI|FI, AO|DI, RST], False)

# JNC: jump if NOT carry (base template = take jump, patched to skip when CF=1)
ucode_template[0xCA] = ('jnc', [MI|PO, RO|II|PE, PO|MI, RO|PI, RST, RST, RST, RST], True)

# JNZ: jump if NOT zero (base template = take jump, patched to skip when ZF=1)
ucode_template[0xCE] = ('jnz', [MI|PO, RO|II|PE, PO|MI, RO|PI, RST, RST, RST, RST], True)

# DDRB2_IMM A B: two consecutive DDRB writes in one opcode (3 bytes total).
# Retires setjmp (0xCB). setjmp was "toggle code page and jump" reserved for
# future code banking — SETPG is unwired (U76 D2 floats), so it was function-
# ally identical to `j imm` and never emitted. Frees the slot for DDRB pair
# fusion. Corpus has 291 ddrb_imm pairs × 1B saved = ~291B corpus-wide.
# Plus 200 triples and 42 quads benefit (pairs within them).
ucode_template[0xCB] = ('ddrb2_imm',
    [MI|PO, RO|II|PE,
     PO|MI, PE|RO|E0|U1,     # read imm1, write to DDRB, PC++
     PO|MI, PE|RO|E0|U1,     # read imm2, write to DDRB, PC++
     RST, RST], True)

# DDRB3_IMM A B C: three consecutive DDRB writes in one opcode (4 bytes total).
# Retires setret (0xCF). Same rationale — setret was reserved for code banking
# return, which requires hw wiring we don't have. Frees the slot for DDRB
# triple fusion, the densest pattern in I2C code (200 triples corpus-wide).
# Uses all 8 microsteps (counter wraps naturally after last write).
ucode_template[0xCF] = ('ddrb3_imm',
    [MI|PO, RO|II|PE,
     PO|MI, PE|RO|E0|U1,
     PO|MI, PE|RO|E0|U1,
     PO|MI, PE|RO|E0|U1], True)

# STSP: stack[SP + offset] = A (clobbers D)
# Step 2: D=A (save value), Step 3: E=SP, Step 4-5: read offset+PC++
# Step 6: MAR=SP+offset, Step 7: write D to stack
# Uses all 8 steps (counter wraps naturally)
ucode_template[0xDB] = ('stsp', [MI|PO, RO|II|PE, AO|DI, SO|EI, PO|MI, PE|RO|AI, EO|MI, STK|DO|RI], True)

# DEREF: A = data[A] — indirect load from data page at address in A
ucode_template[0xC3] = ('deref', [MI|PO, RO|II|PE, AO|MI, HL|RO|AI, RST, RST, RST, RST], False)

# IDEREF: data[B] = A — indirect store to data page at address in B
ucode_template[0xC7] = ('ideref', [MI|PO, RO|II|PE, BO|MI, HL|AO|RI, RST, RST, RST, RST], False)

# SETZ: A = (ZF ? 1 : 0) — flag-dependent, patched in initUCode
# Base (ZF=0): A = 0
ucode_template[0xD3] = ('setz', [MI|PO, RO|II|PE, AO|EI, SUB|EO|AI, RST, RST, RST, RST], False)

# SETNZ: A = (ZF ? 0 : 1) — inverse of setz
# Base (ZF=0): A = 1 (clear then inc)
ucode_template[0xD7] = ('setnz', [MI|PO, RO|II|PE, AO|EI, SUB|EO|AI, AO|EI, CINV|EO|AI, RST, RST], False)

# SETC: A = (CF ? 1 : 0) — flag-dependent
# Base (CF=0): A = 0
ucode_template[0xDE] = ('setc', [MI|PO, RO|II|PE, AO|EI, SUB|EO|AI, RST, RST, RST, RST], False)

# SETNC: A = (CF ? 0 : 1) — inverse of setc
# Base (CF=0): A = 1
ucode_template[0xE3] = ('setnc', [MI|PO, RO|II|PE, AO|EI, SUB|EO|AI, AO|EI, CINV|EO|AI, RST, RST], False)

# PUSH_IMM N: push immediate value onto stack, A = N
ucode_template[0xE7] = ('push_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|AI, SO|MI, STK|SD|AO|RI, RST, RST], True)

# LDSP_B N: B = stack[SP+N] (clobbers A with offset temporarily)
ucode_template[0xF3] = ('ldsp_b', [MI|PO, RO|II|PE, SO|EI, PO|MI, PE|RO|AI, EO, EO|MI, STK|RO|BI], True)

# IDEREFP3: page3[B] = A — indirect store to page 3
ucode_template[0xF7] = ('iderefp3', [MI|PO, RO|II|PE, BO|MI, STK|HL|AO|RI, RST, RST, RST, RST], False)

# EXR variants for 82C55 PPI: stretched reads with XI setup step before E1 assertion.
# Step 2 settles XI and U0/U1 (A0/A1). Step 3 asserts E1 (~RD) with stable address.
# This prevents EEPROM glitches on U75 (U0/U1) from selecting the wrong 82C55 register.
#
# exr 1 0 = read Port A (A0=0, A1=0) — at 0x79 above
# exr 1 1 = read Port B (A0=1, A1=0)
ucode_template[0xC5] = ('exr 1 1', [MI|PO, RO|II|PE, XI|U0, XI|E1|AI|U0, RST, RST, RST, RST], False)
# exr 1 2 = read Port C (A0=0, A1=1)
ucode_template[0xC6] = ('exr 1 2', [MI|PO, RO|II|PE, XI|U1, XI|E1|AI|U1, RST, RST, RST, RST], False)
# exr 1 3 = read Control register (A0=1, A1=1)
ucode_template[0xD2] = ('exr 1 3', [MI|PO, RO|II|PE, XI|U0|U1, XI|E1|AI|U0|U1, RST, RST, RST, RST], False)

# ── exrw: read with BOTH E0+E1 asserted (for W65C22S VIA) ──
# E0 → PHI2 (bus clock), E1 → R/W=HIGH (read).
# Stretched: XI setup in step 2, then E0+E1+AI in step 3.
# Same as exr 1 X but with E0 added for PHI2.
# NOTE: clears both IRQ0 and IRQ1 (XI+E0 and XI+E1 both active).
# exrw 0 = read VIA register 0 (ORB/IRB)
ucode_template[0xC0] = ('exrw 0', [MI|PO, RO|II|PE, XI, XI|E0|E1|AI, RST, RST, RST, RST], False)
# exrw 1 = read VIA register 1 (ORA/IRA)
ucode_template[0xC9] = ('exrw 1', [MI|PO, RO|II|PE, XI|U0, XI|E0|E1|AI|U0, RST, RST, RST, RST], False)
# exrw 2 = read VIA register 2 (DDRB)
ucode_template[0xCD] = ('exrw 2', [MI|PO, RO|II|PE, XI|U1, XI|E0|E1|AI|U1, RST, RST, RST, RST], False)
# exrw 3 = read VIA register 3 (DDRA)
ucode_template[0xD6] = ('exrw 3', [MI|PO, RO|II|PE, XI|U0|U1, XI|E0|E1|AI|U0|U1, RST, RST, RST, RST], False)

# DEREFP3: A = page3[A] — indirect read from page 3
ucode_template[0xD5] = ('derefp3', [MI|PO, RO|II|PE, AO|MI, STK|HL|RO|AI, RST, RST, RST, RST], False)

# DEREF2: A = stack_page[A] — indirect read from page 2 (stack page bottom)
# Same as deref but STK instead of HL. Enables using unused stack page as overlay storage.
ucode_template[0xDD] = ('deref2', [MI|PO, RO|II|PE, AO|MI, STK|RO|AI, RST, RST, RST, RST], False)

# IDEREF2: stack_page[B] = A — indirect write to page 2 (stack page bottom)
ucode_template[0xED] = ('ideref2', [MI|PO, RO|II|PE, BO|MI, STK|AO|RI, RST, RST, RST, RST], False)

# ISTC: code[B] = A — indirect store to code page (no HL, no STK)
ucode_template[0xDA] = ('istc', [MI|PO, RO|II|PE, BO|MI, AO|RI, RST, RST, RST, RST], False)

# CMPI N: compare A with immediate N. Sets ZF/CF from A-N. Doesn't clobber A or B.
# Replaces the old cmp N expansion (ldi $b,N; cmp $b) which clobbered B.
ucode_template[0xFD] = ('cmpi', [MI|PO, RO|II|PE, PO|MI, PE|RO|EI, SUB|EO|FI, RST, RST, RST], True)

# ISTC_INC: code[B] = A; B++ — istc with auto-increment for bulk code writes.
# Steps 4-7: B = B + 1 via zero-E trick (same as INC but targeting B).
# Clobbers A (set to old B) and E (zeroed). Flags NOT set (no FI).
# 8 steps, no RST — counter wraps 7→0 naturally, next fetch starts.
ucode_template[0xD9] = ('istc_inc', [MI|PO, RO|II|PE, BO|MI, AO|RI, BO|AI, AO|EI, SUB|EO|EI, CINV|EO|BI], False)

# PUSH_B: stack[SP] = B; SP-- — push B register without touching A.
ucode_template[0xF1] = ('push_b', [MI|PO, RO|II|PE, SO|MI, STK|SD|BO|RI, RST, RST, RST, RST], False)

# POP_B: B = stack[SP+1]; SP++ — pop into B register without touching A.
ucode_template[0xF2] = ('pop_b', [MI|PO, RO|II|PE, SU, SO|MI, STK|RO|BI, RST, RST, RST], False)

# OCALL N: overlay call — push return address, A = N, jump to address 0
# Step 3: read immediate into A (NO PE — ret adds 1, so push addr_of_imm)
# Step 4-5: push return address (PC = addr of immediate)
# Step 6: E = A (save index), Step 7: PC = A - E = 0 (A unchanged)
# Counter wraps 7→0, next fetch from PC=0 (overlay loader)
ucode_template[0xDF] = ('ocall', [MI|PO, RO|II|PE, PO|MI, RO|AI, SO|MI, STK|SD|PO|RI, AO|EI, SUB|EO|PI], True)

# OUT_IMM N: output immediate to display without touching A
ucode_template[0xD1] = ('out_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|OI, RST, RST, RST, RST], True)

# JAL_R: indirect call — push return address, jump to address in A
ucode_template[0xE1] = ('jal_r', [MI|PO, RO|II|PE, SO|MI, STK|SD|PO|RI, AO|PI, RST, RST, RST], False)

# ADC: A = A + B + CF — add with carry (flag-dependent: CINV when CF=1)
# Base template (CF=0): normal ADD. initUCode patches CF=1 to add CINV.
ucode_template[0xC1] = ('adc', [MI|PO, RO|II|PE, BO|EI, EO|AI|FI, RST, RST, RST, RST], False)

# SBC: A = A - B - !CF — subtract with borrow (flag-dependent: CINV when CF=0)
# Base template (CF=0): SUB+CINV (borrow). initUCode patches CF=1 to normal SUB.
ucode_template[0xC2] = ('sbc', [MI|PO, RO|II|PE, BO|EI, SUB|CINV|EO|AI|FI, RST, RST, RST, RST], False)

# TST N: test bits — sets ZF based on A AND immediate, does NOT modify A
# Loads immediate into E, computes AND for flags only (no AI)
ucode_template[0xFF] = ('tst', [MI|PO, RO|II|PE, PO|MI, PE|RO|EI, AND|FI, RST, RST, RST], True)

# DDRB_IMM N: write immediate to DDRB (VIA register 2), preserves all registers
# Same pattern as OUT_IMM but targets VIA DDRB via E0|U1 instead of OI.
# Immediate goes RAM→bus→VIA in one step. 4 non-VIA steps between consecutive
# writes provide settling time that prevents the DDRA corruption bug
# (caused by data bus transition bleeding into RS0 during rapid exw 0 2 sequences).
ucode_template[0xE2] = ('ddrb_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|E0|U1, RST, RST, RST, RST], True)

# ORB_IMM N: write immediate to ORB (VIA register 0), preserves all registers
ucode_template[0xF0] = ('orb_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|E0, RST, RST, RST, RST], True)

# ORA_IMM N: write immediate to ORA (VIA register 1), preserves all registers
# Key for tone generation: toggle PA1 (piezo) without clobbering A (delay counter)
ucode_template[0xE6] = ('ora_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|E0|U0, RST, RST, RST, RST], True)

# DDRA_IMM N: write immediate to DDRA (VIA register 3), preserves all registers
# Safety: clear DDRA after I2C to prevent port A pins stuck as outputs
ucode_template[0xE9] = ('ddra_imm', [MI|PO, RO|II|PE, PO|MI, PE|RO|E0|U0|U1, RST, RST, RST, RST], True)

# SWAP: swap A and B (using stack as scratch)
# Step 2: MAR=SP, Step 3: push A (SP--), Step 4: A=B, Step 5: SP++, Step 6: MAR=SP, Step 7: B=pop
# Uses all 8 steps (no RST needed — counter wraps naturally)
ucode_template[0xEE] = ('swap', [MI|PO, RO|II|PE, SO|MI, STK|SD|AO|RI, BO|AI, SU, SO|MI, STK|RO|BI], False)

def checkUCode():
    for op, code in ucode_template.items():
        if len(code) < 3 or len(code[1]) != 8:
            print("Error:", str(op), len(code), len(code[1]))

instruction_decode = {y[0]:x for x,y in ucode_template.items()}

#TODO
ucode_template[instruction_decode['stor $pc, [$sp]']][1][4:6] = [PO|MI, RO|register_map[5][1]]

ucode = list(range(16)) #flag instruction step
def initUCode():

    FLAGS_IRQ00IRQ10Z0C0 = 0
    FLAGS_IRQ00IRQ10Z0C1 = 1
    FLAGS_IRQ00IRQ10Z1C0 = 2
    FLAGS_IRQ00IRQ10Z1C1 = 3
    FLAGS_IRQ01IRQ10Z0C0 = 4
    FLAGS_IRQ01IRQ10Z0C1 = 5
    FLAGS_IRQ01IRQ10Z1C0 = 6
    FLAGS_IRQ01IRQ10Z1C1 = 7
    FLAGS_IRQ00IRQ11Z0C0 = 8
    FLAGS_IRQ00IRQ11Z0C1 = 9
    FLAGS_IRQ00IRQ11Z1C0 = 10
    FLAGS_IRQ00IRQ11Z1C1 = 11
    FLAGS_IRQ01IRQ11Z0C0 = 12
    FLAGS_IRQ01IRQ11Z0C1 = 13
    FLAGS_IRQ01IRQ11Z1C0 = 14
    FLAGS_IRQ01IRQ11Z1C1 = 15

    #print(instruction_decode.keys())

    J0 = instruction_decode['je0']#je0 = move $sp imm
    J1 = instruction_decode['je1']#je1 = move $pc imm
    JC = instruction_decode['jcf']#jcf = move $spp imm
    JZ = instruction_decode['jzf']#jzf = move $imm imm
    JNC = instruction_decode['jnc']
    JNZ = instruction_decode['jnz']
    SETZ_OP = instruction_decode['setz']
    SETNZ_OP = instruction_decode['setnz']
    SETC_OP = instruction_decode['setc']
    SETNC_OP = instruction_decode['setnc']
    ADC_OP = instruction_decode['adc']
    SBC_OP = instruction_decode['sbc']
    # setz/setnz/setc/setnc: "set to 1" = clear A then inc
    _SET1 = [AO|EI, SUB|EO|AI, AO|EI, CINV|EO|AI, RST, RST]
    # "set to 0" = just clear A
    _SET0 = [AO|EI, SUB|EO|AI, RST, RST, RST, RST]

    #ZF = 0, CF = 0, IRQ0 = 0, IRQ1 = 0
    ucode[FLAGS_IRQ00IRQ10Z0C0] = deepcopy(ucode_template)

    #ZF = 0, CF = 0, IRQ0 = 0, IRQ1 = 1
    ucode[FLAGS_IRQ00IRQ11Z0C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ11Z0C0][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 0, CF = 0, IRQ0 = 1, IRQ1 = 0
    ucode[FLAGS_IRQ01IRQ10Z0C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ10Z0C0][J0][1][2:4] = [PO|MI, RO|PI];

    #ZF = 0, CF = 0, IRQ0 = 1, IRQ1 = 1
    ucode[FLAGS_IRQ01IRQ11Z0C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ11Z0C0][J0][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z0C0][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 0, CF = 1, IRQ0 = 0, IRQ1 = 0
    ucode[FLAGS_IRQ00IRQ10Z0C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ10Z0C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ10Z0C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ00IRQ10Z0C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ00IRQ10Z0C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ00IRQ10Z0C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ00IRQ10Z0C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)

    #ZF = 0, CF = 1, IRQ0 = 0, IRQ1 = 1
    ucode[FLAGS_IRQ00IRQ11Z0C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ11Z0C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ11Z0C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ00IRQ11Z0C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ00IRQ11Z0C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ00IRQ11Z0C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ00IRQ11Z0C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ00IRQ11Z0C1][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 0, CF = 1, IRQ0 = 1, IRQ1 = 0
    ucode[FLAGS_IRQ01IRQ10Z0C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ10Z0C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ10Z0C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ01IRQ10Z0C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ01IRQ10Z0C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ01IRQ10Z0C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ01IRQ10Z0C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ01IRQ10Z0C1][J0][1][2:4] = [PO|MI, RO|PI];

    #ZF = 0, CF = 1, IRQ0 = 1, IRQ1 = 1
    ucode[FLAGS_IRQ01IRQ11Z0C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ11Z0C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z0C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ01IRQ11Z0C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ01IRQ11Z0C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ01IRQ11Z0C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ01IRQ11Z0C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ01IRQ11Z0C1][J0][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z0C1][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 0, IRQ0 = 0, IRQ1 = 0
    ucode[FLAGS_IRQ00IRQ10Z1C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ10Z1C0][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ10Z1C0][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ00IRQ10Z1C0][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ00IRQ10Z1C0][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0

    #ZF = 1, CF = 0, IRQ0 = 0, IRQ1 = 1
    ucode[FLAGS_IRQ00IRQ11Z1C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ11Z1C0][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ11Z1C0][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ00IRQ11Z1C0][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ00IRQ11Z1C0][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ00IRQ11Z1C0][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 0, IRQ0 = 1, IRQ1 = 0
    ucode[FLAGS_IRQ01IRQ10Z1C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ10Z1C0][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ10Z1C0][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ01IRQ10Z1C0][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ01IRQ10Z1C0][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ01IRQ10Z1C0][J0][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 0, IRQ0 = 1, IRQ1 = 1
    ucode[FLAGS_IRQ01IRQ11Z1C0] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ11Z1C0][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z1C0][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ01IRQ11Z1C0][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ01IRQ11Z1C0][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ01IRQ11Z1C0][J0][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z1C0][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 1, IRQ0 = 0, IRQ1 = 0
    ucode[FLAGS_IRQ00IRQ10Z1C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ10Z1C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ10Z1C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ00IRQ10Z1C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ00IRQ10Z1C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ00IRQ10Z1C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ00IRQ10Z1C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ00IRQ10Z1C1][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ10Z1C1][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ00IRQ10Z1C1][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ00IRQ10Z1C1][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0

    #ZF = 1, CF = 1, IRQ0 = 0, IRQ1 = 1
    ucode[FLAGS_IRQ00IRQ11Z1C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ00IRQ11Z1C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ11Z1C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ00IRQ11Z1C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ00IRQ11Z1C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ00IRQ11Z1C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ00IRQ11Z1C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ00IRQ11Z1C1][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ00IRQ11Z1C1][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ00IRQ11Z1C1][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ00IRQ11Z1C1][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ00IRQ11Z1C1][J1][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 1, IRQ0 = 1, IRQ1 = 0
    ucode[FLAGS_IRQ01IRQ10Z1C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ10Z1C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ10Z1C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ01IRQ10Z1C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ01IRQ10Z1C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ01IRQ10Z1C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ01IRQ10Z1C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ01IRQ10Z1C1][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ10Z1C1][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ01IRQ10Z1C1][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ01IRQ10Z1C1][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ01IRQ10Z1C1][J0][1][2:4] = [PO|MI, RO|PI];

    #ZF = 1, CF = 1, IRQ0 = 1, IRQ1 = 1
    ucode[FLAGS_IRQ01IRQ11Z1C1] =  deepcopy(ucode_template)
    ucode[FLAGS_IRQ01IRQ11Z1C1][JC][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z1C1][JNC][1][2:4] = [PE, RST];  # CF=1: skip
    ucode[FLAGS_IRQ01IRQ11Z1C1][SETC_OP][1][2:8] = _SET1  # CF=1: set A=1
    ucode[FLAGS_IRQ01IRQ11Z1C1][SETNC_OP][1][2:8] = _SET0  # CF=1: setnc → A=0
    ucode[FLAGS_IRQ01IRQ11Z1C1][ADC_OP][1][3] = CINV|EO|AI|FI  # CF=1: add with carry
    ucode[FLAGS_IRQ01IRQ11Z1C1][SBC_OP][1][3] = SUB|EO|AI|FI   # CF=1: normal sub (no borrow)
    ucode[FLAGS_IRQ01IRQ11Z1C1][JZ][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z1C1][JNZ][1][2:4] = [PE, RST];  # ZF=1: skip
    ucode[FLAGS_IRQ01IRQ11Z1C1][SETZ_OP][1][2:8] = _SET1  # ZF=1: set A=1
    ucode[FLAGS_IRQ01IRQ11Z1C1][SETNZ_OP][1][2:8] = _SET0  # ZF=1: setnz → A=0
    ucode[FLAGS_IRQ01IRQ11Z1C1][J0][1][2:4] = [PO|MI, RO|PI];
    ucode[FLAGS_IRQ01IRQ11Z1C1][J1][1][2:4] = [PO|MI, RO|PI];


checkUCode()
initUCode()

def byte(value):
    return (value).to_bytes(1, 'big', signed=False)

def write(address, data, out):
    out.seek(address)
    data = data & 255
    out.write(data.to_bytes(1, 'big'))

def generate_microcode():
    #Program data bytes
    print("Generating microcode...")

    with open("microcode.bin", 'wb') as out:
        #Program the 8 high-order bits of microcode into the first 128 bytes of EEPROM
        for address in range(131072):
            flags       = (address & 0b00111100000000000) >> 11
            byte_sel    = (address & 0b11000000000000000) >> 15
            instruction = (address & 0b00000011111111000) >> 3
            step        = (address & 0b00000000000000111)

            if instruction not in ucode_template or len(ucode[flags][instruction][1]) == 0:
                print ("unused op-code: $s"%bin(instruction))
                instruction = instruction_decode['move $a, $a']

            if byte_sel == 0:
                write(address, ucode[flags][instruction][1][step] >> 24, out)
            elif byte_sel == 1:
                write(address, ucode[flags][instruction][1][step] >> 16, out)
            elif byte_sel == 2:
                write(address, ucode[flags][instruction][1][step] >> 8, out)
            elif byte_sel == 3:
                write(address, ucode[flags][instruction][1][step] >> 0, out)
            else:
                write(address, 0, out)

        def get_checked_signals(k, i):
            return [sorted_signals[x] for x in range(i) if k & sorted_signals[x] == sorted_signals[x] and reduce(lambda a, b: a | b, sorted_signals[:x], 0) != k]

        with open("microcode.txt", 'w') as out:
            sorted_signals = sorted(signals.keys(), reverse=True, key=lambda x: (int(bin(x).replace('0b', '').replace('0', ' ').strip().replace(' ', '0')), -1 if any([x & i == x for i in signals.keys() if i != x]) else 1))
            for mnemonic, opcode in sorted(instruction_decode.items()):
                print(mnemonic, format(opcode, '08b'), "[" + ',\t'.join(['|'.join([signals[y] for i, y in enumerate(sorted_signals) if x & y == y and x & reduce(lambda a, b: a | b, get_checked_signals(x, i), 0) != x]) for x in ucode_template[opcode][1]]) + "]", sep='\t', file=out)

        print("done")

def assemble_binary(input_file):
    address_table = dict()
    b = bytes()
    buffer = BytesIO(b)
    written_bytes = 0
    with open(input_file, 'r') as f:
        address = 0
        line_num = 0
        for line in f:
            line_num += 1
            if ";" in line:
                line = line[:line.find(';')]
            line = line.strip()
            if len(line) == 0 or line.startswith(";"):
                continue
            components = line.split(" ")
            curr_address = address
            if ":" in line:
                components = line.split(":")
                value = components[0].strip()
                if value.isnumeric():
                    curr_address = int(value)*2
                else:
                    if value in address_table:
                        #print(value, address_table[value])
                        for location in address_table[value]:
                            buffer.seek(location)
                            buffer.write(byte(curr_address // 2))
                    address_table[value] = curr_address // 2
                    if len(components[1].strip()) == 0:
                        continue
                    address += 2
                components = components[1].strip().split(" ")
            else:
                address += 2
            mnemonic_value = components[0].strip()
            if mnemonic_value == ".data":
                buffer.seek(curr_address)
                data = components[1:]
                for value in data:
                    written_bytes += buffer.write(byte(int(value.strip())))
                    written_bytes += buffer.write(byte(0))
                    address += 2
                continue

            if not mnemonic_value.isnumeric() and mnemonic_value not in instruction_decode:
                print("Error @ line %d: instruction not recognized: '%s'"%(line_num, mnemonic_value))
                sys.exit(1)
            instruction = int(mnemonic_value) if mnemonic_value.isnumeric() else instruction_decode[mnemonic_value]
            if not mnemonic_value.isnumeric() and len(components) == 1 and ucode_template[instruction][2]:
                print("Error @ line [%d] %s : missing parameter for instruction: %s" % (line_num, line, mnemonic_value))
                sys.exit(1)
            elif not mnemonic_value.isnumeric() and len(components) > 1 and not ucode_template[instruction][2]:
                print("Warning @ line [%d] %s : unused parameter for instruction '%s': %s" % (line_num, line, mnemonic_value, components[1]))
            value = components[1].strip() if len(components) > 1 else '0'
            if not value.isnumeric():
                if value in address_table and type(address_table[value]) is not list:
                    value = address_table[value]
                else:
                    if not value in address_table:
                        address_table[value] = list()
                    address_table[value].append(curr_address+1)
                    value = '0'
            argument = byte(int(value))
            buffer.seek(curr_address)
            written_bytes += buffer.write(byte(instruction))
            written_bytes += buffer.write(argument)

    if any([type(x) is list for x in address_table.values()]):
        print("Linking error")
        print([x for x,y in address_table.items() if type(y) is list])
        sys.exit(1)
    print("Used %d bytes (%.1f%%) out of 512 bytes."%(written_bytes, (written_bytes/512*100)))
    return buffer.getvalue()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Assembler for MK1 computer.')
    parser.add_argument('-i', '--input', metavar='input', type=str,
                        help='input file name')
    parser.add_argument('-o', '--output', metavar='output', type=str,
                        help='output binary file name')

    args = parser.parse_args()

    if not args.input:
        generate_microcode()
        sys.exit(0)

    binary = assemble_binary(args.input)

    out_file_name = args.output or args.input[:args.input.rfind('.')]+".bin"

    with open(out_file_name, 'wb') as out:
        out.write(binary)

    print("%s generated (%d bytes)."%(out_file_name, len(binary)))
