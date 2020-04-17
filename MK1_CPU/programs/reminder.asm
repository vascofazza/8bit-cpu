; reminder test
#include "mk1.cpu"

ldi $a 99
ldi $b 50
jal reminder
out $a
hlt

#include "mk1_std.asm"
