"""T1.1 — whole-program IR.

Bridge between the existing flat-asm representation that every pass in
mk1cc2 consumes today and a structured (section → labels → instrs)
model that cross-section passes can operate on directly.

Design principles:
  - ROUND-TRIP FIDELITY: parse(serialize(ir)) == ir for every legal
    asm produced by mk1cc2. Verify by diffing before/after every
    corpus program; any behavior change is a parser bug.
  - NO SEMANTICS CHANGE YET: this module is a structured VIEW of the
    same bytes. Passes can be migrated to operate on IR one at a
    time; each migration is verifiable by byte-equivalent output.
  - MINIMAL: no attempt to decompose operands to a typed form; the
    operand string is stored verbatim. Future passes can parse
    further when they need to.

Structure:
  Program
    ├── sections: dict[str, Section]   # keyed by section name
    └── labels: dict[str, (section, index)]  # global + scoped labels

  Section
    ├── name: str                      # 'code', 'page3_code', 'data', …
    ├── origin: int | None             # `org N` directive (None = 0)
    └── items: list[Item]              # instructions + labels + directives + comments

  Item is one of:
    Label(name: str, is_local: bool)   # '.foo:' vs 'global:'
    Instr(mnemonic: str, operands: list[str], size_bytes: int, comment: str)
    Directive(name: str, args: str)    # 'byte N', 'org N', 'section X'
    Comment(text: str)                 # '; …' standalone comments
    Blank()                            # preserve blank lines for readability

Round-trip policy: serialization preserves source text EXACTLY
(including indentation, semicolons, comment spacing) wherever the
original line is stored in an Item's `raw` field. Semantic edits
go through `replace` helpers that regenerate raw from structured
fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Item hierarchy ─────────────────────────────────────────────────

@dataclass
class Item:
    raw: str                # original source line (including leading tab/spaces)
    # Subclasses set these where relevant — keep here for simple serialization.


@dataclass
class Label(Item):
    name: str = ''
    is_local: bool = False  # True for '.foo:', False for 'foo:'


@dataclass
class Instr(Item):
    mnemonic: str = ''
    operands: list[str] = field(default_factory=list)
    size_bytes: int = 0
    comment: str = ''       # inline '; …' after operands, stripped of leading ';'


@dataclass
class Directive(Item):
    name: str = ''          # 'section', 'org', 'byte', …
    args: str = ''          # everything after the directive name


@dataclass
class Comment(Item):
    text: str = ''          # comment body, stripped of leading ';'


@dataclass
class Blank(Item):
    pass


# ── Section + Program ──────────────────────────────────────────────

@dataclass
class Section:
    name: str
    origin: Optional[int] = None
    items: list[Item] = field(default_factory=list)


@dataclass
class Program:
    """Asm files re-enter sections multiple times (`section code` …
    `section page3_code` … `section code` again, etc.). We model this
    as an ORDERED LIST of section-chunks rather than a dict, so
    serialize() can reproduce the original interleaving byte-for-byte.

    Passes that need all items in a logical section can use
    `items_in(section_name)` which concatenates chunks by name."""
    chunks: list[Section] = field(default_factory=list)
    # Cross-section label index: label_name → (chunk_index, item_index).
    # Last-wins on duplicates (same as the assembler).
    labels: dict[str, tuple[int, int]] = field(default_factory=dict)

    def items_in(self, name: str) -> list[Item]:
        """Concatenated items from every chunk whose section name matches."""
        out = []
        for ch in self.chunks:
            if ch.name == name:
                out.extend(ch.items)
        return out

    def section_names(self) -> list[str]:
        """Unique section names in first-appearance order."""
        seen = set()
        out = []
        for ch in self.chunks:
            if ch.name not in seen:
                seen.add(ch.name)
                out.append(ch.name)
        return out


# ── Byte-size table (mirrors mk1cc2's `two_byte` set) ──────────────

# Instructions that encode to 2 bytes (1-byte opcode + 1-byte operand).
# Everything else is 1 byte. Labels, directives, comments, and blanks
# count as 0 bytes.
_TWO_BYTE_MNEMONICS = {
    'ldi', 'addi', 'subi', 'ori', 'andi',
    'j', 'jal', 'jz', 'jnz', 'jc', 'jnc',
    'push_imm', 'ldsp', 'stsp', 'ldsp_b',
    'ldp3', 'stp3',
    'ddrb_imm', 'ddra_imm', 'orb_imm', 'ora_imm',
    'ocall',
    'tst', 'cmpi', 'out_imm',
    'je0', 'je1',
}

# Multi-immediate opcodes: opcode + N immediate bytes.
_MULTI_IMM = {'ddrb2_imm': 3, 'ddrb3_imm': 4}


def instr_size(mnemonic: str, operand_str: str) -> int:
    """Return byte size of a single instruction. Mirrors measure_lines()
    in mk1cc2. `cmp` is special-cased: `cmp $X` is 1 byte (register
    cmp opcode), `cmp N` is 2 bytes (cmpi)."""
    if mnemonic == 'cmp':
        return 1 if operand_str.strip().startswith('$') else 2
    if mnemonic in _MULTI_IMM:
        return _MULTI_IMM[mnemonic]
    if mnemonic in _TWO_BYTE_MNEMONICS:
        return 2
    return 1


# ── Parser ─────────────────────────────────────────────────────────

def _strip_comment(line: str) -> tuple[str, str]:
    """Split a line into (instruction-part, comment-part).
    Comment starts at the first unquoted ';'."""
    idx = line.find(';')
    if idx < 0:
        return line, ''
    return line[:idx].rstrip(), line[idx + 1:]


def parse_line(raw: str) -> Item:
    """Classify one source line into an Item subclass. The raw string
    is preserved verbatim on the returned Item for round-trip."""
    s = raw.strip()
    if not s:
        return Blank(raw=raw)
    if s.startswith(';'):
        return Comment(raw=raw, text=s[1:])

    body, comment_text = _strip_comment(raw)
    body_s = body.strip()
    if not body_s:
        # Line is just a comment after whitespace
        return Comment(raw=raw, text=comment_text)

    # Label?
    if body_s.endswith(':'):
        name = body_s[:-1]
        return Label(raw=raw, name=name, is_local=name.startswith('.'))

    # Directive (section, org, byte)
    toks = body_s.split(None, 1)
    mn = toks[0]
    args = toks[1] if len(toks) > 1 else ''
    if mn in ('section', 'org', 'byte'):
        return Directive(raw=raw, name=mn, args=args)

    # Instruction. Operands split by comma at the top level; whitespace
    # trimmed. For simplicity we store operand tokens verbatim.
    ops = []
    if args:
        # Many MK1 instructions use comma separation, but some (exw X Y,
        # exrw N) use whitespace. Preserve whatever was there by just
        # storing the full operand string as a single element plus
        # keeping raw for serialization. Passes that need to inspect
        # operands can re-split.
        ops = [args]
    return Instr(
        raw=raw,
        mnemonic=mn,
        operands=ops,
        size_bytes=instr_size(mn, args),
        comment=comment_text,
    )


def parse_program(lines: list[str]) -> Program:
    """Turn a list of asm lines into a Program. Each `section X`
    directive opens a new chunk — we do NOT merge chunks by name so
    the interleaving found in mk1cc2 output round-trips exactly."""
    prog = Program()
    current_chunk: Optional[Section] = None

    for raw in lines:
        item = parse_line(raw)

        if isinstance(item, Directive) and item.name == 'section':
            sec_name = item.args.strip()
            current_chunk = Section(name=sec_name)
            prog.chunks.append(current_chunk)
            current_chunk.items.append(item)
            continue

        if isinstance(item, Directive) and item.name == 'org':
            if current_chunk is None:
                current_chunk = Section(name='code')
                prog.chunks.append(current_chunk)
            try:
                current_chunk.origin = int(item.args.strip(), 0)
            except (ValueError, AttributeError):
                pass
            current_chunk.items.append(item)
            continue

        # All other items go into the current chunk. If we haven't seen
        # a section directive yet, synthesize a default 'code' chunk so
        # leading comments/blanks aren't lost.
        if current_chunk is None:
            current_chunk = Section(name='code')
            prog.chunks.append(current_chunk)

        if isinstance(item, Label) and not item.is_local:
            chunk_idx = len(prog.chunks) - 1
            prog.labels[item.name] = (chunk_idx, len(current_chunk.items))
        current_chunk.items.append(item)

    return prog


# ── Serializer ────────────────────────────────────────────────────

def serialize_program(prog: Program) -> list[str]:
    """Emit the program as a list of asm lines by concatenating chunks
    in insertion order. Items mutated by passes update their `raw`
    field (see `replace_instr`), so the output reflects edits."""
    out = []
    for chunk in prog.chunks:
        for item in chunk.items:
            out.append(item.raw.rstrip('\n'))
    return out


# ── Mutation helpers ──────────────────────────────────────────────
#
# Passes that rewrite instructions should use these — they keep raw
# and the structured fields in sync so serialization reflects edits.

def replace_instr(section: Section, idx: int, new_mnemonic: str,
                  new_operands: Optional[list[str]] = None,
                  comment: Optional[str] = None) -> None:
    """Replace the instruction at `section.items[idx]` with a new
    mnemonic + operands. Preserves indentation from the original raw
    line."""
    old = section.items[idx]
    assert isinstance(old, Instr), f'expected Instr at {idx}, got {type(old).__name__}'
    indent = old.raw[:len(old.raw) - len(old.raw.lstrip())]
    ops = new_operands if new_operands is not None else old.operands
    new_comment = comment if comment is not None else old.comment
    op_str = ','.join(ops) if ops else ''
    parts = [new_mnemonic]
    if op_str:
        parts.append(op_str)
    line = indent + ' '.join(parts)
    if new_comment:
        line += ' ;' + new_comment
    section.items[idx] = Instr(
        raw=line,
        mnemonic=new_mnemonic,
        operands=ops,
        size_bytes=instr_size(new_mnemonic, op_str),
        comment=new_comment,
    )


def delete_items(section: Section, start: int, end: int) -> None:
    """Delete items[start:end] from a section. Cross-section labels
    pointing into this range become stale — callers are expected to
    rebuild the Program's label index if they rely on it."""
    del section.items[start:end]


