; Continuous clock speed display (kHz on 7-seg)
; Measures SQW cycle on PA0, converts to kHz, loops forever
	ldi $d, 0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0		; ORB = 0
	exw 0 2		; DDRB = 0
	exw 0 3		; DDRA = 0 (PA0 input for SQW)

	; Configure DS3231 SQW = 1Hz
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2
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
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2

.measure:
	; Sync: wait for LOW then rising edge
.s1:
	exrw 1
	tst 0x01
	jz .s2
	j .s1
.s2:
	exrw 1
	tst 0x01
	jnz .go
	j .s2

.go:
	; Count full cycle: HIGH phase then LOW phase until next rising edge
	ldi $c, 0
	ldi $d, 0
.wait_lo:
	exrw 1
	tst 0x01
	jz .in_lo
	mov $d, $a
	inc
	mov $a, $d
	jnz .wait_lo
	mov $c, $a
	inc
	mov $a, $c
	j .wait_lo
.in_lo:
.wait_hi:
	exrw 1
	tst 0x01
	jnz .calc
	mov $d, $a
	inc
	mov $a, $d
	jnz .wait_hi
	mov $c, $a
	inc
	mov $a, $c
	j .wait_hi

.calc:
	; C = overflow count for HALF SQW cycle (0.5s).
	; kHz ≈ C * 256 * 13 / 500 ≈ C * 6.66 ≈ C * 7
	; C * 7 = C * 8 - C = (C << 3) - C
	mov $c, $a		; A = C
	mov $a, $d		; D = C (save for subtract)
	sll
	sll
	sll			; A = C * 8
	sub $d, $a		; A = C*8 - C = C*7
	out
	j .measure

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
