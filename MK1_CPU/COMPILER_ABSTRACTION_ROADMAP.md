# MK1 Compiler: Abstraction Roadmap

**Status**: active roadmap, 2026-04-19
**Author**: Claude (drafted), HeathenUK (owner)
**Scope**: mk1cc2.py

## Motivation

The current compiler has hand-coded special cases for code-sharing. Examples:
- `__lcd_chr` / `__lcd_cmd` merge via shared `__lcd_send` tail (mk1cc2.py ~line 2013)
- `__i2c_st` / `__i2c_sp` stripped from kernel when inlined into `__lcd_chr`
- Init-only helper extraction, bundled overlay helpers, knapsack-based residency
- Phase 6 procedure abstraction (within a single overlay only)

Every "helpers bloat the kernel" bug has historically produced either:
1. A hand-coded merge (future-me has to remember it), or
2. A workaround (`lcd_clear()` inlines a raw delay to avoid `__delay_Nms`, breaking the "always calibrated delays" rule).

**Goal**: replace special cases with general, whole-program passes that find and exploit redundancy automatically. Programs that today overflow by 50B should compile cleanly; programs that today compile cleanly should shrink 10–20%.

## Target: user writes up to ~2000B of C without thinking about structure

The compiler partitions it automatically across the 250B code page, 3 SRAM pages, and 4KB EEPROM.

---

## Foundation (T1) — unlocks everything else

### T1.1 — Whole-program IR

Currently each section (kernel, stage-1, init, each overlay) is emitted as a flat list of asm lines. Passes see one list at a time. Introduce a unified IR: `(section_tag, label_scope, [instr])`. Every optimization pass operates on the whole program at once.

**Foundational** — most of what follows is blocked on this. Cross-section abstraction (T2.1) is literally impossible without it.

### T1.2 — Flow-sensitive liveness + clobber analysis

