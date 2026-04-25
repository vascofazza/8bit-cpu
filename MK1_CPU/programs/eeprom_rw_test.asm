; EEPROM write+read test: write 0xA5 to address 0x0000, read back
; Uses known-good I2C patterns (NOP settling from verified scan code)
; AT24C32 at address 0x57 (write=0xAE, read=0xAF)
_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3

	; === WRITE: START + 0xAE + 0x00 + 0x00 + 0xA5 + STOP ===
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xAE
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	ldi $a,0xA5
	jal __i2c_sb
	jal __i2c_sp

	; Wait for write cycle (~10ms = ~1260 cycles at 126kHz)
	ldi $d,10
.wr_wait:
	ldi $a,0
.wr_inner:
	dec
	jnz .wr_inner
	mov $d,$a
	dec
	mov $a,$d
	jnz .wr_wait

	; === READ: set address pointer, restart, read byte ===
	; START + 0xAE + 0x00 + 0x00 + STOP (set address)
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xAE
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	jal __i2c_sp

	; START + 0xAF (read mode)
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a,0xAF
	jal __i2c_sb

	; Read 8 bits using scan-proven pattern (with NOPs)
	ddrb_imm 0x02    ; SDA released (input), SCL LOW
	ldi $b,0          ; B = received byte
	ldi $c,8          ; C = bit counter

.rd_bit:
	; Shift B left
	mov $b,$a
	sll
	mov $a,$b
	; SCL HIGH (release both)
	ddrb_imm 0x00
	nop
	nop
	nop
	nop
	nop
	; Read SDA
	exrw 0
	tst 0x01
	jz .rd_zero
	; SDA=1: set bit 0
	mov $b,$a
	ori 0x01,$a
	mov $a,$b
.rd_zero:
	; SCL LOW
	ddrb_imm 0x02
	; Decrement counter
	mov $c,$a
	dec
	mov $a,$c
	jnz .rd_bit

	; NACK (don't acknowledge — single byte read)
	ddrb_imm 0x00    ; SCL HIGH, SDA released = NACK
	nop
	nop
	nop
	nop
	nop
	ddrb_imm 0x02    ; SCL LOW

	; STOP
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00

	; Output result
	mov $b,$a
	out               ; should be 0xA5 (165)
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
	exrw 0
	ddrb_imm 0x02
	ret

__i2c_sp:
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
	ret
