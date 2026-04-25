; Scan for EEPROM at 0x57 using ddrb_imm-based __sb
; Compare with ldi+exw scan to isolate if ddrb_imm is broken by GAL
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; START
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
; Send 0xAE using ddrb_imm __sb
ldi $a, 0xAE
jal __sb
; ACK check (same scan-proven pattern)
ddrb_imm 0x02
nop
nop
nop
nop
nop
ddrb_imm 0x00
nop
nop
nop
nop
nop
exrw 0
push $a
ddrb_imm 0x02
; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Check
pop $a
tst 0x01
jnz .nack
out_imm 1
hlt
.nack:
out_imm 0
hlt
; ddrb_imm-based send byte (same as compiler generates)
__sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.is:
	mov $b,$a
	tst 0x80
	jnz .ih
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x03
	j .in
.ih:
	ddrb_imm 0x02
	ddrb_imm 0x00
	ddrb_imm 0x02
.in:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .is
	ddrb_imm 0x02
	ddrb_imm 0x00
	exrw 0
	ddrb_imm 0x02
	ret
