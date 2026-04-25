; Stress test: does DDRB survive 256 iterations of non-VIA ops?
; Output 3 = no corruption. Anything else = E0 glitch problem.
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
; 256 iterations of varied non-VIA instructions
clr $c
.loop:
ldi $a, 0x55
ldi $b, 0xAA
mov $b,$a
sll
sll
ldi $a, 0xFF
ldi $b, 0x01
mov $b,$a
dec
dec
dec
ldi $a, 0x42
tst 0x80
jnz .skip
ldi $a, 0x00
.skip:
mov $c,$a
inc
mov $a,$c
jnz .loop
; Read DDRB back — should still be 3
exrw 2
out
hlt
