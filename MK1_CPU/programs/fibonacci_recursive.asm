;fibonacci sequence - recursive algorithm
#include "lib/mk1.cpu"

main:
  ldi $a 1 ; counter

.loop:
  cmp 14 ; maximum printable fibonacci value is fib(13)
  jz .end
  push $a
  jal fibonacci ; computing fib(counter)
  out $a
  pop $a
  addi 1 $a
  j .loop

.end:
  hlt

fibonacci:
  mov $a $d ; input argument to $d
  cmp 0
  jz .ret_base_0 ; if argument is 0 ret 0
  subi 1 $a
  jz .ret_base_1 ; if argument is 1 ret 1
  push $d
  jal fibonacci ; computing fib(argument - 1)
  pop $d
  mov $a $b ; $b contains fib(-1)
  mov $d $a
  subi 2 $a ; preparing argument - 2
  push $b
  jal fibonacci ; computing fib(argument - 2)
  pop $b
  add $b $a ; returning fib(-1) + fib(-2)
  ret

.ret_base_0:
  ldi $a 0
  ret

.ret_base_1:
  ldi $a 1
  ret
