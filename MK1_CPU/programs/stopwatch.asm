; Stopwatch: 64-iteration inner loop (clock-agnostic), PA1 buzzer synced to display

.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0
	exw 0 2
	exw 0 3			; DDRA = 0 (essential for SQW + prevents stale state)

	; Configure SQW
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

	; Calibrate: 64-iteration inner loop (not 256)
.cal:
	ldi $b, 0
.cal_hi_ovf:
	ldi $a, 64
.cal_hi_inner:
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
	jnz .cal_hi_inner
	mov $b, $a
	inc
	mov $a, $b
	exrw 1
	tst 0x01
	jz .cal_lo
	j .cal_hi_ovf
.cal_lo:
	ldi $a, 64
.cal_lo_inner:
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
	jnz .cal_lo_inner
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
	ideref			; data[0] = D/4

	; Init beep target
	ldi $a, 10
	ldi $b, 1
	ideref			; data[1] = 10 (first beep at tick 10)

	ldi $d, 0
.tick:
	mov $d, $a
	out
	jal beep_check
	jal delay_250ms
	jal delay_250ms
	jal delay_250ms
	jal delay_250ms
	mov $d, $a
	inc
	mov $a, $d
	j .tick

; delay_250ms: D/4 overflows of 64-iteration inner loop (matches calibration)
delay_250ms:
	clr $a
	deref			; A = data[0] = D/4
	mov $a, $b
.d_outer:
	ldi $a, 64
.d_inner:
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
	jnz .d_inner
	mov $b, $a
	dec
	mov $a, $b
	jnz .d_outer
	ret

; beep_check: beep when D matches data[1], then advance target by 10
beep_check:
	clr $a
	exw 0 3			; DDRA = 0
	ldi $a, 1
	deref			; A = data[1] = next beep target
	cmp $d			; target == D?
	jnz .no_beep
	; Beep!
	jal beep
	; Advance target by 10
	ldi $a, 1
	deref			; A = data[1]
	addi 10, $a		; A += 10 (wraps at 256)
	ldi $b, 1
	ideref			; data[1] = new target
.no_beep:
	ret

beep:
	ldi $a, 0x02
	exw 0 3			; DDRA = 0x02 (PA1 output)
	ldi $c, 0
.beep_loop:
	ldi $a, 0x02
	exw 0 1			; PA1 HIGH
	clr $a
	exw 0 1			; PA1 LOW
	mov $c, $a
	dec
	mov $a, $c
	jnz .beep_loop
	clr $a
	exw 0 3			; DDRA = 0
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
	byte 10			; [1] next beep target
