;--- bubble sort ---
#include "lib/mk1.cpu"

#bank ".data"
data: #d8 123, 210, 20, 13, 222, 94, 205, 199, 213, 176, 58, 160, 216, 12, 73, 172, 184, 225, 125, 63, 186, 111, 252, 136, 242, 92, 101, 134, 175, 126, 195, 2, 42, 57, 149, 23, 223, 48, 214, 217
vector_len = pc - data
vector: #res vector_len
#bank ".instr"

init:
  ;copy vector to tmp array
  ldi $a 0
.loop:
  cmp vector_len
  jz main
  addi data $b
  addi vector $c
  ld $b [$b]
  st $b [$c]
  addi 1 $a
  j .loop

main:
  jal print
  ldi $a vector_len
  subi 1 $b ;prepare end - 1
  ldi $a 0
  jal bubble_sort
  jal print
  hlt

bubble_sort:
  ldi $a 0
.loop:
  cmp vector_len - 1
  jz .end
  push $a
  ldi $a 0
.for:
  cmp vector_len - 1
  jz .next
  addi 1 $b
  push $a
  push $b
  addi vector $a
  ld $a [$a]
  push $a
  mov $b $a
  addi vector $a
  ld $a [$a]
  mov $a $b
  pop $a
  jal compare
  cmp 1
  pop $a
  pop $b
  jz .for
  push $a
  push $b
  ;addi vector $a
  ;subi 1 $b
  jal swap
  pop $b
  pop $a
  j .for

.next:
  pop $a
  addi 1 $a
  j .loop

.end:
  ret


; print subroutine
print:
  jal clear_display
  ldi $b vector
  ldi $a 0
.loop:
  cmp vector_len
  jz .end
  add $b $c
  ld $c [$c]
  out $c
  push $a
  mov $c $a
  jal print_int
  ldi $a SPACE
  jal print_char
  pop $a
  addi 1 $a
  j .loop
.end:
  ret

;--- compare ---
compare: ;$a < $b
  sub $b $a
  add $b $a
  jc .ret_false
  ; a greater
  ldi $a 0
  ret
  ; b greater
.ret_false:
  ldi $a 1
  ret

swap:
  addi vector $c ; c = [a]
  ld $a [$c] ; a = vec[a]
  mov $a $d ; d = vec[a]
  mov $b $a
  addi vector $a ; a = [b]
  ld $b [$a] ; b = vec[b]
  st $d [$a]
  st $b [$c]
  ret

#include "lib/helix.asm"