Per instruction: live-in / live-out set over `$a $b $c $d $sp`.
Per helper: precise register clobber set (not today's conservative "everything").

Unlocks T3.x (call-convention elision) and sharper peephole.

---

## Parametric abstraction (T2) — the big unlock

Subsumes today's hand-coded merges. Everything in this tier operates on the whole-program IR from T1.1.

### T2.1 — Cross-section procedure abstraction

Today's Phase 6 runs only inside a single overlay. Extend the suffix-array scan to all sections simultaneously. A sequence that appears in kernel + two overlays becomes a resident thunk (or two bundled copies, whichever knapsack prefers).

### T2.2 — Parametric matching

Two sequences that differ *only in immediate operands* are a match. Extract as a thunk with the differing immediate passed in a register:

```
Before:
  __lcd_chr: push $a; ldi $a, 0x09; j __lcd_send
  __lcd_cmd: push $a; ldi $a, 0x00; j __lcd_send
After (automatic):
  __lcd_write(RS_bit in $b): push $a; mov $b, $a; j __lcd_send
  __lcd_chr: ldi $b, 0x09; j __lcd_write
  __lcd_cmd: ldi $b, 0x00; j __lcd_write
```

This is exactly the hand-coded merge, done generically. Also catches duplicated I2C device-address prologues, duplicated PCF8574 framing, etc.

### T2.3 — Tail merging

If helper A's last *N* instructions are byte-identical to helper B's last *N*, A falls through into B's tail. Classic compiler trick, saves `N × S` bytes. Already happens for `__lcd_chr`/`__lcd_cmd`/`__lcd_send` by hand — generalize.

### T2.4 — Specialization + cloning

If `__lcd_cmd` is called 4 times with a constant byte and once with a variable byte, emit a specialized `__lcd_cmd_0x01` (Clear Display) with the byte baked in — no caller-side `ldi $a, …` / `push $a` overhead. Plus the generic body for the variable call. Knapsack decides profitability.

---

## Call-convention micro-optimization (T3) — requires T1.2

### T3.1 — Liveness-based save/restore elision

Today every overlay call site does `push $b; push $a; … pop $a; pop $b`. If liveness says `$b` is dead across the call, drop the `push $b / pop $b` pair (–2B per elided pair).

### T3.2 — Rematerialization vs save

If `$a` was set by `ldi $a, 5` and is needed after a clobbering call, re-emit `ldi` post-call (2B) instead of `push $a / pop $a` (2B + SP math). Often a wash byte-for-byte, but unblocks peephole chains.

### T3.3 — Thin overlay dispatch

Phase 2 of the existing overlay plan. Current `_overlay_load` call site is 10–15B of ceremony. With liveness, a minimal call site is 4–5B.

---

## Peephole / superoptimizer (T4)

### T4.1 — Brute-force N≤3 superoptimizer

~30 opcodes × 3-instruction window is tractable. For each window, enumerate shorter equivalent windows (byte count ≤ original), verify equivalence via the simulator on a random register/memory fuzz. Ship the canonical replacements as a peephole table. One-time cost, permanent win.

### T4.2 — AST-level idiom recognition

`while (t >= 10) { t -= 10; tens++; }` → divmod intrinsic → smaller emission. Also: shift-by-constant, power-of-two multiply, bit-test chains. Front-end work, high ROI for arithmetic-heavy programs.

---

## Cross-program (T5)

### T5.1 — Synthesized runtime library

Run T2 across a *corpus* of existing MK1 programs (everything in `MK1_CPU/programs/`). Any sequence that appears in 3+ programs becomes a named library helper, emitted only when referenced. LCD/I2C/RTC/EEPROM naturally cluster into reusable primitives.

### T5.2 — Semantic intrinsics

`i2c_sequence({START, 0xD0, 0x11, REPEAT_START, 0xD1, READ})` as a single builtin that emits a byte-coded interpreter call. The `__i2c_stream` helper already exists in the compiler — generalize the pattern.

---

## Validation infrastructure (V)

These come **first**. You can't optimize what you can't measure or trust.

### V1 — Golden sim tests for every builtin

For each `lcd_*`, `rtc_*`, `eeprom_*`, `i2c_*` builtin: a minimal C program whose simulator trace is checked byte-for-byte. Would have caught `lcd_clear()` `$a`/`$d` swap at compile time instead of at hardware-debug time.

### V2 — Size-regression harness

Every program in `MK1_CPU/programs/` gets a recorded kernel / stage-1 / overlay byte count. CI fails on regression. Makes every pass quantifiable.

### V3 — Differential testing

Compile each regression program with each optimization pass individually toggled off; verify identical simulator behavior (but different sizes). Catches passes that miscompile.

---

## Priority & dependencies

```
V1 / V2 / V3 ── FIRST
    │
    ├─→ T1.1 (IR) ─────┬──→ T2.1 ──→ T2.2 ──→ T2.3 ──→ T2.4
    │                  │
    └─→ T1.2 (liveness)┴──→ T3.1 ──→ T3.2 ──→ T3.3

T4.1 (superopt)  ── independent, run anytime
T4.2 (AST idioms) ── independent

T5.x ── after T2 mature
```

---

## Expected cumulative gains

| Tier done          | Typical LCD+RTC program       | Ceiling on dashboard-class programs |
|--------------------|-------------------------------|--------------------------------------|
| Today              | 315B kernel, 2–3 overlays max | ~300–400B total C                    |
| + T2               | 240B kernel, 4–5 overlays     | ~700B                                |
| + T2 + T3          | 220B kernel                   | ~850B                                |
| + T2 + T3 + T4     | 200B kernel                   | ~1000B                               |
| All                | 180B kernel, +EEPROM tier     | ~2000B (plan's stated goal)          |

---

## The meta-win

Today, every "helpers bloat the kernel" bug gets a hand-coded merge or a workaround. Each special case is a place future-me has to remember. T2 replaces them with a general mechanism: helpers are just code, and the compiler finds the sharing.

---

## Recommended first cut

**V2 size-regression harness + T2.1 cross-section abstraction.** That combination gives immediate, measurable, compounding returns without requiring the full IR refactor. V2 lands the safety net; T2.1 proves the approach on real sharing opportunities already present in the codebase.

## Related plans

- `/Users/gadyke/.claude/projects/-Users-gadyke-8bit-cpu/memory/reference_overlay_plan.md` — 7-phase overlay plan (knapsack, thin dispatch, SCC, EEPROM, tone, auto-split). Partial overlap with this roadmap; the overlay plan is more about storage partitioning, this roadmap is about code sharing.
- `/Users/gadyke/.claude/projects/-Users-gadyke-8bit-cpu/memory/project_phase6_procedure_abstraction.md` — the existing Phase 6 (within-overlay thunk extraction). T2.1 generalizes it to cross-section.
