;--- computes prime numbers ---
;--- includes helix display support ---
#include "lib/mk1.cpu"

init:
  ldi $a 3
  jal clear_display

.loop:
  push $a
  jal is_prime ;call subroutine
  cmp 0
  pop $a
  jz .continue ;if the result is 0 do not print value
  push $a
  jal print
  pop $a
.continue:
  addi 2 $a
  jc .end
  j .loop
.end:
  hlt

print:
  out $a
  jal print_int
  ldi $a SPACE
  jal print_char
  ret

; --- is_prime ---
is_prime:
  ;optimization -> divisions start from half
  push $a
  slr
  subi 1 $b ; preparing second operand for reminder
  pop $a
  jz .ret_true

;main loop
.prime_loop:
  push $a
  push $b
  jal reminder
  cmp 0
  jz .ret_false
  pop $a ; counter
  pop $b ; argument
  subi 2 $a ;counter decrement + ;if counter == 1 -> prime
  jz .ret_true
  addi 1 $a ;restore good counter
  mov $b $c
  mov $a $b
  mov $c $a
  j .prime_loop

.ret_true:
  ldi $a 1
  ret
.ret_false:
  pop $b
  pop $b
  ldi $a 0
  ret

#include "lib/mk1_std.asm"
#include "lib/helix.asm"