def section_size_bytes(section: Section) -> int:
    """Total instruction bytes in a section. Labels, directives, and
    comments don't contribute. `byte N` directives contribute 1 byte
    per line."""
    total = 0
    for item in section.items:
        if isinstance(item, Instr):
            total += item.size_bytes
        elif isinstance(item, Directive) and item.name == 'byte':
            total += 1
    return total


# ── Round-trip sanity check ───────────────────────────────────────

# ── Reusable passes ─────────────────────────────────────────────

def collapse_3_window(prog: Program, collapse_table: dict) -> int:
    """Walk every chunk's items; wherever three consecutive Instrs
    have mnemonics+operands matching a key in collapse_table, replace
    the 3-Instr run with the single Instr whose mnemonic is the value.

    collapse_table: dict mapping (str1, str2, str3) → str
      where each str is the stripped asm form of one line
      (e.g. 'mov $b,$a'). Value is the replacement mnemonic.

    Operands are preserved from the ORIGINAL first line's indentation
    (tab prefix), so output looks identical to a hand-written emission.
    Returns the number of collapses performed."""
    count = 0
    for chunk in prog.chunks:
        items = chunk.items
        out = []
        i = 0
        while i < len(items):
            if (i + 2 < len(items)
                and isinstance(items[i], Instr)
                and isinstance(items[i + 1], Instr)
                and isinstance(items[i + 2], Instr)):
                a = items[i].raw.strip().split(';')[0].strip()
                b = items[i + 1].raw.strip().split(';')[0].strip()
                c = items[i + 2].raw.strip().split(';')[0].strip()
                replacement = collapse_table.get((a, b, c))
                if replacement is not None:
                    # Preserve original indentation from the first line.
                    indent = items[i].raw[:len(items[i].raw)
                                          - len(items[i].raw.lstrip())]
                    raw_line = indent + replacement
                    out.append(Instr(
                        raw=raw_line,
                        mnemonic=replacement,
                        operands=[],
                        size_bytes=instr_size(replacement, ''),
                        comment='',
                    ))
                    i += 3
                    count += 1
                    continue
            out.append(items[i])
            i += 1
        chunk.items = out
    return count


