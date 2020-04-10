from copy import deepcopy
import argparse
from io import BytesIO
import sys

_VERSION = 2.0

HLT = 0b10000000000000000000000000000000  # Halt clock
STK = 0b01000000000000000000010000000000  # Memory Stack address space
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
IO  = 0b00000000000000010000000000000000  # Instruction register out
SUB = 0b00000000000000001000000000000000  # ALU subtract mode
OR  = 0b00000000000000000100000000000000  # ALU OR mode
AND = 0b00000000000000001100000000000000  # ALU AND mode
SHF = 0b00000000000000000010000000000000  # REG A SHIFT mode
ROT = 0b00000000000000001010000000000000  # REG A ROTATE mode
RGT = 0b00000000000000000110000000000000  # Right SHIFT or ROTATE
NOT = 0b00000000000000001110000000000000  # ALU NOT mode
FI  = 0b00000000000000000001000000000000  # Flags in
SU  = 0b00000000000000000000100000000000  # StackPointer count UP
SD  = 0b00000000000000000000010000000000  # StackPointer count DOWN
U0  = 0b00000000000000000000001000000000  # X-USR sig 0
U1  = 0b00000000000000000000000100000000  # X-USR sig 1
E0  = 0b00000000000000000000000010000000  # X-Enable 0
E1  = 0b00000000000000000000000001000000  # X-Enable 1
HL  = 0b00000000000000000000000000100000  # HL address mode
RST = 0b00000000000000000000000000000001  # Reset step counter

ucode_template = {
    0b000000 : ('noop', [MI|CO, RO|II,  HL|RO|II|CE,  0,              0,           0,    -1, -1], False),
    0b000001 : ('hlt',  [MI|CO, RO|II,  HL|RO|II|CE,  HLT,            0,           0,    -1, -1], False),

    0b000010 : ('add',  [MI|CO, RO|II,  HL|RO|II|CE,  EO|AI|FI,       0,           0,    -1, -1], False),
    0b000011 : ('addi', [MI|CO, RO|II,  HL|RO|II|CE,  BI|IO,          EO|AI|FI,    0,    -1, -1], True ), #x
    0b000100 : ('sub',  [MI|CO, RO|II,  HL|RO|II|CE,  EO|AI|SU|FI,    0,           0,    -1, -1], False),
    0b000101 : ('subi', [MI|CO, RO|II,  HL|RO|II|CE,  BI|IO,          EO|SU|AI|FI, 0,    -1, -1], True ), #x
    0b000110 : ('and',  [MI|CO, RO|II,  HL|RO|II|CE,  EO|AI|AND|FI,   0,           0,    -1, -1], False),
    0b000111 : ('andi', [MI|CO, RO|II,  HL|RO|II|CE,  BI|IO,          EO|AND|AI|FI,0,    -1, -1], True ), #x
    0b001000 : ('or',   [MI|CO, RO|II,  HL|RO|II|CE,  EO|AI|OR|FI,    0,           0,    -1, -1], False),
    0b001001 : ('ori',  [MI|CO, RO|II,  HL|RO|II|CE,  BI|IO,          EO|OR|AI|FI, 0,    -1, -1], True ), #x

    0b001010 : ('sll',  [MI|CO, RO|II,  HL|RO|II|CE,  SHF|AI,         0,           0,    -1, -1], False),
    0b001011 : ('slr',  [MI|CO, RO|II,  HL|RO|II|CE,  SHF|RGT|AI,     0,           0,    -1, -1], False),
    0b001100 : ('rll',  [MI|CO, RO|II,  HL|RO|II|CE,  ROT|AI,         0,           0,    -1, -1], False),
    0b001101 : ('rlr',  [MI|CO, RO|II,  HL|RO|II|CE,  ROT|RGT|AI,     0,           0,    -1, -1], False),

    0b010000 : ('lda',  [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          AI|RO,       0,    -1, -1], True ), #&x
    0b010001 : ('ldai', [MI|CO, RO|II,  HL|RO|II|CE,  IO|AI,          0,           0,    -1, -1], True ), #x
    0b010010 : ('ldb',  [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          BI|RO,       0,    -1, -1], True ), #&x
    0b010011 : ('ldbi', [MI|CO, RO|II,  HL|RO|II|CE,  IO|BI,          0,           0,    -1, -1], True ), #x
    0b010100 : ('ldasp',[MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          AI|RO|STK,   0,    -1, -1], False),
    0b010101 : ('ldbsp',[MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          BI|RO|STK,   0,    -1, -1], False),
    0b010110 : ('ldspi',[MI|CO, RO|II,  HL|RO|II|CE,  IO|SI,          0,           0,    -1, -1], True ), #x
    0b111000 : ('lda$', [MI|CO, RO|II,  HL|RO|II|CE,  AO|MI,          AI|RO,       0,    -1, -1], False),
    0b111001 : ('ldb$', [MI|CO, RO|II,  HL|RO|II|CE,  BO|MI,          BI|RO,       0,    -1, -1], False),

    0b011001 : ('sta',  [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          AO|RI,       0,    -1, -1], True ), #&x
    0b011010 : ('stb',  [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          BO|RI,       0,    -1, -1], True ), #&x
    0b011011 : ('stsp', [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          SO|STK|RI,   0,    -1, -1], True ), #&x
    0b011100 : ('stasp',[MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          AO|STK|RI,   0,    -1, -1], False),
    0b011101 : ('stbsp',[MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          BO|STK|RI,   0,    -1, -1], False),
    0b1000000: ('sta$', [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          RO|MI,       AO|RI,-1, -1], True ), #data in regA goes to address @ mem[x]
    0b1000001: ('stb$', [MI|CO, RO|II,  HL|RO|II|CE,  IO|MI,          RO|MI,       BO|RI,-1, -1], True ), #data in regB goes to address @ mem[x]

    0b110000 : ('mvab', [MI|CO, RO|II,  HL|RO|II|CE,  BI|AO,          0,           0,    -1, -1], False),
    0b110001 : ('mvba', [MI|CO, RO|II,  HL|RO|II|CE,  BO|AI,          0,           0,    -1, -1], False),
    0b110010 : ('mvsa', [MI|CO, RO|II,  HL|RO|II|CE,  SO|AI,          0,           0,    -1, -1], False),
    0b110011 : ('mvas', [MI|CO, RO|II,  HL|RO|II|CE,  AO|SI,          0,           0,    -1, -1], False),
    0b110100 : ('mvsb', [MI|CO, RO|II,  HL|RO|II|CE,  SO|BI,          0,           0,    -1, -1], False),
    0b110101 : ('mvbs', [MI|CO, RO|II,  HL|RO|II|CE,  BO|SI,          0,           0,    -1, -1], False),

    0b100000 : ('j',    [MI|CO, RO|II,  HL|RO|II|CE,  IO|J,           0,           0,    -1, -1], True ), #&x
    0b100001 : ('jal',  [MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          STK|CO|RI,   J|IO, -1, -1], True ), #&x
    0b100010 : ('jsp',  [MI|CO, RO|II,  HL|RO|II|CE,  SO|MI,          RO|STK|J,    0,    -1, -1], False),
    0b100011 : ('bez',  [MI|CO, RO|II,  HL|RO|II|CE,  0,              0,           0,    -1, -1], True ), #&x
    0b100100 : ('bcf',  [MI|CO, RO|II,  HL|RO|II|CE,  0,              0,           0,    -1, -1], True ), #&x
    0b111111 : ('out',  [MI|CO, RO|II,  HL|RO|II|CE,  AO|OI,          0,           0,    -1, -1], False)
    }

