; reminder test
#include "lib/mk1.cpu"

ldi $a 99
ldi $b 50
jal reminder
out $a
hlt

#include "lib/mk1_std.asm"