def dead_code_elim(prog: Program, terminators=None) -> int:
    """Remove unreachable items after a terminator (`ret`, `hlt`, plain
    `j`) up to the next Label. Section and org directives also end the
    dead region. Returns the number of items removed.

    Directives (`section`, `org`) inside a dead region are KEPT because
    the serializer and downstream passes rely on section markers being
    contiguous. Labels obviously end the dead region — they're jump
    targets, so code after them is reachable."""
    if terminators is None:
        terminators = {'ret', 'hlt', 'j'}
    removed = 0
    for chunk in prog.chunks:
        out = []
        in_dead = False
        for item in chunk.items:
            if isinstance(item, Label):
                in_dead = False
            elif isinstance(item, Directive):
                # Keep — don't classify as dead.
                pass
            elif in_dead:
                removed += 1
                continue
            out.append(item)
            if isinstance(item, Instr) and item.mnemonic in terminators:
                in_dead = True
        chunk.items = out
    return removed


def branch_thread(prog: Program, cond_mnemonics=None) -> int:
    """Rewrite `<cond> TARGET` where TARGET's first instruction is `j X`
    to `<cond> X` directly. Skips the intermediate one-line jump.
    cond_mnemonics defaults to the set of branching instructions.
    Returns count of rewrites.

    Uses the labels index (`prog.labels`) to resolve jump targets
    across chunks. If TARGET's first instruction (first non-comment,
    non-blank, non-directive item after the label) is an unconditional
    `j X`, thread through."""
    if cond_mnemonics is None:
        cond_mnemonics = {'j', 'jz', 'jnz', 'jc', 'jnc'}

    # Pre-build a map label → first Instr after it (skipping blanks/
    # comments/directives). Only cache if the first Instr is `j X`.
    first_instr_after = {}
    for chunk in prog.chunks:
        for idx, item in enumerate(chunk.items):
            if isinstance(item, Label):
                # Scan forward for first Instr
                for j in range(idx + 1, len(chunk.items)):
                    nxt = chunk.items[j]
                    if isinstance(nxt, (Comment, Blank, Directive)):
                        continue
                    if isinstance(nxt, Label):
                        break
                    if isinstance(nxt, Instr):
                        first_instr_after[item.name] = nxt
                    break

    count = 0
    for chunk in prog.chunks:
        for idx, item in enumerate(chunk.items):
            if not isinstance(item, Instr):
                continue
            if item.mnemonic not in cond_mnemonics:
                continue
            # Parse the jump target
            body = item.raw.strip().split(';')[0].strip()
            parts = body.split(None, 1)
            if len(parts) != 2:
                continue
            target = parts[1].strip()
            first = first_instr_after.get(target)
            if first is None:
                continue
            first_body = first.raw.strip().split(';')[0].strip()
            first_parts = first_body.split(None, 1)
            if len(first_parts) != 2 or first_parts[0] != 'j':
                continue
            final_target = first_parts[1].strip()
            # Rewrite: same conditional, new target
            indent = item.raw[:len(item.raw) - len(item.raw.lstrip())]
            new_raw = indent + f'{item.mnemonic} {final_target}'
            item.raw = new_raw
            item.operands = [final_target]
            item.size_bytes = instr_size(item.mnemonic, final_target)
            count += 1
    return count


