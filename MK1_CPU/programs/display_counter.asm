#include "mk1.cpu"

SPACE = 32
ldi $a 0

loop:
  exw 0 1
  addi 1 $b
  ldi $a SPACE
  exw 0 2
  jc end
  mov $b $a
  j loop

end:
  hlt
