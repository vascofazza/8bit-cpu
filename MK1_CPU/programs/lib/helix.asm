;--- helix display interface library ---

SPACE = 32

_active_wait:
  nop
  je0 .ret
  nop
  j _active_wait
.ret:
  exr 0
  ret

print_char:
  push $a
  jal _active_wait
  pop $a
  exw 0 2
  ret

print_int:
  push $a
  jal _active_wait
  pop $a
  exw 0 1
  ret

clear_display:
  push $a
  jal _active_wait
  pop $a
  exw 0 3
  ret