def stsp_ldsp_elide(prog: Program, clobbers_a: set) -> int:
    """Elide `ldsp N` when preceded by `stsp N` AND followed by an
    instruction that clobbers A (so the loaded A value is wasted).
    Also handles a single intervening label before the clobber.
    Returns count of elisions."""
    count = 0
    for chunk in prog.chunks:
        items = chunk.items
        out = []
        i = 0
        while i < len(items):
            # Need stsp N, then ldsp N, then (label?) → clobber
            if (i + 1 < len(items)
                and isinstance(items[i], Instr)
                and items[i].mnemonic == 'stsp'
                and isinstance(items[i + 1], Instr)
                and items[i + 1].mnemonic == 'ldsp'):
                stsp_body = items[i].raw.strip().split(';')[0].strip().split()
                ldsp_body = items[i + 1].raw.strip().split(';')[0].strip().split()
                if (len(stsp_body) == 2 and len(ldsp_body) == 2
                    and stsp_body[1] == ldsp_body[1]):
                    # Peek past the ldsp to see if A is clobbered. Skip
                    # over one label if present (label then clobber is
                    # still safe — any branch into that label also
                    # clobbers A before using it).
                    j = i + 2
                    if j < len(items) and isinstance(items[j], Label):
                        j += 1
                    if j < len(items) and isinstance(items[j], Instr):
                        if items[j].mnemonic in clobbers_a:
                            # Keep stsp, drop ldsp.
                            out.append(items[i])
                            i += 2
                            count += 1
                            continue
            out.append(items[i])
            i += 1
        chunk.items = out
    return count


