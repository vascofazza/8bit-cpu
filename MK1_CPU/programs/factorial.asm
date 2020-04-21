;factorial - recursive algorithm
#include "lib/mk1.cpu"

max_value = 5 + 1
init:
  ldi $a 0

main:
  cmp max_value
  jz end
  push $a
  jal factorial
  out
  pop $a
  addi 1 $a
  j main

end:
  hlt

;--- factorial routine ---
factorial:
  ;base case
  cmp 0
  jz .ret_base
  ;computing factorial($a - 1)
  push $a
  subi 1 $a
  jal factorial
  pop $b
  jal multiply
  ret

.ret_base:
  ldi $a 1
  ret

#include "lib/mk1_std.asm"
