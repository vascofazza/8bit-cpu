_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3
	; Write DDRB = 0xAA, read back
	ldi $a,0xAA
	exw 0 2
	exrw 2
	out
	hlt