def pass_2_window(prog: Program, rewrite_fn) -> int:
    """Generic 2-instruction window rewrite. rewrite_fn takes
    (line_a_stripped, line_b_stripped) and returns either
      - None (no match, keep both lines as-is)
      - a list of replacement raw lines (strings)
    replacing the 2-line window. Returns count of rewrites."""
    count = 0
    for chunk in prog.chunks:
        items = chunk.items
        out = []
        i = 0
        while i < len(items):
            if (i + 1 < len(items)
                and isinstance(items[i], Instr)
                and isinstance(items[i + 1], Instr)):
                a = items[i].raw.strip().split(';')[0].strip()
                b = items[i + 1].raw.strip().split(';')[0].strip()
                replacement_lines = rewrite_fn(a, b, items[i].raw)
                if replacement_lines is not None:
                    for ln in replacement_lines:
                        # Re-parse each replacement line so the IR stays
                        # consistent (size_bytes, mnemonic, etc.).
                        out.append(parse_line(ln))
                    i += 2
                    count += 1
                    continue
            out.append(items[i])
            i += 1
        chunk.items = out
    return count


# ── T1.2: Liveness analysis ────────────────────────────────────────
#
# Forward-scan register liveness for straight-line sequences.
# Conservative on uncertainty (assumes live) so caller-side decisions
# that depend on "is this register dead?" err toward keeping code.
#
# These operate on text/mnemonic strings for reusability across the
# line-based passes that still use flat lists AND the IR-based ones.
# The text form is the stripped asm body (mnemonic + operands, no
# leading tab, no trailing semicolon-comment).


