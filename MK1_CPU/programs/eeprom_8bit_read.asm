; Read 8 individual data bits from EEPROM using scan-proven bit pattern
; First write 0xA5 to addr 0x0000, wait, then read back bit by bit
; Outputs 8 values: each is 0 or 1 for that bit (MSB first)
; Expected for 0xA5: 1,0,1,0,0,1,0,1
nop
nop
nop
ldi $a, 0x00
exw 0 0
ldi $a, 0x00
exw 0 2
exw 0 3

; === WRITE 0xA5 to addr 0x0000 ===
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAE
jal __i2c_sb
ldi $a, 0x00
jal __i2c_sb
ldi $a, 0x00
jal __i2c_sb
ldi $a, 0xA5
jal __i2c_sb
; STOP
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2

; Wait 20ms for write cycle
ldi $d, 20
.ww:
ldi $a, 0
.wi:
dec
jnz .wi
mov $d,$a
dec
mov $a,$d
jnz .ww

; === SET ADDRESS POINTER to 0x0000 ===
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAE
jal __i2c_sb
ldi $a, 0x00
jal __i2c_sb
ldi $a, 0x00
jal __i2c_sb
; STOP
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2

; === START READ ===
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAF
jal __i2c_sb

; === READ 8 BITS using scan ACK pattern, output each ===
; Bit 7 (MSB)
ldi $a, 0x02
exw 0 2
nop
nop
nop
nop
nop
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
exrw 0
tst 0x01
jnz .b7_1
out_imm 0
j .b6
.b7_1:
out_imm 1
; Bit 6
.b6:
ldi $a, 0x02
exw 0 2
nop
nop
nop
nop
nop
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
exrw 0
tst 0x01
jnz .b6_1
out_imm 0
j .b5
.b6_1:
out_imm 1
; Bit 5
.b5:
ldi $a, 0x02
exw 0 2
nop
nop
nop
nop
nop
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
exrw 0
tst 0x01
jnz .b5_1
out_imm 0
j .b4
.b5_1:
out_imm 1
; Bit 4
.b4:
ldi $a, 0x02
exw 0 2
nop
nop
nop
nop
nop
ldi $a, 0x00
exw 0 2
nop
nop
nop
nop
nop
exrw 0
tst 0x01
jnz .b4_1
out_imm 0
j .done
.b4_1:
out_imm 1
; Only read top 4 bits — enough to identify 0xA (1010)
.done:
; NACK + STOP (don't read remaining bits)
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
out_imm 99
hlt

__i2c_sb:
	mov $a,$b
	ldi $a,8
	mov $a,$c
.isb:
	mov $b,$a
	tst 0x80
	jnz .isbh
	ldi $a,0x03
	exw 0 2
	ldi $a,0x01
	exw 0 2
	ldi $a,0x03
	exw 0 2
	j .isbn
.isbh:
	ldi $a,0x02
	exw 0 2
	ldi $a,0x00
	exw 0 2
	ldi $a,0x02
	exw 0 2
.isbn:
	mov $b,$a
	sll
	mov $a,$b
	mov $c,$a
	dec
	mov $a,$c
	jnz .isb
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
