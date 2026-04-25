; Scan for AT24C32 at 0x57 (write addr 0xAE)
nop
nop
nop
ldi $a, 0x00
exw 0 0
ldi $a, 0x00
exw 0 2
exw 0 3
exrw 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0xAE
mov $a, $b
ldi $a, 8
mov $a, $c
.send:
mov $b, $a
tst 0x80
jnz .high
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
j .next
.high:
ldi $a, 0x02
exw 0 2
ldi $a, 0x00
exw 0 2
ldi $a, 0x02
exw 0 2
.next:
mov $b, $a
sll
mov $a, $b
mov $c, $a
dec
mov $a, $c
jnz .send
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
push $a
ldi $a, 0x02
exw 0 2
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2
pop $a
tst 0x01
jnz .nack
out_imm 1
hlt
.nack:
out_imm 0
hlt