def reg_used_by_instr(text: str, reg: str,
                       func_params: Optional[dict] = None,
                       thunk_ov_arg_count: Optional[callable] = None,
                       overlay_arg_count: Optional[callable] = None) -> bool:
    """True if the instruction reads `reg`. `reg` is 'a','b','c','d'.

    For `jal <label>`:
      - If label is a user function `_foo`, look up arg count in
        `func_params[foo]`. Args ≥1 means $a read; ≥2 means $b read.
      - If label is a thunk wrapping an overlay and
        `thunk_ov_arg_count(label)` returns a count, use it.
      - Otherwise conservative: treat as True (caller passed args).
    """
    s = text.strip()
    if not s:
        return False
    parts = s.split()
    mn = parts[0]
    dollar = f'${reg}'

    if mn in ('ret', 'hlt'):
        # ret may carry return value in $a. Conservative elsewhere: dead.
        return reg == 'a'
    if mn in ('j', 'jz', 'jnz', 'jc', 'jnc'):
        # Conditional branches read flags; conservative for $a (flags set
        # by prior A-op are the common case).
        return True
    if mn == 'jal':
        # Resolve target; jal's read depends on callee's arg count.
        if len(parts) >= 2:
            tgt = parts[1]
            # User function: _foo
            if func_params is not None and tgt.startswith('_') and not tgt.startswith('__'):
                bare = tgt.lstrip('_')
                if bare in func_params:
                    ac = func_params[bare]
                    if reg == 'a': return ac >= 1
                    if reg == 'b': return ac >= 2
                    return False
            # Thunk wrapping overlay
            if thunk_ov_arg_count is not None:
                ac = thunk_ov_arg_count(tgt)
                if ac is not None:
                    if reg == 'a': return ac >= 1
                    if reg == 'b': return ac >= 2
                    return False
            # Direct _overlay_load: compiler passes index in $c; $a/$b
            # unused by the loader itself. Overlay's arg count decides.
            if tgt == '_overlay_load' and overlay_arg_count is not None:
                # Caller-determined arg count isn't visible here; conservative.
                return True
        return True

    # push/pop
    if mn == 'push':
        return len(parts) > 1 and parts[1] == dollar
    if mn == 'push_b':
        return reg == 'b'
    if mn == 'push_imm':
        return False
    if mn == 'pop':
        return False  # pop writes, doesn't read
    if mn == 'pop_b':
        return False

    # mov src, dst → reads src
    if mn == 'mov':
        mv = s.replace(',', ' ').split()
        return len(mv) >= 2 and mv[1] == dollar

    # cmp $X reads $a and $X. cmp imm reads $a only (handled in mk1cc2 via cmpi).
    if mn == 'cmp':
        if reg == 'a': return True
        return len(parts) > 1 and parts[1] == dollar

    # ALU register-register forms: reads both $a and $b (by convention).
    if mn in ('add', 'sub', 'and', 'or', 'xor'):
        return reg in ('a', 'b')

    # Unary A-ops
    if mn in ('inc', 'dec', 'sll', 'slr', 'rll', 'rlr', 'clr',
              'swap', 'tst', 'cmpi', 'addi', 'subi', 'andi', 'ori',
              'deref', 'derefp3', 'deref2', 'ideref', 'iderefp3',
              'ideref2', 'istc', 'istc_inc', 'out', 'out_imm',
              'exw', 'exr', 'exrw', 'not', 'neg', 'adc', 'sbc'):
        return reg == 'a'

    # Register inc/dec — read the named register (decb reads $b, etc.)
    if mn in ('decb', 'incb'): return reg == 'b'
    if mn in ('decc', 'incc'): return reg == 'c'
    if mn in ('decd', 'incd'): return reg == 'd'

    # stsp writes A to stack; ldsp writes A from stack.
    if mn == 'stsp': return reg == 'a'
    if mn == 'ldsp': return False
    if mn == 'ldsp_b': return False

    # VIA immediate writes — take imm, no reg read.
    if mn in ('ddrb_imm', 'ddra_imm', 'ora_imm', 'orb_imm', 'nop'):
        return False

    # ldi writes only
    if mn == 'ldi': return False

    return False


def reg_written_by_instr(text: str, reg: str) -> bool:
    """True if the instruction writes `reg`."""
    s = text.strip()
    if not s: return False
    parts = s.split()
    mn = parts[0]
    dollar = f'${reg}'

    if mn == 'ldi':
        parts2 = s.replace(',', ' ').split()
        return len(parts2) >= 2 and parts2[1] == dollar
    if mn == 'clr':
        return len(parts) > 1 and parts[1] == dollar
    if mn == 'pop':
        return len(parts) > 1 and parts[1] == dollar
    if mn == 'pop_b':
        return reg == 'b'
    if mn == 'mov':
        mv = s.replace(',', ' ').split()
        return len(mv) >= 3 and mv[2] == dollar
    if mn in ('inc', 'dec', 'sll', 'slr', 'rll', 'rlr', 'swap',
              'addi', 'subi', 'andi', 'ori', 'derefp3', 'deref',
              'deref2', 'out', 'exrw', 'ldsp', 'ldsp_b', 'exw', 'exr',
              'not', 'neg', 'adc', 'sbc', 'setz', 'setnz', 'setc', 'setnc'):
        if reg == 'a': return True
    # Register inc/dec clobber A AND the named register
    if mn in ('decb', 'incb'): return reg in ('a', 'b')
    if mn in ('decc', 'incc'): return reg in ('a', 'c')
    if mn in ('decd', 'incd'): return reg in ('a', 'd')
    return False


