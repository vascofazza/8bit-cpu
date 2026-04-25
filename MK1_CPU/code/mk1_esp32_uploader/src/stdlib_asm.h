// Embedded MK1 standard library — auto-included when #include "lib/mk1_std.asm"
// This is the assembly source embedded as a string constant.

#pragma once

static const char MK1_STDLIB_ASM[] = R"ASM(
;-- utility functions --

;-- XOR -- ret $a = $a XOR $b
#bank ".data"
a_nand_b: #res 1
b_nand_anandb: #res 1

#bank ".instr"
eor:
    push $c
    push $d
    mov $a $d
    and $b $a
    not
    st $a a_nand_b
    and $b $a
    not
    st $a b_nand_anandb
    mov $d $a
    ld $c a_nand_b
    and $c $a
    not
    ld $c b_nand_anandb
    and $c $a
    not
    pop $d
    pop $c
    ret

;--- multiplication ---
multiply:
  mov $b $c
  mov $a $b
  ldi $d 0
  cmp 0
  jz .end

.loop:
  mov $c $a
  cmp 0
  jz .end
  mov $d $a
  add $b $a
  mov $a $d
  mov $c $a
  subi 1 $c
  j .loop

.end:
  mov $d $a
  ret

;--- divide ---
#bank ".data"
_sign: #res 1
#bank ".instr"
divide:
  mov $a $c
  ldi $d 2
  st $d _sign
  ldi $d 0
  cmp 0
  jz .ret

.loop:
  mov $c $a
  sub $b $a
  mov $a $c
  jz .ret_zero
  andi 128 $a
  jz .set_sign
  push $d
  ld $d _sign
  sub $d $a
  pop $d
  jz .ret
.continue:
  mov $d $a
  addi 1 $d
  j .loop

.ret_zero:
  mov $d $a
  addi 1 $d
.ret:
  mov $d $a
  ret

.set_sign:
  ldi $a 128
  st $a _sign
  j .continue


;--- get division reminder ---
reminder:
  mov $a $c
  ldi $d 2
  cmp 0
  jz .ret_zero

.loop:
  mov $c $a
  sub $b $a
  jz .ret_zero
  mov $a $c
  andi 128 $a
  jz .set_sign
  sub $d $a
  jz .ret
  j .loop

.ret:
  mov $c $a
  add $b $a
.ret_zero:
  ret

.set_sign:
  ldi $d 128
  j .loop

;--- compare ---
compare:
  sub $b $a
  add $b $a
  jc .ret_false
  ldi $a 0
  ret
.ret_false:
  ldi $a 1
  ret
)ASM";
