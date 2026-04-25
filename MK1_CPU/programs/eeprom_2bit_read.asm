; Minimal EEPROM read test: write 0xA5, read 2 bits back
; Uses ddrb_imm to save bytes
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; WRITE 0xA5 to addr 0x0000
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __i2c_sb
clr $a
jal __i2c_sb
clr $a
jal __i2c_sb
ldi $a, 0xA5
jal __i2c_sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Wait 20ms
ldi $d, 20
.ww:
clr $a
.wi:
dec
jnz .wi
mov $d,$a
dec
mov $a,$d
jnz .ww
; SET ADDRESS to 0x0000
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
; READ: START + 0xAF
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __i2c_sb
; Read bit 7 (MSB) — scan ACK pattern with ddrb_imm
ddrb_imm 0x02
nop
nop
nop
ddrb_imm 0x00
nop
nop
nop
exrw 0
push $a
; SCL LOW
ddrb_imm 0x02
; Read bit 6
ddrb_imm 0x00
nop
nop
nop
exrw 0
push $a
ddrb_imm 0x02
; NACK + STOP
ddrb_imm 0x00
nop
ddrb_imm 0x02
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Output bit 7
pop $a       ; bit 6 (discard)
pop $a       ; bit 7
tst 0x01
jnz .msb1
out_imm 0
j .end
.msb1:
out_imm 1
.end:
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