def reg_live_after(lines, idx: int, reg: str, **kwargs) -> bool:
    """Forward-scan liveness. `lines` may be a list of strings (flat asm
    line list as mk1cc2 uses internally) or a list of Items.

    Returns True if `reg` might be read before being overwritten by
    some path starting at lines[idx+1]. Conservative: unknown labels
    and conditional flow return True unless a definite dead-end
    (hlt/ret) is reached first. Passes **kwargs through to
    `reg_used_by_instr` (for func_params / thunk lookups)."""
    i = idx + 1
    while i < len(lines):
        # Normalize to a text string
        entry = lines[i]
        if isinstance(entry, Instr):
            s = entry.raw.strip().split(';')[0].strip()
        elif isinstance(entry, (Label, Directive, Comment, Blank)):
            s = entry.raw.strip()
        else:
            s = entry.strip() if isinstance(entry, str) else ''

        if not s or s.startswith(';'):
            i += 1; continue
        if s.startswith('section ') or s.startswith('org '):
            i += 1; continue
        if s.endswith(':'):
            # Label — peek at next non-trivial for dead-end detection
            j = i + 1
            while j < len(lines):
                entry2 = lines[j]
                if isinstance(entry2, Instr):
                    ns = entry2.raw.strip().split(';')[0].strip()
                elif isinstance(entry2, (Label, Directive, Comment, Blank)):
                    ns = entry2.raw.strip()
                else:
                    ns = entry2.strip() if isinstance(entry2, str) else ''
                if not ns or ns.startswith(';') or ns.startswith('section') or ns.startswith('org'):
                    j += 1; continue
                break
            if j < len(lines):
                entry2 = lines[j]
                if isinstance(entry2, Instr):
                    ns = entry2.raw.strip().split(';')[0].strip()
                else:
                    ns = entry2.strip() if isinstance(entry2, str) else ''
                if ns == 'hlt':
                    return False
                if ns == 'ret':
                    return reg == 'a'
            return True
        if reg_used_by_instr(s, reg, **kwargs):
            return True
        if reg_written_by_instr(s, reg):
            return False
        mn = s.split()[0] if s.split() else ''
        if mn == 'j':
            return True
        if mn in ('jz', 'jnz', 'jc', 'jnc'):
            return True
        if mn in ('ret', 'hlt'):
            return reg == 'a'
        i += 1
    return False


# ── Shared extractability / sizing primitives ────────────────────────
# These are used by multiple passes (T2.1 cross-section abstraction,
# Phase 6 within-overlay dedup, future tail-merge / CSE). Extracted
# here so behavior stays consistent across passes.

TWO_BYTE: frozenset = frozenset({
    'ldsp', 'stsp', 'push_imm', 'jal', 'jc', 'jz', 'jnc', 'jnz', 'j',
    'ldi', 'cmp', 'addi', 'subi', 'andi', 'ori', 'ld', 'st', 'ldsp_b',
    'ldp3', 'stp3', 'ocall', 'tst', 'out_imm', 'cmpi',
    'ddrb_imm', 'ddra_imm', 'ora_imm', 'orb_imm',
})


def instr_byte_size(line: str, two_byte_set: frozenset = TWO_BYTE) -> int:
    """Byte size of an asm line. 0 for labels / comments / blanks /
    directives. `cmp $X` is 1 byte (reg-reg); `cmp N` is 2 (reg-imm).
    ddrb2_imm is 3B (opcode+2imm), ddrb3_imm is 4B (opcode+3imm)."""
    s = line.strip()
    if not s or s.endswith(':') or s.startswith(';'):
        return 0
    if s.startswith('section') or s.startswith('org '):
        return 0
    parts = s.split()
    mn = parts[0]
    if mn == 'cmp':
        return 1 if (len(parts) > 1 and parts[1].startswith('$')) else 2
    if mn == 'ddrb2_imm':
        return 3
    if mn == 'ddrb3_imm':
        return 4
    if mn in two_byte_set:
        return 2
    return 1


def seq_stack_balanced(texts: list[str]) -> bool:
    """True iff the sequence has balanced push/pop — no trailing imbalance
    and no intermediate pop-without-push. `exw` (stack from IO) is rejected
    because its effective stack-delta depends on state, so it's unsafe to
    extract into a thunk body. A thunk's `ret` requires the stack top to
    be the jal-pushed return address; any imbalance breaks that."""
    balance = 0
    for t in texts:
        mn = t.split()[0] if t.split() else ''
        if mn in ('push', 'push_b', 'push_imm'):
            balance += 1
        elif mn in ('pop', 'pop_b'):
            balance -= 1
            if balance < 0:
                return False
        elif mn == 'exw':
            return False
    return balance == 0


