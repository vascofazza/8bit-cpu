#include "lib/mk1.cpu"

jal init_display
ldi $a 0

loop:
  push $a
  out
  jal print_int
  ldi $a SPACE
  jal print_char
  pop $a
  addi 1 $a
  jc end
  j loop

end:
  hlt

#include "lib/helix.asm"
