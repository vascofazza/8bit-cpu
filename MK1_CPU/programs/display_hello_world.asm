#include "lib/mk1.cpu"

#bank data
helloworld: #d "Hello, world!\0"

#bank instr
main:
  jal init_display
  ldi $b helloworld
.loop:
  ld $a [$b]
  cmp 0
  jz end
  push $a
  push $b
  jal print_char
  pop $b
  pop $a
  ldi $a 1
  add $b $b
  j .loop

end:
  hlt

#include "lib/helix.asm"