def is_locally_extractable(text: str,
                            allow_ret_terminal: bool = False,
                            reject_ovthunk_jal: bool = False) -> bool:
    """Predicate: can this single instruction legally appear inside a
    thunk body?

    - Local-label branches (`.foo`) are rejected — their targets may not
      exist in every rewrite site.
    - `hlt` is always rejected; `ret` only allowed when
      `allow_ret_terminal=True` (tail-merge variant).
    - Stack-relative addressing (`ldsp`/`stsp`) is rejected because a
      `jal` to the thunk pushes a return address, shifting SP.
    - When `reject_ovthunk_jal=True`, `jal __ovthunk_N` is rejected
      (overlay-local symbols don't resolve cross-overlay)."""
    s = text.strip()
    if s == 'ret':
        return allow_ret_terminal
    if s == 'hlt':
        return False
    for jtype in ('j ', 'jnz ', 'jz ', 'jc ', 'jnc '):
        if s.startswith(jtype):
            tgt = s[len(jtype):].strip()
            if tgt.startswith('.'):
                return False
    if s.startswith('j ') and not s.startswith('jal'):
        return False
    mn = s.split()[0] if s.split() else ''
    if mn in ('ldsp', 'stsp'):
        return False
    if reject_ovthunk_jal and s.startswith('jal '):
        tgt = s.split(None, 1)[1].strip()
        if tgt.startswith('__ovthunk_'):
            return False
    return True


def validate_section_jumps(prog: Program, runtime_sections: set,
                            stage1_section: str) -> list[str]:
    """Cross-section jump validator. For each `jal X` or `j X` in a
    chunk whose section is in `runtime_sections`, check X's definition
    section. If X is defined in `stage1_section` only, that's a bug:
    runtime code will execute garbage after self-copy overwrote the
    stage-1 bytes.

    Returns a list of human-readable error strings. Empty list = clean.
    Local labels (starting with '.') are skipped — they're function-
    local and can't cross sections. Targets undefined in prog.labels
    are also skipped (external or yet-to-resolve)."""
    # Build label → section-name map from the IR's label index.
    label_section: dict[str, str] = {}
    for name, (chunk_idx, _item_idx) in prog.labels.items():
        label_section[name] = prog.chunks[chunk_idx].name

    errors: list[str] = []
    for chunk in prog.chunks:
        if chunk.name not in runtime_sections:
            continue
        for item in chunk.items:
            if not isinstance(item, Instr):
                continue
            if item.mnemonic not in ('jal', 'j'):
                continue
            # Extract the target from the raw line (operands may be
            # stored as a single string).
            body = item.raw.strip().split(';')[0].strip()
            parts = body.split(None, 1)
            if len(parts) != 2:
                continue
            target = parts[1].strip().split()[0]
            if target.startswith('.'):
                continue  # local label
            target_section = label_section.get(target)
            if target_section == stage1_section:
                errors.append(
                    f"{item.mnemonic} {target}: caller is in '{chunk.name}' "
                    f"(runtime), target is in '{stage1_section}' "
                    f"(stage-1 only). After self-copy, the target address "
                    f"is overwritten by kernel code — this jal will "
                    f"execute garbage."
                )
    return errors


def round_trip_identical(lines: list[str]) -> tuple[bool, str]:
    """Parse then serialize the given lines. Returns (identical, diff)
    where identical is True iff the serialization exactly matches the
    input (modulo trailing whitespace on each line). Used as a
    regression guard: if this returns False for any corpus program's
    asm, the parser is lossy for some construct we haven't covered."""
    prog = parse_program(lines)
    out = serialize_program(prog)
    in_trimmed = [ln.rstrip('\n').rstrip() for ln in lines]
    out_trimmed = [ln.rstrip('\n').rstrip() for ln in out]
    if in_trimmed == out_trimmed:
        return True, ''
    # Minimal diff: show first mismatch
    for i, (a, b) in enumerate(zip(in_trimmed, out_trimmed)):
        if a != b:
            return False, f'line {i}: {a!r} != {b!r}'
    if len(in_trimmed) != len(out_trimmed):
        return False, f'length diff: {len(in_trimmed)} vs {len(out_trimmed)}'
    return False, 'unknown mismatch'
