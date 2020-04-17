; division test
#include "mk1.cpu"

ldi $a 144
ldi $b 3; = 48
jal divide
out $a
hlt

#include "mk1_std.asm"
