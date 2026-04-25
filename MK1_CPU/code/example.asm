	section code
	j _main
	hlt
_max:
	ldsp 3
	mov $a,$b
	ldsp 2
	mov $b,$a
	mov $a,$b
	cmp $b
	jnc .L4
.L3:
	j .L1
.L4:
	mov $b,$a
.L1:
	ret

_count_above:
	; allocate 1 locals on stack
	push_imm 0
	ldsp 4
	mov $a,$d
	ldsp 3
	mov $a,$c
	ldi $a,0
	mov $a,$b
	mov $c,$a
	mov $a,$b
	mov $d,$a
	cmp $b
	jz .L8
	jnc .L8
.L7:
	mov $b,$a
	inc
	mov $a,$b
.L8:
	mov $c,$a
	mov $a,$b
	ldsp 5
	cmp $b
	jz .L10
	jnc .L10
.L9:
	mov $b,$a
	inc
	mov $a,$b
.L10:
	mov $c,$a
	mov $a,$b
	ldsp 6
	cmp $b
	jz .L12
	jnc .L12
.L11:
	mov $b,$a
	inc
	mov $a,$b
.L12:
	mov $c,$a
	mov $a,$b
	ldsp 7
	cmp $b
	jz .L14
	jnc .L14
.L13:
	mov $b,$a
	inc
	mov $a,$b
.L14:
	mov $b,$a
.L5:
	pop $d
	ret

_main:
	; allocate 1 locals on stack
	push_imm 0
	push_imm 25
	push_imm 10
	jal _max
	pop $d
	pop $d
	stsp 1
	ldsp 1
	out

	push_imm 150
	push_imm 200
	jal _max
	pop $d
	pop $d
	stsp 1
	ldsp 1
	out

	push_imm 30
	push_imm 100
	push_imm 75
	push_imm 20
	push_imm 50
	jal _count_above
	pop $d
	pop $d
	pop $d
	pop $d
	pop $d
	stsp 1
	ldsp 1
	out

	hlt

.L15:
	pop $d
	ret

