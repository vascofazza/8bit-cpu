;--- merge sort ---
#include "lib/mk1.cpu"

#bank ".data"
data: #d8 123, 210, 20, 13, 222, 94, 205, 199;, 213, 176, 58, 160, 216, 12, 73, 172, 184, 225, 125, 63, 186, 111, 252, 136, 242, 92, 101, 134, 175, 126, 195, 2, 42, 57, 149, 23, 223, 48, 214, 217
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
  jal merge_sort
  jal print
  hlt

merge_sort: ; start, end
  cmp $b ; if start == end -> return
  jz .return

  ;compute mid index
  mov $a $d ; d = start
  mov $b $a ; a = b = end
  sub $d $a ; a = end - start
  slr ;(end - start) / 2
  add $d $a ; a = start + (end - start) / 2
  mov $b $c ; c = end
  mov $a $b ; b = mid = start + (end - start) / 2
  mov $d $a ; a = start

  ;first call (start, middle)
  push $a
  push $b
  push $c
  jal merge_sort
  pop $b ; end
  pop $a ; mid
  pop $c ; start

  ;second call (middle, end)
  push $a
  push $b
  push $c
  addi 1 $a
  jal merge_sort
  pop $a ; start
  pop $c ; end
  pop $b ; mid

  ;merge phase
  jal merge
.return:
  ret

; ---- merge function ----
merge: ;start, mid, end

; merge variables
#bank ".data"
start: #res 1
start2: #res 1
mid: #res 1
end: #res 1
index: #res 1
#bank ".instr"

  ;init variable
  st $a start
  st $b mid
  st $c end
  mov $b $a
  addi 1 $a
  st $a start2 ; a = mid +1 = start2

; if vec[mid] <= vec[start2] -> return
  addi vector $a ; a = [start2]
  ld $c [$a] ; c = vec[start2]
  ldi $a vector
  add $b $b ; b = [mid]
  mov $c $a ; a = vec[start2]
  ld $b [$b] ; b = vec[mid]
  jal compare ; $a < $b? vec[start2] < vec[mid] ?
  cmp 1
  jz .while
  j .return

.while:
  ;while start <= mid and start2 <= end
  ld $a mid
  ld $b start
  jal compare ; mid < start?
  cmp 1
  jz .return
  ld $a end
  ld $b start2
  push $b
  jal compare ; end < start2?
  cmp 1
  pop $a
  jz .return

.if: ;a -> start2
  ;if vec[start] <= vec[start2] -> start++
  addi vector $c ; c = [start2]
  ld $a start
  mov $a $d ; d = start
  addi vector $b ; b = [start]
  ld $a [$c] ; a = vec[start2]
  push $a ; n                  <---- vec[start2] in stack (value)
  ld $b [$b] ; b = vec[start]
  push $d
  jal compare ; start2 < start ?
  cmp 1
  pop $d ;                     <------- d = start
  jz .else
  mov $d $a
  addi 1 $a
  st $a start ; start++
  pop $a ; de-allocating stack
  j .while
.else:
  ;idx = start2
  ;while idx != start
  ld $b start2 ; b = start 2 = idx
.while_2:
  mov $d $a ; d = a = start
  cmp $b
  jz .break
  ;vec[idx] = vec[idx - 1]
  mov $b $a ; b = idx
  subi 1 $a ; idx -1
  addi vector $a ; [idx - 1]
  ld $c [$a] ; c = vec[idx - 1]
  mov $b $a ; b = idx
  addi vector $a ; [idx]
  st $c [$a]; ;vec[idx] = vec[idx - 1]
  ;idx --
  mov $b $a
  subi 1 $b ; b = idx - 1
  j .while_2

.break:
  ;d = start
  ;arr[start] = value (in stack)
  mov $d $a
  addi vector $a; a = [start]
  pop $b ;<- value
  st $b [$a] ; arr[start] = value

  ;update counters
  ldi $a 1
  add $d $d ; start++
  st $d start
  ld $b start2
  add $b $b
  st $b start2 ; start2++
  ld $b mid
  add $b $b
  st $b mid ; mid++
  j .while

.return:
  ret

#include "lib/helix.asm"

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
