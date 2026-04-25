;-- utility functions --

;-- XOR -- ret $a = $a XOR $b
#bank ".data"
a_nand_b: #res 1
b_nand_anandb: #res 1

#bank ".instr"
eor: ;ret $a = $a XOR $b

    push $c
    push $d
    mov $a $d ; hold original logic a in $d

    and $b $a
    not ;$a = (A NAND B)
    st $a a_nand_b

    and $b $a
    not ;$a = (B NAND(A NAND B))
    st $a b_nand_anandb

    mov $d $a
    ld $c a_nand_b

    and $c $a
    not; $a = (A NAND (A NAND B))

    ld $c b_nand_anandb

    and $c $a
    not; $a = (A NAND (A NAND B)) NAND (B NAND(A NAND B))
    
    pop $d
    pop $c
    ret

;--- multiplication ---
multiply: ; $a * $b
  mov $b $c ;counter
  mov $a $b ;multiplication base
  ldi $d 0 ;tmp
  cmp 0
  jz .end

.loop:
  mov $c $a ; counter equals 0 -> we're done
  cmp 0
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
#bank ".data"
_sign: #res 1
#bank ".instr"
divide: ;$a / $b
  mov $a $c; c contains tmp value
  ldi $d 2; sign on
  st $d _sign
  ldi $d 0; counter
  cmp 0
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
  ld $d _sign
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
  st $a _sign
  j .continue


;--- get division reminder ---
reminder: ;$a % $b
  mov $a $c; c contains tmp value
  ldi $d 2; sign
  cmp 0
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
