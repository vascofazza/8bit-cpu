; Test: send 256 zeros with D+B saved/restored around __sb
; B=1 (outer counter, single pass). Expected: val=1
ldi $d, 0
.dly:
dec
jnz .dly
clr $a
exw 0 0
ddrb_imm 0x00
clr $a
exw 0 3
ldi $c, 9
.rcv:
ddrb_imm 0x00
ddrb_imm 0x02
mov $c, $a
dec
mov $a, $c
jnz .rcv
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0x78
jal __sb
ldi $a, 0x40
jal __sb
ldi $b, 4
.clr_out:
ldi $d, 0
.clr_in:
mov $d, $a
push $a
mov $b, $a
push $a
clr $a
jal __sb
pop $a
mov $a, $b
pop $a
mov $a, $d
mov $d, $a
inc
mov $a, $d
jnz .clr_in
mov $b, $a
dec
mov $a, $b
jnz .clr_out
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
out_imm 1
hlt

__sb:
	mov $a, $b
	ldi $a, 8
	mov $a, $c
.isb:
	mov $b, $a
	tst 0x80
	jnz .isbh
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x03
	j .isbn
.isbh:
	ddrb_imm 0x02
	ddrb_imm 0x00
	ddrb_imm 0x02
.isbn:
	mov $b, $a
	sll
	mov $a, $b
	mov $c, $a
	dec
	mov $a, $c
	jnz .isb
	ddrb_imm 0x02
	ddrb_imm 0x00
	exrw 0
	ddrb_imm 0x02
	ret
