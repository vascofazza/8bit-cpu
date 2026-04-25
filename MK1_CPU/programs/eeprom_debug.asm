; EEPROM write debug: outputs NACK bitmask then 4 read bytes
; Bit N of bitmask = 1 if byte N NACKed. 0 = all OK.
; After __sb, A has exrw 0 result (bit 0 = ACK).
; We shift D left and OR in the ACK bit.

; VIA init
ldi $d, 0
.dly:
dec
jnz .dly
clr $a
exw 0 0
ddrb_imm 0x00
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Pre-write ACK poll
.pre:
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
tst 0x01
jnz .pre
; WRITE with bitmask accumulation
ldi $d, 0
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
clr $a
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
clr $a
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
ldi $a, 0xDE
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
ldi $a, 0xAD
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
ldi $a, 0xBE
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
ldi $a, 0xEF
jal __sb
andi 0x01, $a
push $a
mov $d, $a
sll
pop $b
or $b, $a
mov $a, $d
; STOP
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Output bitmask
mov $d, $a
out
; Post-write ACK poll
.post:
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAE
jal __sb
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
tst 0x01
jnz .post
; READ
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
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __sb
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x03
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x03
jal __rb
mov $d,$a
out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x03
jal __rb
mov $d,$a
out
ddrb_imm 0x00
ddrb_imm 0x02
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
