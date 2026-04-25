; EEPROM stress test: 5 patterns, write+delay+read, count passes
; Reads D/4 from data[0] (set by calibration program)
; NO section data — preserves calibration's data[0]
;
; CRITICAL: deref reads data[A], ideref writes data[B]=A

	; VIA init (1.5ms RC settle)
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0			; ORB = 0
	exw 0 2			; DDRB = 0
	exw 0 3			; DDRA = 0 (ensure PA0 input for SQW)

	; Init pass counter
	clr $a
	ldi $b, 1
	ideref			; data[1] = 0

	; Test loop: 5 patterns from data[10..19]
	ldi $d, 10

.test_loop:
	; Load value → data[3], addr_lo → data[2]
	mov $d, $a
	deref			; A = data[D] = value
	ldi $b, 3
	ideref			; data[3] = value
	mov $d, $a
	inc
	deref			; A = data[D+1] = addr_lo
	ldi $b, 2
	ideref			; data[2] = addr_lo
	; Save next index
	mov $d, $a
	addi 2, $a
	push $a

	; Write + delay + read
	jal write_and_read	; D = read value

	; Compare D to expected
	ldi $a, 3
	deref			; A = data[3] = expected
	cmp $d
	jnz .no_match
	; Increment pass count
	ldi $b, 1
	mov $b, $a		; A = 1
	deref			; A = data[1] = pass count
	inc
	ideref			; data[1] = A (B still = 1)
.no_match:
	pop $a
	mov $a, $d
	cmp 20			; 5 tests × 2 = 10 bytes, start at 10
	jnz .test_loop

	; Output pass count
	ldi $a, 1
	deref			; A = data[1]
	out
	clr $a
	exw 0 2			; idle I2C
	hlt

; ════════════════════════════════════════
; write_and_read: write data[3] to EEPROM 0x03:data[2],
;                 delay 15ms, read back. D = result.
; ════════════════════════════════════════
write_and_read:
	; Write: START, 0xAE, 0x03, addr_lo, value, STOP
	jal __i2c_header	; sends START, 0xAE, 0x03, addr_lo
	ldi $a, 3
	deref			; A = data[3] = value
	jal __i2c_sb
	jal __i2c_sp

	; Delay 15ms for write cycle
	ldi $b, 15
	jal delay_Nms

	; Set read address (dummy write): same header, then STOP
	jal __i2c_header
	jal __i2c_sp

	; Current-address read
	jal __i2c_st
	ldi $a, 0xAF
	jal __i2c_sb
	jal __i2c_rb		; D = read byte

	; NACK + STOP via fall-through subroutine
	jal __i2c_nack_sp
	ret

; ════════════════════════════════════════
; Proven I2C subroutines (unchanged from 30/30 test)
; ════════════════════════════════════════

; Shared EEPROM address header: START, 0xAE, 0x03, data[2]=addr_lo
__i2c_header:
	jal __i2c_st
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, 0x03
	jal __i2c_sb
	ldi $a, 2
	deref			; A = data[2] = addr_lo
	jal __i2c_sb
	ret

__i2c_st:
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
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

; NACK then fall through to STOP (same timing as proven inline NACK)
__i2c_nack_sp:
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	nop
	nop
	ldi $a, 0x02
	exw 0 2
__i2c_sp:
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2
	ret

__i2c_rb:
	ldi $d, 0
	ldi $c, 8
.rb:
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	exrw 0
	push $a
	mov $d, $a
	sll
	mov $a, $d
	pop $a
	andi 0x01, $a
	or $d, $a
	mov $a, $d
	ldi $a, 0x02
	exw 0 2
	mov $c, $a
	dec
	mov $a, $c
	jnz .rb
	ret

delay_Nms:
	; B = ms. D/4 overflows of __d256 per ms (proven in ee_test_simple.asm)
.dnms:
	clr $a
	deref			; A = data[0] = D/4
	mov $a, $c		; C = overflow count
.dov:
	jal __d256		; 256 iterations of same 13-cycle loop as calibration
	mov $c, $a
	dec
	mov $a, $c
	jnz .dov
	mov $b, $a
	dec
	mov $a, $b
	jnz .dnms
	ret
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
