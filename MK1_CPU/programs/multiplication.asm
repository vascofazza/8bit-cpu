; reminder test
#include "lib/mk1.cpu"

ldi $a 5
ldi $b 17 ; 85
jal multiply
out $a
hlt

#include "lib/mk1_std.asm"
