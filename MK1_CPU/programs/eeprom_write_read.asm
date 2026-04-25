; Simple EEPROM test: write 42, delay 15ms, read back, output result
; data[0] has D/4 from calibration program
	ldi $d, 0
.via_dly:
	dec
	jnz .via_dly
	clr $a
	exw 0 0
	exw 0 2
	exw 0 3			; DDRA = 0

	; Write 42 to 0x0350
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, 0x03
	jal __i2c_sb
	ldi $a, 0x50
	jal __i2c_sb
	ldi $a, 42
	jal __i2c_sb
	jal __i2c_sp

	; Delay 15ms
	ldi $b, 15
	jal delay_Nms

	; Read back from 0x0350
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAE
	jal __i2c_sb
	ldi $a, 0x03
	jal __i2c_sb
	ldi $a, 0x50
	jal __i2c_sb
	jal __i2c_sp
	exrw 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0xAF
	jal __i2c_sb
	jal __i2c_rb
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	nop
	nop
	ldi $a, 0x02
	exw 0 2
	jal __i2c_sp

	; Output read value (should be 42)
	mov $d, $a
	out
	clr $a
	exw 0 2
	hlt

__i2c_sb:
	mov $a, $b
	ldi $a, 8
	mov $a, $c
.isb:
	mov $b, $a
	tst 0x80
	jnz .isbh
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	ldi $a, 0x03
	exw 0 2
	j .isbn
.isbh:
	ldi $a, 0x02
	exw 0 2
	clr $a
	exw 0 2
	ldi $a, 0x02
	exw 0 2
.isbn:
	mov $b, $a
	sll
	mov $a, $b
	mov $c, $a
	dec
	mov $a, $c
	jnz .isb
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	nop
	nop
	exrw 0
	push $a
	ldi $a, 0x02
	exw 0 2
	pop $a
	ret
__i2c_sp:
	ldi $a, 0x03
	exw 0 2
	ldi $a, 0x01
	exw 0 2
	clr $a
	exw 0 2
	ret
__i2c_rb:
	ldi $d, 0
	ldi $c, 8
.rb:
	ldi $a, 0x02
	exw 0 2
	nop
	nop
	clr $a
	exw 0 2
	nop
	nop
	nop
	exrw 0
	push $a
	mov $d, $a
	sll
	mov $a, $d
	pop $a
	andi 0x01, $a
	or $d, $a
	mov $a, $d
	ldi $a, 0x02
	exw 0 2
	mov $c, $a
	dec
	mov $a, $c
	jnz .rb
	ret
delay_Nms:
.dnms:
	clr $a
	deref
	mov $a, $c
.dov:
	jal __d256
	mov $c, $a
	dec
	mov $a, $c
	jnz .dov
	mov $b, $a
	dec
	mov $a, $b
	jnz .dnms
	ret
__d256:
	clr $a
.d256:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	dec
	jnz .d256
	ret
