;-- utility functions --

;--- multiplication ---
multiply: ; $a * $b
  mov $b $c
  mov $a $b
  mov $a $d

.loop:
  mov $c $a
  subi 1 $a
  jz .end
  mov $d $a
  add $b $d
  mov $c $a
  subi 1 $c
  j .loop

.end:
  mov $d $a
  ret

;--- divide ---
divide: ;$a / $b
#bank ".data"
._sign:
  #res 1
#bank ".instr"

  mov $a $c; c contains tmp value
  ldi $d 2; sign on
  st $d ._sign
  ldi $d 0; counter
  subi 0 $a
  jz .ret

.loop:
  mov $c $a
  sub $b $a ;subtract the divisor
  mov $a $c
  jz .ret_zero
  ;check if the sign is positive.
  ;if sign is positive we'll check when goes negative and return.
  andi 128 $a
  jz .set_sign
  ;sign is not positive, check against old sign
  push $d
  ld $d ._sign
  sub $d $a
  pop $d
  jz .ret ;sign went negative, returning
.continue:
  mov $d $a
  addi 1 $d
  j .loop

.ret_zero:
  mov $d $a
  addi 1 $d
.ret: ;we're done! reminder is negative, get positive part and return
  mov $d $a
  ret

.set_sign:
  ldi $a 128 ;set sign to 1, when we compare and it changes we're done.
  st $a ._sign
  j .continue


;--- get division reminder ---
reminder: ;$a % $b
  mov $a $c; c contains tmp value
  ldi $d 2; sign
  subi 0 $a
  jz .ret_zero

.loop:
  mov $c $a
  sub $b $a ;subtract the divisor and check if zero
  jz .ret_zero
  mov $a $c
  ;check if the sign is positive.
  ;if sign is positive we'll check when goes negative and return.
  andi 128 $a
  jz .set_sign
  ;sign is not positive, check against old sign
  sub $d $a
  jz .ret ;sign went negative, returning.
  j .loop

.ret: ;we're done! reminder is negative, get positive part and return
  mov $c $a
  add $b $a
.ret_zero:
  ret

.set_sign:
  ldi $d 128 ;set sign to 1, when we compare and it changes we're done.
  j .loop
