; Write 0x42 to addr 0x0000, check ACK after each byte
; Outputs ACK status for each of 4 bytes: 10=ACK, 11=NACK (etc.)
; Then outputs 99 when done. With bus recovery.

; VIA init + bus recovery
ldi $d, 0
.dly:
ddrb_imm 0x00
ddrb_imm 0x02
dec
jnz .dly
clr $a
exw 0 0
ddrb_imm 0x00
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00

; START
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
; Byte 1: 0xAE (device addr write)
ldi $a, 0xAE
jal __sb
tst 0x01
jnz .n1
out_imm 10      ; ACK
j .b2
.n1:
out_imm 11      ; NACK
.b2:
; Byte 2: 0x00 (addr high)
clr $a
jal __sb
tst 0x01
jnz .n2
out_imm 20
j .b3
.n2:
out_imm 21
.b3:
; Byte 3: 0x00 (addr low)
clr $a
jal __sb
tst 0x01
jnz .n3
out_imm 30
j .b4
.n3:
out_imm 31
.b4:
; Byte 4: 0x42 (data)
ldi $a, 0x42
jal __sb
tst 0x01
jnz .n4
out_imm 40
j .stop
.n4:
out_imm 41
.stop:
; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
out_imm 99
hlt

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
