; EEPROM read using FIXED __i2c_rb (counter in D, accumulator in C)
; Write 0x42 to addr 0x0000, wait, read back
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; WRITE
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __i2c_sb
clr $a
jal __i2c_sb
clr $a
jal __i2c_sb
ldi $a, 0x42
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
; SET ADDR
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
jal __i2c_rb
; NACK
ddrb_imm 0x00
ddrb_imm 0x02
; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Output (D has the byte)
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

; FIXED __i2c_rb: B=accumulator, D=counter (exrw 0 clobbers A+C)
__i2c_rb:
	ldi $b,0
	ldi $d,8
.rb:
	mov $b,$a
	sll
	mov $a,$b
	ddrb_imm 0x00
	exrw 0
	tst 0x01
	jz .rz
	mov $b,$a
	ori 0x01,$a
	mov $a,$b
.rz:
	ddrb_imm 0x02
	mov $d,$a
	dec
	mov $a,$d
	jnz .rb
	mov $b,$d
	ret
