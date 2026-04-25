; Combined: VIA init, SQW config, calibrate, EEPROM write+read
; Single-phase calibration (HIGH only), D_half/2 = D/4
; Output: read-back value (expect 042)

.via_dly:
    dec
    jnz .via_dly
    clr $a
    exw 0 0
    exw 0 2
    exw 0 3
    push $a
    pop $a

    ; I2C: configure DS3231 SQW = 1Hz
    jal __i2c_st
    ldi $a, 0xD0
    jal __i2c_sb
    ldi $a, 0x0E
    jal __i2c_sb
    clr $a
    jal __i2c_sb
    jal __i2c_sp

    ; SQW sync: wait LOW then HIGH
.s1:
    exrw 1
    tst 0x01
    jz .s2
    j .s1
.s2:
    exrw 1
    tst 0x01
    jnz .cal
    j .s2

    ; Calibrate: count overflows during HIGH phase only
.cal:
    ldi $b, 0
.ch:
    ldi $a, 64
.ci:
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    dec
    jnz .ci
    mov $b, $a
    inc
    mov $a, $b
    exrw 1
    tst 0x01
    jz .cd
    j .ch

    ; D_half = B. D_half/2 = D/4
.cd:
    mov $b, $a
    slr
    ldi $b, 0
    ideref          ; data[0] = D/4

    ; EEPROM write 42 to 0x0320
    jal __i2c_wr_addr
    ldi $a, 42
    jal __i2c_sb
    jal __i2c_sp

    ; Delay ~250ms (D/4 overflows)
    jal delay

    ; Set read address
    jal __i2c_wr_addr
    jal __i2c_sp

    ; Current-address read
    jal __i2c_st
    ldi $a, 0xAF
    jal __i2c_sb
    jal __i2c_rb
    jal __i2c_nack_sp

    ; Output
    mov $d, $a
    out
    clr $a
    exw 0 2
    hlt

; ── Subroutines ──

; START + send device addr + high addr + low addr
__i2c_wr_addr:
    jal __i2c_st
    ldi $a, 0xAE
    jal __i2c_sb
    ldi $a, 0x03
    jal __i2c_sb
    ldi $a, 0x20
    jal __i2c_sb
    ret

__i2c_st:
    exrw 2
    ldi $a, 0x01
    exw 0 2
    ldi $a, 0x03
    exw 0 2
    ret

delay:
    clr $a
    deref
    mov $a, $b
.do:
    ldi $a, 64
.di:
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    dec
    jnz .di
    mov $b, $a
    dec
    mov $a, $b
    jnz .do
    ret

__i2c_sb:
    mov $a, $b
    ldi $a, 8
    mov $a, $c
.isb:
    mov $b, $a
    tst 0x80
    jnz .isbh
    ldi $a, 0x03
    exw 0 2
    ldi $a, 0x01
    exw 0 2
    ldi $a, 0x03
    exw 0 2
    j .isbn
.isbh:
    ldi $a, 0x02
    exw 0 2
    clr $a
    exw 0 2
    ldi $a, 0x02
    exw 0 2
.isbn:
    mov $b, $a
    sll
    mov $a, $b
    mov $c, $a
    dec
    mov $a, $c
    jnz .isb
    ldi $a, 0x02
    exw 0 2
    nop
    nop
    nop
    nop
    nop
    clr $a
    exw 0 2
    nop
    nop
    nop
    nop
    nop
    exrw 0
    push $a
    ldi $a, 0x02
    exw 0 2
    pop $a
    ret

__i2c_nack_sp:
    ldi $a, 0x02
    exw 0 2
    clr $a
    exw 0 2
    nop
    nop
    ldi $a, 0x02
    exw 0 2
__i2c_sp:
    ldi $a, 0x03
    exw 0 2
    ldi $a, 0x01
    exw 0 2
    clr $a
    exw 0 2
    ret

__i2c_rb:
    ldi $d, 0
    ldi $c, 8
.rb:
    ldi $a, 0x02
    exw 0 2
    nop
    nop
    clr $a
    exw 0 2
    nop
    nop
    nop
    exrw 0
    push $a
    mov $d, $a
    sll
    mov $a, $d
    pop $a
    andi 0x01, $a
    or $d, $a
    mov $a, $d
    ldi $a, 0x02
    exw 0 2
    mov $c, $a
    dec
    mov $a, $c
    jnz .rb
    ret

    section data
    byte 0
