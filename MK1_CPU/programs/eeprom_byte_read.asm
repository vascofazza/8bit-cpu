; EEPROM byte read: read byte at addr 0x0000, output it
; Address already set by previous eeprom_2bit_read write
; Just do: START + 0xAE + 0x00 + 0x00 + STOP, START + 0xAF + read 8 bits
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; Set addr pointer: START + 0xAE + 0x00 + 0x00 + STOP
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __i2c_sb
clr $a
jal __i2c_sb
clr $a
jal __i2c_sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Read: START + 0xAF + 8 bits + NACK + STOP
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __i2c_sb
; Read 8 bits into B. Counter in D.
ddrb_imm 0x02    ; SDA released, SCL LOW
ldi $b, 0
ldi $d, 8
.rd:
mov $b,$a
sll
mov $a,$b         ; B <<= 1
ddrb_imm 0x00    ; SCL HIGH
nop
nop
nop
exrw 0            ; A = port B pins
tst 0x01          ; SDA = bit 0
jz .rz
mov $b,$a
ori 0x01,$a
mov $a,$b         ; B |= 1
.rz:
ddrb_imm 0x02    ; SCL LOW
mov $d,$a
dec
mov $a,$d
jnz .rd
; NACK
ddrb_imm 0x00
nop
nop
ddrb_imm 0x02
; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Output byte
mov $b,$a
out
hlt
__i2c_sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.isb:
	mov $b,$a
	tst 0x80
	jnz .isbh
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x03
	j .isbn
.isbh:
	ddrb_imm 0x02
	ddrb_imm 0x00
	ddrb_imm 0x02
.isbn:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .isb
	ddrb_imm 0x02
	ddrb_imm 0x00
	exrw 0
	ddrb_imm 0x02
	ret
