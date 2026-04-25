; Test VIA with GAL - no delay_cal, no SQW
; Just verify we can write/read DDRB and ORB
_main:
	; VIA init delay (RC reset settle)
	ldi $d,0
.dly:
	dec
	jnz .dly
	; Clear VIA state
	clr $a
	exw 0 0         ; ORB = 0
	ddrb_imm 0x00   ; DDRB = 0
	exw 0 3          ; DDRA = 0
	; Test: set DDRB to 0x03 (PB0+PB1 output) then read it back
	ddrb_imm 0x03    ; write DDRB = 3
	exrw 2           ; read DDRB back into A
	out               ; output A — should be 3 if VIA works
	hlt
