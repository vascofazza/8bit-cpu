; Known-good I2C scan for DS3231 at address 0x68 (87 decimal)
; Uses exw 0 2 (not ddrb_imm) — matches verified-working VIA scan code
nop
nop
nop
ldi $a, 0x00
exw 0 0            ; ORB = 0
ldi $a, 0x00
exw 0 2            ; DDRB = 0 (idle)
; Scan address 0x68
exrw 2              ; READ DDRB — required before START
; START
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
; Send 0xD0 (0x68 << 1 = write address)
ldi $a, 0xD0
mov $a, $b
ldi $a, 8
mov $a, $c
.send:
mov $b, $a
tst 0x80
jnz .high
; LOW bit
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x03
exw 0 2
j .next
.high:
; HIGH bit
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
; ACK check
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
exrw 0              ; read port B — bit 0 = SDA
push $a
ldi $a, 0x02
exw 0 2
; STOP
ldi $a, 0x03
exw 0 2
ldi $a, 0x01
exw 0 2
ldi $a, 0x00
exw 0 2
; Check ACK
pop $a
tst 0x01
jnz .nack
out_imm 87          ; ACK — device found at 0x68
hlt
.nack:
out_imm 0           ; NACK — not found
hlt
