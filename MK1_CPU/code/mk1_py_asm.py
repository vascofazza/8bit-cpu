#!/usr/bin/env python3
"""Python MK1 assembler — converts mk1cc2's asm dialect to code/data/page3
byte arrays. Mirrors enough of the ESP32 C++ assembler (assembler.h) to
let us run compiled programs through mk1sim.MK1 without needing hardware.

mk1cc2's dialect differs slightly from microcode.py's canonical mnemonics:
  mk1cc2  →  canonical
  ldi $a,5    move imm, $a
  mov $a,$b   move $a, $b
  push $a     stor $a, [$sp]
  pop $a      load $a, [$sp]
  jal X       stor $pc, [$sp]     (imm=X)
  j X         move imm, $pc       (imm=X)
  ret         load $pc, [$sp]
  clr $a      sub $a, $a
  nop         move $a, $a
  out         move $a, $out
  addi N,$a   add imm, $a         (imm=N)
  cmpi N      cmp imm             (imm=N)

Sections:
  code / page3_code / data_code / stack_code / data / page3 / eeprom
  `org N` sets the current position within the active section.

Two-pass assembly: pass 1 collects label addresses, pass 2 emits bytes.
Output matches the ESP32 uploadBuf layout: [code(256), data(256),
stack(256), page3(256)] plus optional EEPROM bytes.

Usage as a module:
    pages = assemble_asm(asm_text)
    # pages['code'], pages['data'], pages['stack'], pages['page3'],
    # pages['eeprom']
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import microcode as _mc


# ── Build the canonical-mnemonic → opcode map ────────────────────────

def _build_opcode_map():
    """Returns (by_mnemonic, has_imm_by_mnemonic).

    `by_mnemonic[canonical_str]` = opcode_byte.
    `has_imm_by_mnemonic[canonical_str]` = True iff the instruction takes
    an immediate (i.e. is ≥ 2 bytes total). Microcode is the authoritative
    source for this — do not duplicate the list anywhere else in this file.
    """
    by_mn = {}
    has_imm_mn = {}
    for opc, entry in _mc.ucode_template.items():
        mn, steps, imm = entry
        by_mn[mn] = opc
        has_imm_mn[mn] = imm
    return by_mn, has_imm_mn


CANON, HAS_IMM_MN = _build_opcode_map()

# Multi-immediate opcodes (more than 1 imm byte). Microcode's has_imm is
# a single bool, so fusion opcodes are special-cased here. Keep this in
# sync with mk1ir._MULTI_IMM.
_MULTI_IMM = {'ddrb2_imm': 3, 'ddrb3_imm': 4}  # total instruction size incl. opcode

# Opcodes that are 2 bytes in binary but which microcode's has_imm flag
# gets wrong. Two reasons the flag lies:
#   1. Flag-set conditionals (`jcf`, `jzf`, `je0`, `je1`) consume a filler
#      byte via PE without reading it as data — the has_imm flag tracks
#      data-use, not PC-advance.
#   2. `stor $pc, [$sp]` (canonical form of `jal imm`) is post-hacked at
#      microcode.py line 419 to read an imm byte as jump target, but the
#      has_imm flag on its template entry was set from the generic stor
#      for-loop (`second == 7 or first == 7` — both false for $pc/$sp)
#      and the patch doesn't update it.
# ESP32's isa.h correctly marks all of these as ARGS_IMM. Until we rework
# microcode's third tuple element to mean "instruction size in bytes",
# this set covers the gap.
_IMM_SKIP_MN = {'jcf', 'jzf', 'je0', 'je1', 'stor $pc, [$sp]'}


# ── mk1cc2 dialect → canonical mnemonic translator ───────────────────

def _translate_instr(s):
    """Return (canonical_mnemonic, imm_expr_or_None) for one instr line.

    s is the bare instruction text (no leading whitespace, no label).
    imm_expr_or_None is a string expression (label/number) that should
    resolve to a byte value during pass 2.

    Raises ValueError for unknown instructions."""
    parts = s.split()
    if not parts:
        raise ValueError(f'empty instruction')
    mn = parts[0]
    rest = s[len(mn):].strip()

    # Directly-matching mnemonics with no operand rewriting
    direct = {
        'nop': ('move $a, $a', None),
        'hlt': ('hlt', None),
        'ret': ('load $pc, [$sp]', None),
        'out': ('move $a, $out', None),
        'clr': None,        # handled below (has operand)
        'dec': ('dec', None),
        'inc': ('inc', None),
        'decb': ('decb', None), 'incb': ('incb', None),
        'decc': ('decc', None), 'incc': ('incc', None),
        'decd': ('decd', None), 'incd': ('incd', None),
        'deref': ('deref', None),
        'deref2': ('deref2', None),
        'derefp3': ('derefp3', None),
        'ideref': ('ideref', None),
        'ideref2': ('ideref2', None),
        'iderefp3': ('iderefp3', None),
        'istc': ('istc', None),
        'istc_inc': ('istc_inc', None),
        'sll': ('sll', None), 'slr': ('slr', None),
        'rll': ('rll', None), 'rlr': ('rlr', None),
        'swap': ('swap', None),
        'not': ('not', None), 'neg': ('neg', None),
        'xor': ('xor', None),
        'pop_b': ('pop_b', None),
        'push_b': ('push_b', None),
        'setc': ('setc', None), 'setz': ('setz', None),
        'setnc': ('setnc', None), 'setnz': ('setnz', None),
        'setjmp': ('setjmp', None), 'setret': ('setret', None),
        'ocall': ('ocall', None),
        'adc': ('adc', None), 'sbc': ('sbc', None),
        'jal_r': ('jal_r', None),
        'cmpi': None,  # handled below
    }
    if mn in direct and direct[mn] is not None:
        return direct[mn]

    # clr $a → sub $a, $a
    if mn == 'clr':
        if rest == '$a':
            return ('sub $a, $a', None)
        raise ValueError(f'unknown clr operand: {s!r}')

    # ldi $X, N → move imm, $X
    if mn == 'ldi':
        m = re.match(r'\s*(\$\w+)\s*,\s*(\S+)\s*$', rest)
        if not m:
            raise ValueError(f'bad ldi: {s!r}')
        reg, imm = m.group(1), m.group(2)
        return (f'move imm, {reg}', imm)

    # mov $src, $dst → move $src, $dst (may be 2B if src=imm or dst=imm)
    if mn == 'mov':
        m = re.match(r'\s*(\$\w+)\s*,\s*(\$\w+)\s*$', rest)
        if not m:
            raise ValueError(f'bad mov: {s!r}')
        src, dst = m.group(1), m.group(2)
        return (f'move {src}, {dst}', None)

    # push $X → stor $X, [$sp]
    if mn == 'push':
        m = re.match(r'\s*(\$\w+)\s*$', rest)
        if not m:
            raise ValueError(f'bad push: {s!r}')
        return (f'stor {m.group(1)}, [$sp]', None)
    # pop $X → load $X, [$sp]
    if mn == 'pop':
        m = re.match(r'\s*(\$\w+)\s*$', rest)
        if not m:
            raise ValueError(f'bad pop: {s!r}')
        return (f'load {m.group(1)}, [$sp]', None)

    # push_imm N → push_imm with imm
    if mn == 'push_imm':
        return ('push_imm', rest)

    # jal X → stor $pc, [$sp] imm=X
    if mn == 'jal':
        return ('stor $pc, [$sp]', rest)
    # j/jz/jnz/jc/jnc X → specific opcodes with imm=X
    if mn == 'j':
        return ('move imm, $pc', rest)
    if mn == 'jz':
        return ('jzf', rest)
    if mn == 'jnz':
        return ('jnz', rest)
    if mn == 'jc':
        return ('jcf', rest)
    if mn == 'jnc':
        return ('jnc', rest)

    # Immediate ALU: addi/subi/andi/ori N,$X → add/sub/and/or imm, $X
    for op_in, op_out in (('addi', 'add'), ('subi', 'sub'),
                          ('andi', 'and'), ('ori', 'or')):
        if mn == op_in:
            m = re.match(r'\s*(\S+?)\s*,\s*(\$\w+)\s*$', rest)
            if not m:
                raise ValueError(f'bad {op_in}: {s!r}')
            imm, dst = m.group(1), m.group(2)
            return (f'{op_out} imm, {dst}', imm)

    # ALU reg-reg: add/sub/and/or $src, $dst
    for alu in ('add', 'sub', 'and', 'or'):
        if mn == alu:
            m = re.match(r'\s*(\$\w+)\s*,\s*(\$\w+)\s*$', rest)
            if not m:
                raise ValueError(f'bad {alu}: {s!r}')
            return (f'{alu} {m.group(1)}, {m.group(2)}', None)

    # cmp $X → cmp $X (1B, clobbers nothing useful).
    # cmp N  → cmpi (opcode 0xFD, 2B, doesn't clobber $b).
    # ESP32 emits cmpi for the immediate form (see assembler.h line 738).
    # The legacy `cmp imm` opcode (0x86, clobbers $b via EI) exists in
    # microcode but is not emitted by either ESP32 or mk1cc2 in practice.
    if mn == 'cmp':
        m = re.match(r'\s*(\S+)\s*$', rest)
        if not m:
            raise ValueError(f'bad cmp: {s!r}')
        operand = m.group(1)
        if operand.startswith('$'):
            return (f'cmp {operand}', None)
        return ('cmpi', operand)
    # cmpi N → cmp imm (but there's a separate 0xFD opcode for cmpi)
    if mn == 'cmpi':
        return ('cmpi', rest)

    # tst N → tst with imm
    if mn == 'tst':
        return ('tst', rest)

    # load $X, [$Y] / stor $X, [$Y] / load $X, [imm] / stor $X, [imm]
    if mn in ('load', 'stor'):
        m = re.match(r'\s*(\$\w+)\s*,\s*\[(.+?)\]\s*$', rest)
        if not m:
            raise ValueError(f'bad {mn}: {s!r}')
        reg, inside = m.group(1), m.group(2).strip()
        if inside.startswith('$'):
            return (f'{mn} {reg}, [{inside}]', None)
        # Non-register: immediate addressing
        return (f'{mn} {reg}, [imm]', inside)

    # move (canonical form user may type directly)
    if mn == 'move':
        m = re.match(r'\s*(\$\w+|imm)\s*,\s*(\$\w+|imm)\s*$', rest)
        if m:
            src, dst = m.group(1), m.group(2)
            return (f'move {src}, {dst}', None if src != 'imm' else '0')

    # ddrb_imm N, ddra_imm N, orb_imm N, ora_imm N, out_imm N — single imm
    for specimm in ('ddrb_imm', 'ddra_imm', 'orb_imm', 'ora_imm', 'out_imm'):
        if mn == specimm:
            return (specimm, rest)

    # ddrb2_imm A,B and ddrb3_imm A,B,C — multi-imm. `rest` holds the
    # comma-joined imms; the emit path splits them in pass 2.
    if mn in ('ddrb2_imm', 'ddrb3_imm'):
        return (mn, rest)

    # ocall N — overlay call with immediate index
    if mn == 'ocall':
        return ('ocall', rest)

    # je0 / je1 — flag-set PC moves with imm (skip-semantics).
    if mn in ('je0', 'je1'):
        return (mn, rest)

    # ldsp N, stsp N, ldsp_b N, ldp3 N, stp3 N
    for specmn in ('ldsp', 'stsp', 'ldsp_b', 'ldp3', 'stp3'):
        if mn == specmn:
            return (specmn, rest)

    # exr / exw / exrw
    if mn == 'exr' or mn == 'exw' or mn == 'exrw':
        # Normalise spacing: `exr 0` vs `exr 0 0`
        parts2 = rest.split()
        if mn == 'exrw':
            # exrw N — single operand in canonical. mk1cc2 uses same form.
            return (f'exrw {parts2[0]}', None)
        # exw/exr need two operands in canonical form
        if len(parts2) == 1:
            return (f'{mn} 0 {parts2[0]}', None)
        if len(parts2) == 2:
            return (f'{mn} {parts2[0]} {parts2[1]}', None)

    raise ValueError(f'unknown instruction: {s!r}')


# ── Expression evaluation (pass 2) ───────────────────────────────────

def _eval_imm(expr, labels):
    """Resolve a numeric immediate. Accepts decimal, hex (0xNN), binary
    (0bNNN), label names, char literals ('A'), or sum of such via `+`."""
    expr = expr.strip()
    if expr.startswith("'") and expr.endswith("'") and len(expr) >= 3:
        body = expr[1:-1]
        if body.startswith('\\'):
            esc = {'n': 10, 'r': 13, 't': 9, '0': 0, '\\': 92, "'": 39}
            if len(body) == 2 and body[1] in esc:
                return esc[body[1]]
        if len(body) == 1:
            return ord(body)
    # Simple sum: a+b
    if '+' in expr and not expr.startswith('0x'):
        return sum(_eval_imm(p.strip(), labels) for p in expr.split('+'))
    if expr.startswith('0x') or expr.startswith('0X'):
        return int(expr, 16)
    if expr.startswith('0b') or expr.startswith('0B'):
        return int(expr, 2)
    if expr.lstrip('-').isdigit():
        return int(expr)
    # Label
    if expr in labels:
        return labels[expr]
    raise ValueError(f'unresolved immediate: {expr!r}')


# ── Pass 1: measure sizes + collect label addresses ──────────────────

def _instr_size(canon_mn):
    """Byte size of an instruction given its canonical mnemonic.

    Sources of truth (authoritative in order):
      1. `_MULTI_IMM` — explicit fusion opcodes that span >2 bytes.
      2. `HAS_IMM_MN` — from microcode, for instructions that READ an imm.
      3. `_IMM_SKIP_MN` — for instructions that consume a filler byte via
         PE without reading it (flag-skip conditionals).

    Any divergence from the ESP32 assembler is a bug in one of these three
    tables, not a judgment call here."""
    if canon_mn in _MULTI_IMM:
        return _MULTI_IMM[canon_mn]
    if HAS_IMM_MN.get(canon_mn, False):
        return 2
    if canon_mn in _IMM_SKIP_MN:
        return 2
    return 1


def _parse_lines(asm_text):
    """Strip comments + blank lines. Yields (line_no, stripped_text)."""
    for i, raw in enumerate(asm_text.splitlines(), 1):
        s = raw
        # Strip ; comments
        if ';' in s:
            s = s[:s.index(';')]
        s = s.strip()
        if s:
            yield i, s


# Sections recognised by mk1cc2 + their target byte-buffer key.
# `code` is the main stage-1 code page.
# `page3_code` bytes live at code addresses but are ALSO copied to page3
# at the same offset (via `section page3_code` + `org N`).
# `page3_kernel` is an alternate spelling for init-extraction mode.
# `data_code`, `stack_code` are overlay BODY bytes that live in data/stack
# pages at runtime (copied by overlay loader to code[overlay_region]).
# `data`, `page3`, `eeprom`, `stack` are pure data.
SECTIONS = {
    'code': 'code',
    'page3_code': 'page3_code',   # dual-residence (code + page3)
    'page3_kernel': 'page3_code', # alias
    'data_code': 'data_code',     # overlay body → data page
    'stack_code': 'stack_code',   # overlay body → stack page
    'data': 'data',
    'page3': 'page3',             # direct page3 data (bytes, no code)
    'stack': 'stack',
    'eeprom': 'eeprom',
}


def assemble_asm(asm_text):
    """Two-pass assemble. Returns dict with bytearrays for each page."""
    # Pass 1 — compute label addresses per section.
    # Each section has its own address counter. `org N` sets it.
    # Labels take the current counter value in the current section.
    # For `code` and `page3_code`: the counter IS the code-page address.
    # For data/page3/stack/eeprom: the counter is the buffer offset.
    sec_pc = {k: 0 for k in set(SECTIONS.values())}
    # Track overlay-body data offsets separately. `data_code` + `org N`
    # means "virtually at code address N" but BYTES go sequentially into
    # the data page starting at the next-free data slot.
    data_code_offset = None   # set when overlay storage starts
    # Labels map name → address (int). data_code labels use the org value,
    # so when the loader copies data_code[offset..offset+size] to code[N..],
    # the labels resolve correctly to the loaded addresses.
    labels = {}
    cur_section = 'code'
    pass1_lines = []   # list of (section_at_time_of_line, text)
    for ln_no, text in _parse_lines(asm_text):
        if text.startswith('section '):
            sec = text.split()[1]
            if sec not in SECTIONS:
                raise ValueError(f'Line {ln_no}: unknown section {sec!r}')
            cur_section = SECTIONS[sec]
            pass1_lines.append((cur_section, text))
            continue
        if text.startswith('org '):
            val = int(text.split()[1], 0)
            sec_pc[cur_section] = val
            pass1_lines.append((cur_section, text))
            continue
        # Label? (ends with :, no whitespace)
        if text.endswith(':'):
            label = text[:-1]
            # For code/page3_code: label = code-page address (sec_pc['code']
            # or sec_pc['page3_code']). For data_code/stack_code: label =
            # the virtual code-page address (the `org N` value, which is
            # where the overlay body will live at runtime).
            labels[label] = sec_pc[cur_section]
            pass1_lines.append((cur_section, text))
            continue
        # Directive: `byte N` = 1 byte, takes expression
        if text.startswith('byte '):
            pass1_lines.append((cur_section, text))
            sec_pc[cur_section] += 1
            continue
        # Regular instruction
        try:
            canon, imm_expr = _translate_instr(text)
        except ValueError as e:
            raise ValueError(f'Line {ln_no}: {e}')
        size = _instr_size(canon)
        pass1_lines.append((cur_section, text))
        sec_pc[cur_section] += size

    # Pass 2 — emit bytes.
    code = bytearray(256)
    data = bytearray(256)
    stack = bytearray(256)
    page3 = bytearray(256)
    eeprom = bytearray(4096)

    # Running write pointers per output BUFFER (not per section). The
    # ESP32 assembler has a single `result.data_size` that's advanced by
    # both `section data` (byte directives) and `section data_code`
    # (instructions) — they share the buffer. Same for stack, page3,
    # eeprom. py_asm mirrors that.
    #
    # sec_pc still exists separately and tracks the VIRTUAL code PC for
    # label resolution (in code/page3_code/data_code/stack_code sections).
    # sec_pc has no bearing on where bytes land in the output buffers
    # for *_code sections.
    buf_pos = {'code': 0, 'data': 0, 'stack': 0, 'page3': 0, 'eeprom': 0}

    sec_pc = {k: 0 for k in set(SECTIONS.values())}
    cur_section = 'code'

    def emit(section, byte):
        """Emit one byte to the right buffer, advancing the matching
        buf_pos and (for *_code sections) sec_pc so labels resolve to
        the correct virtual address."""
        if section == 'code':
            if 0 <= sec_pc['code'] < 256:
                code[sec_pc['code']] = byte
            sec_pc['code'] += 1
            buf_pos['code'] = sec_pc['code']   # kept in sync for diagnostics
        elif section == 'page3_code':
            # Bytes go ONLY to page3 buffer (at buf_pos['page3']), not to
            # the code buffer. These are stage-2 kernel bytes that
            # self-copy will blit into the code page at runtime. Label
            # addresses advance in sec_pc['page3_code'] so they resolve
            # to the code-page address they'll occupy after self-copy.
            if 0 <= buf_pos['page3'] < 256:
                page3[buf_pos['page3']] = byte
            buf_pos['page3'] += 1
            sec_pc['page3_code'] += 1
        elif section == 'data_code':
            # Bytes go into the data buffer sequentially (shared pointer
            # with `section data`), but the virtual code PC advances so
            # labels inside the overlay body resolve to the runtime code
            # address they will be loaded at.
            if 0 <= buf_pos['data'] < 256:
                data[buf_pos['data']] = byte
            buf_pos['data'] += 1
            sec_pc['data_code'] += 1
        elif section == 'stack_code':
            if 0 <= buf_pos['stack'] < 256:
                stack[buf_pos['stack']] = byte
            buf_pos['stack'] += 1
            sec_pc['stack_code'] += 1
        elif section == 'data':
            # Raw data: ESP32 advances data_size on every byte directive
            # regardless of `org`. We match by writing at buf_pos['data'].
            if 0 <= buf_pos['data'] < 256:
                data[buf_pos['data']] = byte
            buf_pos['data'] += 1
            sec_pc['data'] = buf_pos['data']
        elif section == 'page3':
            if 0 <= buf_pos['page3'] < 256:
                page3[buf_pos['page3']] = byte
            buf_pos['page3'] += 1
            sec_pc['page3'] = buf_pos['page3']
        elif section == 'stack':
            if 0 <= buf_pos['stack'] < 256:
                stack[buf_pos['stack']] = byte
            buf_pos['stack'] += 1
            sec_pc['stack'] = buf_pos['stack']
        elif section == 'eeprom':
            if 0 <= buf_pos['eeprom'] < 4096:
                eeprom[buf_pos['eeprom']] = byte
            buf_pos['eeprom'] += 1
            sec_pc['eeprom'] = buf_pos['eeprom']

    for sec_at_line, text in pass1_lines:
        cur_section = sec_at_line
        if text.startswith('section '):
            continue
        if text.startswith('org '):
            val = int(text.split()[1], 0)
            sec_pc[cur_section] = val
            continue
        if text.endswith(':'):
            continue
        if text.startswith('byte '):
            expr = text.split(None, 1)[1]
            val = _eval_imm(expr, labels) & 0xFF
            emit(cur_section, val)
            continue
        canon, imm_expr = _translate_instr(text)
        opcode = CANON.get(canon)
        if opcode is None:
            raise ValueError(f'No opcode for canonical {canon!r} (from {text!r})')
        emit(cur_section, opcode)
        # Emit immediate byte(s). For ddrb2_imm/ddrb3_imm the `rest` string
        # is comma-separated; split and emit each. For all other 2-byte
        # instructions, a single imm follows.
        if canon in _MULTI_IMM:
            if imm_expr is None:
                raise ValueError(f'Expected imms for {canon!r}: {text!r}')
            parts = [p.strip() for p in imm_expr.split(',') if p.strip()]
            expected = _MULTI_IMM[canon] - 1  # minus the opcode byte
            if len(parts) != expected:
                raise ValueError(
                    f'{canon} expects {expected} imms, got {len(parts)}: {text!r}')
            for p in parts:
                emit(cur_section, _eval_imm(p, labels) & 0xFF)
        elif HAS_IMM_MN.get(canon, False) or canon in _IMM_SKIP_MN:
            # _IMM_SKIP_MN emits a target byte too (ESP32 ARGS_IMM) — the
            # hardware consumes it via PE even though microcode's has_imm
            # flag is False.
            if imm_expr is None:
                raise ValueError(f'Expected immediate for {canon!r}: {text!r}')
            emit(cur_section, _eval_imm(imm_expr, labels) & 0xFF)

    return {'code': code, 'data': data, 'stack': stack, 'page3': page3,
            'eeprom': eeprom, 'labels': labels}


if __name__ == '__main__':
    # Smoke test
    asm = """
    section code
    org 0
    ldi $a,42
    out
    hlt
    """
    result = assemble_asm(asm)
    print('code[0..5] =', result['code'][:5].hex())
    # Expected: move imm, $a opcode + 42 + out opcode + hlt opcode
    # move imm, $a = 0x38 (0b00111000). out = move $a, $out = 0x06. hlt = 0x7F.
    # Byte sequence: 38 2A 06 7F
