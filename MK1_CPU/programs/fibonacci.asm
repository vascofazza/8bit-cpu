;fibonacci sequence
#include "mk1.cpu"

init:
  ldi $a 1
  ldi $b 1

loop:
  out $a
  mov $a $c
  add $b $a
  jc end
  mov $c $b
  j loop

end:
  hlt
