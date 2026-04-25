; Hardware smoke test for new register inc/dec opcodes.
; Exercises decb, decc, decd, incb, incc, incd and their flag behaviour.
; Each test outputs a known value via OI.
; Expected output sequence: 4 9 99 1 43 8 255 0 77 3 2 1
; Run via test_new_incdec_hw.py which issues ASM + UPLOAD + RUNNB to ESP32.

    section code
    org 0

; --- DECD: D 5 -> 4 ---
    ldi $d,5
    decd
    mov $d,$a
    out

; --- DECC: C 10 -> 9 ---
    ldi $c,10
    decc
    mov $c,$a
    out

; --- DECB: B 100 -> 99 ---
    ldi $b,100
    decb
    mov $b,$a
    out

; --- INCD: D 0 -> 1 ---
    ldi $d,0
    incd
    mov $d,$a
    out

; --- INCC: C 42 -> 43 ---
    ldi $c,42
    incc
    mov $c,$a
    out

; --- INCB: B 7 -> 8 ---
    ldi $b,7
    incb
    mov $b,$a
    out

; --- DECD wrap: 0 -> 255 ---
    ldi $d,0
    decd
    mov $d,$a
    out

; --- INCD wrap: 255 -> 0 ---
    ldi $d,255
    incd
    mov $d,$a
    out

; --- DECD zero flag: 1-1=0, jz should fire to "77" branch ---
    ldi $d,1
    decd
    jz .zf_ok
    ldi $a,0xFF
    out
    j .zf_done
.zf_ok:
    ldi $a,77
    out
.zf_done:

; --- Loop: decd; jnz -- count 3,2,1 ---
    ldi $d,3
.loop:
    mov $d,$a
    out
    decd
    jnz .loop

    hlt
