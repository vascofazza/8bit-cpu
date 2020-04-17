#include "mk1.cpu"

j main
#align 2
helloworld: #str "H\0e\0l\0l\0o\0,\0 \0w\0o\0r\0l\0d\0!\0\0\0"

main:
  ldi $b helloworld / 2
loop:
  ld $a [$b]
  subi 0 $a
  jz end
  exw 0 2
  ldi $a 1
  add $b $b
  j loop

end:
  hlt
