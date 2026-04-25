; Write 0x42 to EEPROM addr 0x0000, wait, read back, output
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
jal __sb
clr $a
jal __sb
clr $a
jal __sb
ldi $a, 0x42
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Wait
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
jal __sb
clr $a
jal __sb
clr $a
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; READ
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __sb
; Read 8 bits: B=byte, D=counter
ddrb_imm 0x02
ldi $b, 0
ldi $d, 8
.rd:
; Shift B left
mov $b,$a
sll
mov $a,$b
; SCL HIGH
ddrb_imm 0x00
nop
nop
nop
; Read SDA
exrw 0
tst 0x01
jz .rz
; Set bit 0
mov $b,$a
ori 0x01,$a
mov $a,$b
.rz:
; SCL LOW
ddrb_imm 0x02
; Counter--
mov $d,$a
dec
mov $a,$d
jnz .rd
; NACK + STOP
ddrb_imm 0x00
nop
nop
ddrb_imm 0x02
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Output
mov $b,$a
out
hlt
__sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.is:
	mov $b,$a
	tst 0x80
	jnz .ih
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x03
	j .in
.ih:
	ddrb_imm 0x02
	ddrb_imm 0x00
	ddrb_imm 0x02
.in:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .is
	ddrb_imm 0x02
	ddrb_imm 0x00
	exrw 0
	ddrb_imm 0x02
	ret
