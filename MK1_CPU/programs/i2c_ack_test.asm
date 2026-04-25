; Test I2C ACK: send DS3231 address byte, output ACK status
_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3
	; START
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	; Send 0xD0 (DS3231 write addr)
	ldi $a,0xD0
	jal __i2c_sb
	; A now has ACK bit from exrw 0 inside i2c_sb
	; ACK=0 means device responded, ACK=1 means no response
	tst 0x01
	jnz .nack
	out_imm 1        ; ACK received
	j .done
.nack:
	out_imm 0        ; NACK - device not found
.done:
	; STOP
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
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
	; ACK clock
	ddrb_imm 0x02
	ddrb_imm 0x00
	exrw 0            ; read ORB/IRB — bit 0 = SDA (ACK)
	ddrb_imm 0x02
	ret