def checkUCode():
    for op, code in ucode_template.items():
        if len(code) < 3 or len(code[1]) < 8:
            print("Error: "+op)
            break

instruction_decode = {y[0]:x for x,y in ucode_template.items()}

FLAGS_Z0C0 = 0
FLAGS_Z0C1 = 1
FLAGS_Z1C0 = 2
FLAGS_Z1C1 = 3

JZ = instruction_decode['bez']#0b100010
JC = instruction_decode['bcf']#0b100011

ucode = list(range(4)) #flag instruction step
def initUCode():
    #ZF = 0, CF = 0
    ucode[FLAGS_Z0C0] = deepcopy(ucode_template)

    #ZF = 0, CF = 1
    ucode[FLAGS_Z0C1] =  deepcopy(ucode_template)
    ucode[FLAGS_Z0C1][JC][1][3] = IO|J;

    #ZF = 1, CF = 0
    ucode[FLAGS_Z1C0] = deepcopy(ucode_template)
    ucode[FLAGS_Z1C0][JZ][1][3] = IO|J;

    # ZF = 1, CF = 1
    ucode[FLAGS_Z1C1] = deepcopy(ucode_template)
    ucode[FLAGS_Z1C1][JC][1][3] = IO|J;
    ucode[FLAGS_Z1C1][JZ][1][3] = IO|J;

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
        for address in range(65536):
            flags       = (address & 0b0001100000000000) >> 11
            byte_sel    = (address & 0b1110000000000000) >> 13
            instruction = (address & 0b0000011111111000) >> 3
            step        = (address & 0b0000000000000111)

            if instruction not in ucode_template or len(ucode[flags][instruction][1]) == 0:
                instruction = instruction_decode['noop']

            if byte_sel == 1:
                write(address, ucode[flags][instruction][1][step] >> 16, out)
            elif byte_sel == 2:
                write(address, ucode[flags][instruction][1][step] >> 8, out)
            elif byte_sel == 4:
                write(address, ucode[flags][instruction][1][step] >> 0, out)
            else:
                write(address, 0, out)

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
