
#include "lib/mk1.cpu"

#bank ".data"
helloworld: #str "Hello, world!\0"
s2: #str "Knock knock?\0"
s3: #str "Who's there?\0"

#bank ".instr"

jal init_lcd

ldi $b helloworld
jal print_string

jal clear_lcd

ldi $b s2
jal print_string

jal clear_lcd

ldi $b s3
jal print_string

hlt

init_lcd:
  ldi $a 0b00001101;  display on, cursor on, cursor blinks
  exw 0 1;   
  ldi $a 0b00000000;  rs = 0
  exw 0 2;   
  exw 0 3; 

  ldi $a 0b00000001;  clear display
  exw 0 1;   
  ldi $a 0b00000000;  rs = 0
  exw 0 2;
  exw 0 3; 

  ldi $a 0b00000110;  entry mode
  exw 0 1;   
  ldi $a 0b00000000;  rs = 0
  exw 0 2;  
  exw 0 3; 
  
  ret

clear_lcd:
  ldi $a 0b00000001;  clear display
  exw 0 1;   
  ldi $a 0b00000000;  rs = 0
  exw 0 2;
  exw 0 3; 

  ldi $a 0b00000011;  return home
  exw 0 1;   
  ldi $a 0b00000000;  rs = 0
  exw 0 2;
  exw 0 3; 
  

print_char:
  exw 0 1;   
  ldi $a 0b00000001;  rs/rw
  exw 0 2         
  exw 0 3  
  ret

print_string:

.loop:
  ld $a [$b]
  cmp 0
  jz .ret
    push $a
    push $b
    jal print_char
    pop $b
    pop $a
    ldi $a 1
    add $b $b
  j .loop
  .ret:
    ret

end:
    hlt