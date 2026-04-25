; Does exrw 0 clobber C?
nop
nop
nop
clr $a
exw 0 0
ddrb_imm 0x00
exw 0 3
; Set C to known value
ldi $a, 42
mov $a,$c        ; C = 42
; Do exrw 0
exrw 0           ; A = port B. Does C change?
; Output C
mov $c,$a        ; A = C (should be 42 if preserved)
out
hlt
