; Count between TWO rising edges (guaranteed full cycle)
; Uses B as edge counter
	ldi $d, 0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	exw 0 2
	
	; Sync: wait for LOW
.s1:
	exrw 1
	tst 0x01
	jz .s2
	j .s1
.s2:
	; Wait for rising edge (first edge)
	exrw 1
	tst 0x01
	jnz .count_start
	j .s2

.count_start:
	ldi $c, 0
	ldi $d, 0
	ldi $b, 1		; B = edges remaining (detect 1 more rising = full cycle)

	; Wait for LOW (end of first HIGH phase)
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
	; In LOW phase — count until next HIGH (second rising edge)
.wait_hi:
	exrw 1
	tst 0x01
	jnz .done		; Second rising edge = full cycle complete
	mov $d, $a
	inc
	mov $a, $d
	jnz .wait_hi
	mov $c, $a
	inc
	mov $a, $c
	j .wait_hi

.done:
	mov $c, $a
	out
	clr $a
	exw 0 2
	hlt
