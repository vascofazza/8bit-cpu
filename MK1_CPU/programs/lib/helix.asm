;--- helix display interface library ---

SPACE = 32

#bank ".data"
_ready: #d8 1
#bank ".instr"

init_display:
  ldi $a 1
  je0 .ret
  ldi $a 0
.ret:
  st $a _ready
  ret

print_char:
  jal _display_ready
  exw 0 2
  ret

print_int:
  jal _display_ready
  exw 0 1
  ret

clear_display:
  jal _display_ready
  exw 0 3
  ret

_display_ready:
  push $a
  ld $a _ready
  add $a $a
  jz .ret
  jal _active_wait
.ret:
  pop $a
  ret

_active_wait:
  nop
  je0 .ret
  nop
  j _active_wait
.ret:
  exr 0
  ret
