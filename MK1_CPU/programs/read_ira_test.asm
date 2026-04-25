_main:
	ldi $d,0
.dly:
	dec
	jnz .dly
	clr $a
	exw 0 0
	ddrb_imm 0x00
	exw 0 3
	; Read IRA (register 1) — should return PA pin states
	exrw 1
	out
	hlt
