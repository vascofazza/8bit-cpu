; Phase A spike — helper-overlay proof of concept (v2).
;
; Avoid `org N` in section page3_code: ESP32's assembler pads with HLT
; bytes up to N, which for N=230 clobbers page3 past the useful range.
; Instead, emit the helper body sequentially into page3 and record the
; page3 offset in the manifest. Helper labels that need runtime-code
; addresses can be placed via a separate code org block if required —
; the spike's helper has no internal labels so no need here.

	section page3
	byte 2               ; manifest[0].offset = 2 (helper body at page3[2])
	byte 3               ; manifest[0].size   = 3

	; Helper body bytes — raw, no org. Assembler continues page3_size
	; from 2, so these land at page3[2..4].
	byte 0xD1            ; out_imm opcode
	byte 0xB0            ; imm
	byte 0x6C            ; ret

	section code
	org 0
	j _main
_load_helper:
	push $b
	push $a
	mov $c, $a
	sll
	addi 0, $a           ; __h_manifest is at page3[0]
	mov $a, $d
	derefp3              ; A = offset
	mov $a, $c
	mov $d, $a
	inc
	derefp3              ; A = size
	addi 230, $a
	mov $a, $d
	ldi $b, 230
.hcopy:
	mov $c, $a
	derefp3
	istc_inc
	incc
	mov $b, $a
	cmp $d
	jnz .hcopy
	pop $a
	pop $b
	j 230

__hello:
	ldi $c, 0
	j _load_helper

_main:
	ldi $b, 0xFF
	mov $b, $sp
	out_imm 0xA0
	out_imm 0xA1
	jal __hello
	out_imm 0xA2
	hlt
.t:
	j .t
