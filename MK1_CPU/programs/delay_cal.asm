; Self-calibrating delay test
; Phase 1: calibrate (SQW full cycle, 13-cycle loop → C)
; Phase 2: display C, then blink 100/200 with ~2s calibrated delay
; C is passed on stack to delay_ms

	ldi $d, 0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	exw 0 2

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

	; Calibrate: sync to rising edge, count full cycle
.s1:
	exrw 1
	tst 0x01
	jz .s2
	j .s1
.s2:
	exrw 1
	tst 0x01
	jnz .cal_go
	j .s2
.cal_go:
	ldi $c, 0
	ldi $d, 0
.cal_hi:
	exrw 1
	tst 0x01
	jz .cal_lo_start
	mov $d, $a
	inc
	mov $a, $d
	jnz .cal_hi
	mov $c, $a
	inc
	mov $a, $c
	j .cal_hi
.cal_lo_start:
.cal_lo:
	exrw 1
	tst 0x01
	jnz .cal_done
	mov $d, $a
	inc
	mov $a, $d
	jnz .cal_lo
	mov $c, $a
	inc
	mov $a, $c
	j .cal_lo
.cal_done:
	; C = full-cycle overflow count. Push to stack for delay_ms.
	mov $c, $a
	push $a			; stack[SP] = C (stays there permanently)

	; Display C
	out

	; Blink with calibrated delay
.blink:
	out_imm 100
	; delay ~2s = 8 × 250ms
	ldi $d, 8
.d1:
	ldsp 1			; A = C (from stack)
	ldi $b, 250
	jal delay_ms
	mov $d, $a
	dec
	mov $a, $d
	jnz .d1

	out_imm 200
	ldi $d, 8
.d2:
	ldsp 1
	ldi $b, 250
	jal delay_ms
	mov $d, $a
	dec
	mov $a, $d
	jnz .d2

	j .blink

; delay_ms: A = calibration count C, B = ms to delay
; Inner loop must match calibration: same relationship.
; Cal loop = 13 cycles/iter, C overflows in 1s.
; cycles/ms = C * 256 * 13 / 1000 = C * 3.328
; Inner loop at 7 cycles: iters/ms = C * 3.328 / 7 = C * 0.475
; So inner count ≈ C/2 per ms.
; Using C/2: error = (0.475-0.5)/0.475 = 5.3% long. Safe.
delay_ms:
	mov $a, $c		; C = calibration count
.dms_outer:
	mov $c, $a		; A = C
	slr			; A = C/2 = inner count per ms
.dms_inner:
	nop
	nop
	nop
	nop
	dec
	jnz .dms_inner
	mov $b, $a
	dec
	mov $a, $b
	jnz .dms_outer
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
