_main:
	ldi $d,0
.br_dly1:
	dec
	jnz .br_dly1
	clr $a
	exw 0 0
	exw 0 2
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	clr $a
	exw 0 2
	exrw 2
	ldi $a,0x01
	exw 0 2
	ldi $a,0x03
	exw 0 2
	ldi $a,208
	jal __i2c_sb
	ldi $a,14
	jal __i2c_sb
	ldi $a,0
	jal __i2c_sb
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	clr $a
	exw 0 2
	out_imm 1
	exw 0 2
	hlt
__i2c_sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.isb2:
	mov $b,$a
	tst 0x80
	jnz .isbh3
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	ldi $a,0x03
	exw 0 2
	j .isbn4
.isbh3:
	ldi $a,0x02
	exw 0 2
	ldi $a,0x00
	exw 0 2
	ldi $a,0x02
	exw 0 2
.isbn4:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .isb2
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
	push $a
	ldi $a,0x02
	exw 0 2
	pop $a
	ret
