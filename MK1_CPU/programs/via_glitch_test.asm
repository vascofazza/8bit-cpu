; Test: does DDRB get corrupted by non-VIA instructions?
; Sets DDRB=0x03, runs many non-VIA ops, reads DDRB back
; Expected output: 3 (no corruption), anything else = glitch problem
nop
nop
nop
; VIA init delay
ldi $d,0
.dly:
dec
jnz .dly
; Clear VIA
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; Set DDRB = 0x03
ddrb_imm 0x03
; Now do a LOT of non-VIA work
; 10 iterations of ALU + jump activity
ldi $c, 10
.loop:
ldi $a, 0x55
ldi $b, 0xAA
mov $b,$a
ldi $a, 0x0F
ldi $b, 0xF0
mov $b,$a
sll
sll
sll
mov $c,$a
dec
mov $a,$c
jnz .loop
; Read DDRB back
exrw 2
out
hlt
