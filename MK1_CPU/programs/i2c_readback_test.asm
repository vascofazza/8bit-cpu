; Write DS3231 reg 0x0E = 0x00, then read it back
_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3
	; WRITE: START + 0xD0 + 0x0E + 0x00 + STOP
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xD0
	jal __i2c_sb
	ldi $a,0x0E
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	jal __i2c_sp
	; READ: START + 0xD0 + 0x0E (set addr) + RESTART + 0xD1 + read byte + NACK + STOP
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xD0
	jal __i2c_sb
	ldi $a,0x0E
	jal __i2c_sb
	jal __i2c_sp
	; Restart for read
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xD1
	jal __i2c_sb
	; Read byte (8 bits, release SDA, clock in)
	ddrb_imm 0x02    ; SDA released (input), SCL LOW
	ldi $c,8
	ldi $b,0
.rd:
	mov $b,$a
	sll
	mov $a,$b
	ddrb_imm 0x00    ; SCL HIGH
	exrw 0            ; read PB0 (SDA)
	tst 0x01
	jz .rz
	mov $b,$a
	ori 0x01,$a
	mov $a,$b
.rz:
	ddrb_imm 0x02    ; SCL LOW
	mov $c,$a
	dec
	mov $a,$c
	jnz .rd
	; NACK (don't acknowledge)
	ddrb_imm 0x00    ; SCL HIGH (SDA released = NACK)
	ddrb_imm 0x02    ; SCL LOW
	; STOP
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
	; Output the byte we read
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
__i2c_sp:
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
	ret
