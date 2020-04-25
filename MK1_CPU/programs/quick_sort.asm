;--- quick sort ---
#include "lib/mk1.cpu"

#bank ".data"
data: #d8 123, 110, 20, 13, 222, 94, 205, 199, 213, 176, 58, 160, 216, 12, 73, 172, 184, 225, 125, 63, 186, 111, 252, 136, 242, 92, 101, 134, 175, 126, 195, 2, 42, 57, 149, 23, 223, 48, 214, 217
vector_len = pc - data
vector: #res vector_len
#bank ".instr"

init:
  jal init_display
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
  jal quick_sort
  jal print
  hlt


quick_sort:
  ;cmp $b ; if low == high -> return
  push $a
  push $b
  jal compare_signed
  cmp 1
  pop $b
  pop $a
  jz .continue
  j .return
.continue:
  push $b ; high
  push $a ; low
  jal partition; pivot
  subi 1 $a ; pivot -1
  mov $a $b
  pop $a
  push $b ;pivot -1
  jal quick_sort

  pop $a ; pivot -1
  addi 2 $a ; pivot +1
  pop $b ; high
  jal quick_sort
  ret

.return:
  ret

#bank ".data"
pivot: #res 1
i: #res 1
j: #res 1
#bank ".instr"
partition: ;low, high
  mov $a $c ; c = low
  mov $b $a
  addi vector $a
  ld $a [$a]
  st $a pivot
  mov $c $a
  subi 1 $a
  st $a i
  st $c j
.for:
  ld $a j
  push $b
  cmp $b
  jz .break

  addi vector $a
  ld $a [$a]
  ld $b pivot
  jal compare
  cmp 0
  jz .next
  ld $a i
  addi 1 $a
  st $a i
  ld $b j
  jal swap
.next:
  ld $a j
  addi 1 $a
  st $a j
  pop $b ; high
  j .for

.break:
  ld $a i
  addi 1 $a
  pop $b ; high
  push $a
  jal swap
  pop $a
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

;--- compare ---
compare_signed:
  mov $a $c
  mov $b $d
  andi 128 $a
  mov $a $b
  mov $d $a
  andi 128 $a
  cmp $b
  jz _compare
  cmp 128
  jz .ret_true
  ldi $a 1
  ret
.ret_true:
  ldi $a 0
  ret

_compare:
  mov $c $a
  mov $d $b
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
