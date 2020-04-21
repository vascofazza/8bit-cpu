; division test
#include "lib/mk1.cpu"

ldi $a 144
ldi $b 3; = 48
jal divide
out $a
hlt

#include "lib/mk1_std.asm"
