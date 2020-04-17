;--- test suite ---
#include "mk1.cpu"

;--- MOVE ---

test_01:
  ldi $a 0xFF
  mov $a $b
  mov $b $c
  mov $c $d
  sub $b $a
  jz .continue1
  hlt
.continue1:
  mov $c $a
  sub $c $a
  jz .continue2
  hlt
.continue2:
  mov $d $a
  sub $d $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 1
  out

test_02:
  ldi $a 0x77
  subi 0x77 $a
  jz .continue1
  hlt
.continue1:
  ldi $b 0x66
  ldi $a 0x66
  sub $b $a
  jz .continue2
  hlt
.continue2:
  ldi $c 0x55
  ldi $a 0x55
  sub $c $a
  jz .continue3
  hlt
.continue3:
  ldi $d 0x44
  ldi $a 0x44
  sub $d $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 2
  out

;--- LOAD ---

j test_03
variable: #d8 0x55
location =  pc
variable_location: #d8 location / 2
test_03:
  ld $a location
  subi 0x55 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 3
  out

test_04:
  ld $b variable_location
  ld $a [$b]
  subi 0x55 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 4
  out

;--- STORE ---

j test_05
value = 0x42
store_variable: #res 2
var_location = pc - 2
test_05:
  ldi $a value
  st $a var_location
  ld $b var_location
  sub $b $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 5
  out

test_06:
  value1 = 0x54
  ldi $a value1
  ldi $b var_location / 2
  st $a [$b]
  ld $b [$b]
  sub $b $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 6
  out

;ALU

test_07:
  ldi $a 77
  ldi $b 10
  add $b $a
  subi 87 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 7
  out

test_08:
  ldi $a 77
  addi 10 $a
  subi 87 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 8
  out

test_09:
  ldi $a 77
  ldi $b 10
  sub $b $a
  subi 67 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 9
  out

test_10:
  ldi $a 77
  subi 10 $a
  subi 67 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 10
  out

test_11:
  ldi $a 77
  ldi $b 112
  or $b $a
  subi 125 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 11
  out

test_12:
  ldi $a 77
  ori 112 $a
  subi 125 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 12
  out

test_13:
  ldi $a 77
  ldi $b 112
  and $b $a
  subi 64 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 13
  out

test_14:
  ldi $a 77
  andi 112 $a
  subi 64 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 14
  out

test_15:
  ldi $a 0x55
  not
  subi 0xAA $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 15
  out

test_16:
  ldi $a 0xAA
  sll
  subi 0x54 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 16
  out

test_17:
  ldi $a 0x55
  slr
  subi 0x2A $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 17
  out

test_18:
  ldi $a 0xB2
  rll
  subi 0x65 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 18
  out

test_19:
  ldi $a 0x65
  rlr
  subi 0xB2 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 19
  out

;EXTRA (pop push jal ret jz jc)

test_20:
  mov $sp $a
  subi 0 $a
  jz .continue1
  hlt
.continue1:
  ldi $a 123
  push $a
  mov $sp $a
  subi 0xFF $a
  jz .continue2
  hlt
.continue2:
  pop $b
  subi 0 $a
  jz .continue3
  hlt
.continue3:
  mov $b $a
  subi 123 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 20
  out

test_21:
  ldi $a 0xFF
  addi 0 $a
  jz .test_no
  jc .test_no
  addi 1 $a
  jc .test_ok
  hlt
.test_no:
  hlt
.test_ok:
  ldi $a 21
  out

test_22:
  jal func
  subi 0x55 $a
  jz .test_ok
  hlt
.test_ok:
  ldi $a 22
  out

test_23: ;cmp

hlt

func:
  ldi $a 0x55
  ret
