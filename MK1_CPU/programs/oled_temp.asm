; SSD1306 OLED temperature display — live temp, optimized
; VIA init + bus recovery combined
ldi $d, 0
.dly:
ddrb_imm 0x00
ddrb_imm 0x02
dec
jnz .dly
clr $a
exw 0 0
ddrb_imm 0x00
; STOP to finalize bus recovery
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; OLED init (16 bytes from data[65])
ddrb_imm 0x01
ddrb_imm 0x03
ldi $d, 65
ldi $c, 16
jal __send_n
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Clear page 0: 128 zeros (countdown)
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0x78
jal __sb
ldi $a, 0x40
jal __sb
ldi $d, 128
.clz:
push $d
clr $a
jal __sb
pop $d
mov $d, $a
dec
mov $a, $d
jnz .clz
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Read DS3231 temp: set reg ptr (data-driven, 4 bytes at data[81])
ddrb_imm 0x01
ddrb_imm 0x03
ldi $d, 81
ldi $c, 2
jal __send_n
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; Read phase: START + 0xD1 + read byte + NACK + STOP
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xD1
jal __sb
; Inline __rb (saves jal+ret = 3B)
ldi $b, 0
ldi $d, 8
.rb:
mov $b, $a
sll
mov $a, $b
ddrb_imm 0x00
exrw 0
tst 0x01
jz .rz
mov $b, $a
ori 0x01, $a
mov $a, $b
.rz:
ddrb_imm 0x02
mov $d, $a
dec
mov $a, $d
jnz .rb
mov $b, $a
; A=temp
; NACK + STOP
ddrb_imm 0x00
ddrb_imm 0x02
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; A=temp → 7-seg
out
; Divide by 10
ldi $b, 0
.div:
cmp 10
jc .divd
subi 10, $a
mov $b, $a
inc
mov $a, $b
j .div
.divd:
push $a
; Tens (space if 0)
mov $b, $a
tst 0xFF
jnz .st
ldi $a, 10
.st:
jal __glyph
pop $a
jal __glyph
ldi $a, 11
jal __glyph
ldi $a, 12
jal __glyph
hlt

__glyph:
	mov $a, $b
	sll
	sll
	add $b, $a
	mov $a, $d
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a, 0x78
	jal __sb
	ldi $a, 0x40
	jal __sb
	ldi $c, 5
	jal __send_n
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
	ret

__send_n:
.sn:
	push $d
	mov $c, $a
	push $a
	mov $d, $a
	deref
	jal __sb
	pop $a
	mov $a, $c
	pop $a
	mov $a, $d
	mov $d, $a
	inc
	mov $a, $d
	mov $c, $a
	dec
	mov $a, $c
	jnz .sn
	ret

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

#bank ".data"
; Font (offset 0-64)
#d8 0x3E
#d8 0x51
#d8 0x49
#d8 0x45
#d8 0x3E
#d8 0x00
#d8 0x42
#d8 0x7F
#d8 0x40
#d8 0x00
#d8 0x42
#d8 0x61
#d8 0x51
#d8 0x49
#d8 0x46
#d8 0x21
#d8 0x41
#d8 0x45
#d8 0x4B
#d8 0x31
#d8 0x18
#d8 0x14
#d8 0x12
#d8 0x7F
#d8 0x10
#d8 0x27
#d8 0x45
#d8 0x45
#d8 0x45
#d8 0x39
#d8 0x3C
#d8 0x4A
#d8 0x49
#d8 0x49
#d8 0x30
#d8 0x01
#d8 0x71
#d8 0x09
#d8 0x05
#d8 0x03
#d8 0x36
#d8 0x49
#d8 0x49
#d8 0x49
#d8 0x36
#d8 0x06
#d8 0x49
#d8 0x49
#d8 0x29
#d8 0x1E
#d8 0x00
#d8 0x00
#d8 0x00
#d8 0x00
#d8 0x00
#d8 0x06
#d8 0x09
#d8 0x09
#d8 0x06
#d8 0x00
#d8 0x3E
#d8 0x41
#d8 0x41
#d8 0x41
#d8 0x22
; OLED init (offset 65, 16 bytes): page addressing
#d8 0x78
#d8 0x00
#d8 0xAE
#d8 0xA8
#d8 0x3F
#d8 0x8D
#d8 0x14
#d8 0x20
#d8 0x02
#d8 0xA1
#d8 0xC8
#d8 0xDA
#d8 0x12
#d8 0xA4
#d8 0xA6
#d8 0xAF
; DS3231 temp write phase (offset 81, 4 bytes): addr + reg 0x11
#d8 0xD0
#d8 0x11
#d8 0xD1
#d8 0xFF
