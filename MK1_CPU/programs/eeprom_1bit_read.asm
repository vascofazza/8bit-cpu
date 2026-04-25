; Write address pointer to 0x0000, then read 1 bit of data
nop
nop
nop
ldi $a, 0x00
exw 0 0
ldi $a, 0x00
exw 0 2
exw 0 3
; Set address: START + 0xAE + 0x00 + 0x00 + STOP
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAE
jal __i2c_sb
clr $a
jal __i2c_sb
clr $a
jal __i2c_sb
; STOP
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2
; Read: START + 0xAF
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAF
jal __i2c_sb
; Now slave should drive SDA with MSB of data
; Release SDA, clock SCL HIGH, read SDA — exact scan ACK pattern
ldi $a, 0x02
exw 0 2
nop
nop
nop
nop
nop
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
exrw 0           ; read PB0 = SDA = MSB of data
push $a
; SCL LOW
ldi $a, 0x02
exw 0 2
; NACK + STOP
ldi $a, 0x00
exw 0 2
nop
nop
ldi $a, 0x02
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2
; Output the bit we read
pop $a
tst 0x01
jnz .one
out_imm 0        ; SDA=0 (MSB=0)
hlt
.one:
out_imm 1        ; SDA=1 (MSB=1)
hlt
__i2c_sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.isb:
	mov $b,$a
	tst 0x80
	jnz .isbh
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	ldi $a,0x03
	exw 0 2
	j .isbn
.isbh:
	ldi $a,0x02
	exw 0 2
	ldi $a,0x00
	exw 0 2
	ldi $a,0x02
	exw 0 2
.isbn:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .isb
	ldi $a,0x02
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	ldi $a,0x00
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	exrw 0
	ldi $a,0x02
	exw 0 2
	ret
