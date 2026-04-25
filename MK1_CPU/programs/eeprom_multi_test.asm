; Write 4 different values to EEPROM addrs 0x0000-0x0003, read all back
; Outputs each byte — expect 0xDE, 0xAD, 0xBE, 0xEF
; With bus recovery + ACK polling (no fixed delay)

; VIA init
ldi $d, 0
.dly:
dec
jnz .dly
clr $a
exw 0 0
ddrb_imm 0x00
; Clean STOP to end any prior transaction
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00

; ACK poll: ensure EEPROM is ready (previous write cycle may be active)
.pre_poll:
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
tst 0x01
jnz .pre_poll

; WRITE 4 bytes starting at 0x0000 (page write)
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
clr $a
jal __sb
clr $a
jal __sb
ldi $a, 0xDE
jal __sb
ldi $a, 0xAD
jal __sb
ldi $a, 0xBE
jal __sb
ldi $a, 0xEF
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00

; ACK poll: send START + 0xAE, check ACK, repeat until ACK
; EEPROM NACKs while write cycle is in progress
.poll:
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
tst 0x01
jnz .poll_nack
; ACK — write complete, send STOP and continue
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
j .read
.poll_nack:
; NACK — send STOP and retry
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
j .poll

.read:
; SET ADDR back to 0x0000
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
clr $a
jal __sb
clr $a
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00

; Sequential READ 4 bytes
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __sb

; Byte 0 — ACK after each to continue sequential read
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x02

; Byte 1
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x02

; Byte 2
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x02

; Byte 3 — NACK (no more bytes)
jal __rb
mov $d,$a
out
ddrb_imm 0x00
ddrb_imm 0x02

; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
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

__rb:
	ldi $b,0
	ldi $d,8
.rb:
	mov $b,$a
	sll
	mov $a,$b
	ddrb_imm 0x00
	exrw 0
	tst 0x01
	jz .rz
	mov $b,$a
	ori 0x01,$a
	mov $a,$b
.rz:
	ddrb_imm 0x02
	mov $d,$a
	dec
	mov $a,$d
	jnz .rb
	mov $b,$d
	ret
