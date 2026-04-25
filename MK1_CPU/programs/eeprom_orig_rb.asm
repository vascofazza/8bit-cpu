; EEPROM read using ORIGINAL __i2c_rb (C=counter, D=accumulator)
; Tests if the original code works now that E1 is disconnected from GAL
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; SET ADDR 0x0000
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
; READ
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __i2c_sb
jal __i2c_rb_orig
; NACK + STOP
ddrb_imm 0x00
ddrb_imm 0x02
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
mov $d,$a
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
; ORIGINAL __i2c_rb: D=accumulator, C=counter
__i2c_rb_orig:
	ldi $d,0
	ldi $c,8
.rb:
	ddrb_imm 0x00
	exrw 0
	andi 0x01,$a
	mov $a,$b
	mov $d,$a
	sll
	or $b,$a
	mov $a,$d
	ddrb_imm 0x02
	mov $c,$a
	dec
	mov $a,$c
	jnz .rb
	ret
