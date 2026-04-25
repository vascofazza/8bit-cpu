; Test I2C through GAL: enable DS3231 SQW, verify by reading PA0
_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3
	; I2C: write DS3231 register 0x0E = 0x00 (enable SQW 1Hz)
	exrw 2           ; read DDRB (required before START)
	ddrb_imm 0x01    ; START: SDA LOW
	ddrb_imm 0x03    ; SCL LOW
	ldi $a,0xD0      ; DS3231 write address
	jal __i2c_sb
	ldi $a,0x0E      ; control register
	jal __i2c_sb
	clr $a            ; value = 0x00 (SQW enabled, 1Hz)
	jal __i2c_sb
	jal __i2c_sp      ; STOP
	; Read SQW state via PA0
	clr $a
	exw 0 3           ; DDRA = 0 (PA0 input)
	exrw 1            ; read IRA — bit 0 = SQW
	out                ; output SQW state
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
