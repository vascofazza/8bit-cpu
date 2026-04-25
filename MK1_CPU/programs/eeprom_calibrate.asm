; Program 1: Calibrate delay, store D/4 in data[0]
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0			; ORB = 0
	exw 0 2			; DDRB = 0
	exw 0 3			; DDRA = 0 (ensure PA0 is input for SQW)
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xD0
	jal __i2c_sb
	ldi $a, 0x0E
	jal __i2c_sb
	clr $a
	jal __i2c_sb
	jal __i2c_sp
.s1:
	exrw 1
	tst 0x01
	jz .s2
	j .s1
.s2:
	exrw 1
	tst 0x01
	jnz .cal
	j .s2
.cal:
	ldi $b, 0
.cal_hi:
	jal __d256
	mov $b, $a
	inc
	mov $a, $b
	exrw 1
	tst 0x01
	jz .cal_lo
	j .cal_hi
.cal_lo:
	jal __d256
	mov $b, $a
	inc
	mov $a, $b
	exrw 1
	tst 0x01
	jnz .cal_done
	j .cal_lo
.cal_done:
	mov $b, $a
	slr
	slr
	ldi $b, 0
	ideref
	out
	clr $a
	exw 0 2
	hlt
__d256:
	clr $a
.d256:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	dec
	jnz .d256
	ret
__i2c_sb:
	mov $a, $b
	ldi $a, 8
	mov $a, $c
.isb:
	mov $b, $a
	tst 0x80
	jnz .isbh
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	j .isbn
.isbh:
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	ldi $a, 0x02
	exw 0 2
.isbn:
	mov $b, $a
	sll
	mov $a, $b
	mov $c, $a
	dec
	mov $a, $c
	jnz .isb
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	exrw 0
	push $a
	ldi $a, 0x02
	exw 0 2
	pop $a
	ret
__i2c_sp:
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2
	ret
	section data
	byte 0			; [0] D/4
	byte 0			; [1] pass count
	byte 0			; [2] addr_lo (param)
	byte 0			; [3] value (param)
	byte 0			; [4-9] reserved
	byte 0
	byte 0
	byte 0
	byte 0
	byte 0
	byte 42			; [10] test pattern 1
	byte 0x20
	byte 255		; [12] test pattern 2
	byte 0x21
	byte 170		; [14] test pattern 3
	byte 0x22
	byte 85			; [16] test pattern 4
	byte 0x23
	byte 99			; [18] test pattern 5
	byte 0x24
