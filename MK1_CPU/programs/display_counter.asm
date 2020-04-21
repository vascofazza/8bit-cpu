#include "lib/mk1.cpu"

ldi $a 0

loop:
  jal print_int
  addi 1 $b
  ldi $a SPACE
  push $a
  push $b
  jal print_char
  pop $b
  pop $a
  jc end
  mov $b $a
  j loop

end:
  hlt

#include "lib/helix.asm"
