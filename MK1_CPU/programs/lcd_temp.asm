; HD44780 LCD temperature display via PCF8574 I2C on VIA
; Data-driven init + inline temp read + division + char display
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
; STOP to finalize bus recovery
ddrb_imm 0x03
ddrb_imm 0x01
ddrb_imm 0x00
; LCD init (data-driven from data page, uses __lcd_write)
; Send init nibbles with DELAY sentinel support
ldi $d, 0
.linit:
mov $d, $a
deref
ldi $b, 0xFF
cmp $b
jz .linit_done
ldi $b, 0xFC
cmp $b
jnz .linit_send
; DELAY: ~5ms
push $d
ldi $a, 0
.ldly:
dec
jnz .ldly
pop $d
j .linit_adv
.linit_send:
jal __lcd_write
.linit_adv:
mov $d, $a
inc
mov $a, $d
j .linit
.linit_done:
; Read DS3231 temp (reg 0x11) — use inline START (not __i2c_st which sends LCD addr)
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xD0
jal __sb
ldi $a, 0x11
jal __sb
jal __i2c_sp
exrw 2
ddrb_imm 0x01
ddrb_imm 0x03
ldi $a, 0xD1
jal __sb
; Read byte (inline)
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
; NACK + STOP
ddrb_imm 0x00
ddrb_imm 0x02
jal __i2c_sp
; A = temp → 7-seg
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
; Display tens (space if 0)
mov $b, $a
tst 0xFF
jnz .st
j .skip_tens
.st:
addi 48, $a
mov $a, $d
jal __lcd_chr
.skip_tens:
; Display ones
pop $a
addi 48, $a
mov $a, $d
jal __lcd_chr
; Degree symbol
ldi $d, 0xDF
jal __lcd_chr
; C
ldi $d, 0x43
jal __lcd_chr
hlt

; ── LCD write: send one byte to PCF8574 via I2C ──
__lcd_write:
	push $a
	jal __i2c_st
	pop $a
	jal __sb
	jal __i2c_sp
	ret

; ── LCD char: send character in D ──
__lcd_chr:
	; High nibble with RS+BL+EN
	mov $d, $a
	andi 0xF0, $a
	ori 0x0D, $a
	jal __lcd_write
	; High nibble RS+BL (no EN)
	mov $d, $a
	andi 0xF0, $a
	ori 0x09, $a
	jal __lcd_write
	; Low nibble with RS+BL+EN
	mov $d, $a
	sll
	sll
	sll
	sll
	andi 0xF0, $a
	ori 0x0D, $a
	jal __lcd_write
	; Low nibble RS+BL (no EN)
	mov $d, $a
	sll
	sll
	sll
	sll
	andi 0xF0, $a
	ori 0x09, $a
	jal __lcd_write
	ret

; ── I2C START + PCF8574 addr ──
__i2c_st:
	exrw 2
	ddrb_imm 0x01
	ddrb_imm 0x03
	ldi $a, 0x4E
	jal __sb
	ret

; ── I2C STOP ──
__i2c_sp:
	ddrb_imm 0x03
	ddrb_imm 0x01
	ddrb_imm 0x00
	ret

; ── I2C send byte ──
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
; LCD init sequence with DELAY (0xFC) and END (0xFF) sentinels
; Each data byte is sent via __lcd_write (I2C to PCF8574)
; BL=0x08, EN=0x04, RS=0x01
; Reset nibble 0x03 × 3 with delays
#d8 0x3C
#d8 0x38
#d8 0xFC
#d8 0x3C
#d8 0x38
#d8 0xFC
#d8 0x3C
#d8 0x38
; 4-bit mode
#d8 0x2C
#d8 0x28
; Function set 0x28: 4-bit, 2-line, 5x8
#d8 0x2C
#d8 0x28
#d8 0x8C
#d8 0x88
; Display on 0x0C
#d8 0x0C
#d8 0x08
#d8 0xCC
#d8 0xC8
; Clear 0x01
#d8 0x0C
#d8 0x08
#d8 0x1C
#d8 0x18
#d8 0xFC
; Entry mode 0x06
#d8 0x0C
#d8 0x08
#d8 0x6C
#d8 0x68
#d8 0xFF
