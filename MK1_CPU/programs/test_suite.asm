;--- test suite ---
#include "lib/mk1.cpu"

init:
;--- MOVE ---

test_00: ;cmp
  ldi $a 243
  cmp 200
  jz end
  mov $a $b
  cmp $b
  jz test_01
  hlt

test_01:
  ldi $a 0x77
  cmp 0x77
  jz .continue1
  hlt
.continue1:
  ldi $b 0x66
  ldi $a 0x66
  cmp $b
  jz .test_ok
  hlt
.test_ok:
  out 1

test_02:
  ldi $a 0xFF
  mov $a $b
  mov $b $c
  mov $c $d
  cmp $b
  jz .continue1
  hlt
.continue1:
  mov $c $a
  cmp $c
  jz .continue2
  hlt
.continue2:
  mov $d $a
  cmp $d
  jz .test_ok
  hlt
.test_ok:
  out 2

;--- LOAD ---
#bank data
variable: #d8 0x55
variable_location: #d8 variable
#bank instr
test_03:
  ld $a variable
  cmp 0x55
  jz .test_ok
  hlt
.test_ok:
  out 3

test_04:
  ld $b variable_location
  ld $a [$b]
  cmp 0x55
  jz .test_ok
  hlt
.test_ok:
  out 4

;--- STORE ---

#bank data
value = 0x42
store_variable: #res 1
#bank instr
test_05:
  ldi $a value
  st $a store_variable
  ld $b store_variable
  cmp $b
  jz .test_ok
  hlt
.test_ok:
  out 5

test_06:
  value1 = 0x54
  ldi $a value1
  ldi $b store_variable
  st $a [$b]
  ld $b [$b]
  cmp $b
  jz .test_ok
  hlt
.test_ok:
  out 6

;ALU

test_07:
  ldi $a 77
  addi 10 $a
  subi 87 $a
  jz .test_ok
  hlt
.test_ok:
  out 7

test_08:
  ldi $a 77
  ldi $b 10
  sub $b $a
  cmp 67
  jz .test_ok
  hlt
.test_ok:
  out 8

test_09:
  ldi $a 77
  ori 112 $a
  cmp 125
  jz .test_ok
  hlt
.test_ok:
  out 9

test_10:
  ldi $a 77
  andi 112 $a
  cmp 64
  jz .test_ok
  hlt
.test_ok:
  out 10

test_11:
  ldi $a 0x55
  not
  cmp 0xAA
  jz .test_ok
  hlt
.test_ok:
  out 11

test_12:
  ldi $a 0xAA
  sll
  cmp 0x54
  jz .test_ok
  hlt
.test_ok:
  out 12

test_13:
  ldi $a 0x55
  slr
  cmp 0x2A
  jz .test_ok
  hlt
.test_ok:
  out 13

test_14:
  ldi $a 0xB2
  rll
  cmp 0x65
  jz .test_ok
  hlt
.test_ok:
  out 14

test_15:
  ldi $a 0x65
  rlr
  cmp 0xB2
  jz .test_ok
  hlt
.test_ok:
  out 15

;EXTRA (pop push jal ret jz jc)

test_16:
  mov $sp $a
  cmp 0
  jz .continue1
  hlt
.continue1:
  ldi $a 123
  push $a
  mov $sp $a
  cmp 0xFF
  jz .continue2
  hlt
.continue2:
  pop $b
  mov $sp $a
  cmp 0
  jz .continue3
  hlt
.continue3:
  mov $b $a
  cmp 123
  jz .test_ok
  hlt
.test_ok:
  out 16

test_17:
  ldi $a 0xFF
  addi 0 $a
  jc end
  addi 1 $a
  jc .test_ok
  hlt
.test_ok:
  out 17

test_18:
  jal func
  cmp 0x55
  jz .test_ok
  hlt
.test_ok:
  out 18

end:
  hlt

func:
  ldi $a 0x55
  ret
