; Read-only EEPROM test: just read addr 0x0000 and output
; No write. Uses D as bit counter (not C).
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; Set addr: START + 0xAE + 0x00 + 0x00 + STOP
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
; Read: START + 0xAF
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xAF
jal __sb
; Read 8 bits
ddrb_imm 0x02    ; SDA in, SCL LOW
ldi $b, 0         ; byte accumulator
ldi $d, 8         ; counter
.rd:
mov $b,$a
sll
mov $a,$b
; SCL HIGH — use exw pattern for maximum settling
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
; Read
exrw 0
tst 0x01
jz .rz
mov $b,$a
ori 0x01,$a
mov $a,$b
.rz:
; SCL LOW
ldi $a, 0x02
exw 0 2
; Counter
mov $d,$a
dec
mov $a,$d
jnz .rd
; NACK + STOP
ldi $a, 0x00
exw 0 2
nop
nop
ldi $a, 0x02
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2
; Output
mov $b,$a
out
hlt
__sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.is:
	mov $b,$a
	tst 0x80
	jnz .ih
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	ldi $a,0x03
	exw 0 2
	j .in
.ih:
	ldi $a,0x02
	exw 0 2
	ldi $a,0x00
	exw 0 2
	ldi $a,0x02
	exw 0 2
.in:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .is
	ldi $a,0x02
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	ldi $a,0x00
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	exrw 0
	ldi $a,0x02
	exw 0 2
	ret
