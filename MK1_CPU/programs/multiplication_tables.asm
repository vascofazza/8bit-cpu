; multiplication tables
#include "lib/mk1.cpu"

init:
  jal init_display
  ldi $a 1
  ldi $b 1

main:
  cmp 26
  jz .end
.loop:
  push $a
  push $b
  jal multiply
  jal print
  pop $a
  cmp 10
  jz .break
  addi 1 $b
  pop $a
  j .loop

.break:
  jal clear_display
  pop $a
  addi 1 $a
  ldi $b 1
  j main

.end:
  hlt

print:
  out
  jal print_int
  ldi $a SPACE
  jal print_char
  ret


#include "lib/mk1_std.asm"
#include "lib/helix.asm"
