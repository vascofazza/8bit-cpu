# Two-Region Overlay with Helper Paging + Tail Chaining

**Status:** Design accepted 2026-04-22. Implementation pending.
**Authority:** This document is the canonical design for the next-generation MK1 overlay system. When it conflicts with `OVERLAY_SYSTEM.md` (which documents the current, to-be-replaced system), this doc wins.
**Scope:** Compiler architecture (`mk1cc2.py`), runtime loader, Phase 7 splitting.
**Replaces:** Current helper-bundling + wrap-safety-retry + knapsack-resident scheme.

## Read-first checklist

Before making any compiler change that touches the overlay system:

1. Read this document in full.
2. Check `project_stage1_layout_bugs.md` in memory for the four stage-1 bugs fixed on 2026-04-22.
3. Check `project_storage_hierarchy.md` in memory for the 4-tier storage model.
4. Confirm your change aligns with §4 (Proposed Design). If it doesn't, either update this doc first or argue for an exception in writing.

## 1. Executive Summary

The MK1 has a 250-byte executable code page and ~1KB of fast SRAM across pages 1-3, plus 4KB of EEPROM. Real programs need 300-500B of code. The existing compiler handles this by copying user functions from page 3 into an "overlay region" at the end of the code page, with each overlay bundling the helpers it calls. **This is the source of every remaining correctness and fit problem.**

Bundling duplicates helper bodies across overlays; each overlay ends up bigger than the region; the compiler tries promoting helpers to resident status but the per-overlay-excess math is invariant under promotion (proved in §3), so ~12 programs silently generated code that smashed `_overlay_load` on the second call. As of 2026-04-22 the compiler catches this statically (`wrap past code[255]` error), but those 12 programs now fail to compile at all.

This design replaces bundling with **two overlay regions**: one for user code (`R_user`), one for helpers (`R_helper`). Helpers become their own overlays, loaded on demand via kernel thunks. Phase 7 is simplified to emit **tail-chained** overlay sequences instead of main-dispatched phase calls.

Expected results:
- Kernel shrinks 60-90B (helpers moved out)
- Overlay region per user function grows 60-80B
- ~11 currently-failing programs compile
- ~500 lines of bundling/knapsack/wrap-safety logic deleted
- Per-helper-call overhead ~170 cycles (acceptable for LCD/I2C work; resident leaf helpers for inner loops)

## 2. Current architecture (inventory)

### The boot sequence (KEEP — works well)

- Stage-1 at code[0..250] runs from cold start: mini-copy → pre-mc helpers → init code → self-copy → `j _main`
- Self-copy blits page 3's stage-2 kernel image into code[0..199]
- Overlays live in page 1/2/3/EEPROM, loaded into code[OVERLAY_REGION..250] on demand

### The stage-2 kernel (REPLACE — broken model)

```
code[0..1]     j _main
code[2..~42]   _overlay_load  (~40B)
code[~42..N]   RESIDENT HELPERS  (__i2c_sb, __lcd_chr, __lcd_cmd,
                                  __print_u8_dec, ... — 80-100B total)
code[N..M]     _main body
code[M..249]   overlay region  (~30-60B, shrinks as kernel grows)
```

The resident helpers list is decided by a knapsack over `(times-used × size)` against kernel budget. Anything not resident is **bundled** into every overlay that calls it: `__lcd_chr_ov0` label, full body appended to the overlay body, label-renamed so multiple overlays don't collide.

### Cruft inventory (to be deleted)

These exist only because of bundling:

| Component | Approx lines | Role | Post-redesign |
|---|---|---|---|
| `_ovN` suffix renaming | ~50 | rewrites jal targets and labels per overlay | **delete** |
| `bundleable_helpers` + `all_needed` scan | ~80 | decides what to copy into each overlay | **delete** |
| `_NO_OVERLAY` dynamic set | ~30 | ad-hoc "keep this one resident" mechanism | **delete** |
| Helper knapsack (step 8b + Phase 6) | ~200 | cost/benefit for bundle vs resident | **replace with leaf-set** |
| Wrap-safety detection + retry | ~120 | late check when overlays exceed region | **delete** (wraps impossible) |
| `__xsthunk_N` cross-section extract | ~300 | find repeated sequences to dedup | **keep but trivialized** (helpers aren't duplicated) |
| Phase 7 live-var branching (0/1/2/N) | ~150 | separate code for each live-var count | **collapse to one path** |
| Per-overlay manifest with page tag | ~40 | flexible page dispatch | **keep, extend with region flag** |

Other cruft surfaced during the 2026-04-22 session, unrelated but noted:

- `INIT_COMPAT_HELPERS` has grown organically (now includes `__delay_cal` from the init-move fix). An AST-level "init-phase function" marker would be cleaner than the name-set.
- `mk1_py_asm.py` diverges from the ESP32 assembler. I found jnz-target byte disagreement on 2026-04-22. Decide before the redesign lands: either fix py_asm to match, or retire it and rely on the ESP32 assembler as the single source of truth.

## 3. Problem the redesign solves

### The bundling-promotion math (verified empirically)

Helper `h` bundled in `B` of `N` overlays, region size `R`, largest overlay size `V`:

- **Before promotion:** excess per wrapping overlay = `V - R`
- **Promote `h` resident:** kernel grows by `+h`, region shrinks by `-h`, each of `B` bundled overlays shrinks by `-h`
  - For the B bundled overlays: new excess = `(V - h) - (R - h) = V - R` — **invariant**
  - For the other N-B overlays: new excess = `V - (R - h) = V - R + h` — **grows by h**

**Promotion cannot fix wraps.** I verified this on the corpus (2026-04-22). The compiler's wrap-retry promotes helpers in a loop; every promotion leaves wrap-excess unchanged for the affected overlay and worsens it for others.

### The redesign's insight

The problem is that helpers *count against the user overlay's size budget*. If helpers live in a **separate region**, user code budget is only user code. A 50B user function fits in a 50B user region — no bundling, no wrap, no math trap.

## 4. Proposed Design

### 4.1 Physical code-page layout

```
code[0..1]          j _main                         (2B reset vector)
code[2..~42]        _overlay_load  (unified)        (~40B)
code[~42..~70]      leaf helpers:                   (~28B)
                    __i2c_sb (25B), __i2c_sp (3B inline)
code[~70..~95]      helper thunks:                  (~25B)
                    __lcd_chr, __lcd_cmd, __i2c_st,
                    __print_u8_dec, __tone, ...
                    (4-5B each)
code[~95..~155]     _main body                      (~60B max after init extraction)
code[~155..~195]    R_helper  (helper overlay)      (~40B)
code[~195..~250]    R_user    (user overlay)        (~55B)
```

Total kernel: ~155B. Two overlay regions total: ~95B. Slack up to 100B for programs with small `_main`.

Sizes adjust per program — `_main` grows, regions shrink, etc. The loader's `R_helper`/`R_user` addresses are compile-time constants chosen after measuring the kernel. The compiler selects them during placement.

### 4.2 Unified loader

```asm
_overlay_load:
    ; input: $c = manifest index
    ; 3-byte manifest entries: [src_page_tag, src_offset, size_and_region_flag]
    ; size_and_region_flag: low 7 bits = size (0-127),
    ;                       high bit  = 0 → R_user, 1 → R_helper
    push $b
    push $a
    mov $c, $a
    sll
    add $c, $a           ; A = C*3
    addi __manifest, $a
    mov $a, $d
    derefp3              ; A = page_tag (0=p1, 3=p3, 0xEE=eeprom)
    ; <dispatch on page_tag to the right deref op>
    ; <each copy loop knows dest = R_user or R_helper based on the flag>
    pop $a
    pop $b
    j R_dest             ; tail-jump; NOT ret
```

**Key property:** the loader ends with `j R_dest`, never `ret`. Caller style (`jal _overlay_load` vs `j _overlay_load`) determines whether the loaded overlay's `ret` returns to the caller or to the caller's caller. This is what makes overlay chaining (§4.5) free.

Unified ~40B; handles p1/p3/EEPROM source pages and R_user/R_helper destinations.

### 4.3 Helper thunks

For each helper promoted to overlay status:

```asm
__lcd_chr:               ; 4B thunk in kernel
    ldi $c, LCD_CHR_IDX
    j _overlay_load      ; manifest entry has R_helper flag set
```

Call site stays 2B: `jal __lcd_chr`. Unchanged from resident-helper days. The thunk handles loading R_helper transparently.

**Leaf helpers** (kept resident): the ones called from helper bodies themselves, or small enough that the thunk overhead (4B) rivals the body. Current candidates:

- `__i2c_sb` (25B, called from `__lcd_chr`, `__lcd_cmd`, `__i2c_st`) — **resident (non-negotiable)**
- `__i2c_sp` (3B) — inline where used
- `__delay_Nms` (12B) — resident if used

**Leaf rule:** a helper is leaf (resident) iff
```
body_size < 15B
  OR
called from the body of another overlay helper
```

The second clause prevents nested overlay loads (which would clobber R_helper mid-execution).

For the current MK1 helper graph: `__i2c_sb` is called by `__lcd_chr`, `__i2c_st`, `__i2c_sp`. So `__i2c_sb` must be resident. `__lcd_chr` calls only `__i2c_sb`, so `__lcd_chr` can be overlay. Dependency graph is shallow (depth ≤ 2); rule is easy to satisfy.

### 4.4 User overlay call sites

Unchanged from today's T3.3 thin dispatch:

```asm
ldi $c, IDX
jal _overlay_load       ; 4B inline at call site
```

The only difference is the manifest entry's region flag is clear (R_user). Call semantics: `jal _overlay_load` pushes a return; loader `j R_user`; user overlay `ret` pops it.

### 4.5 Tail-chain overlay (replaces Phase 7 multi-call)

**Today:** Phase 7 splits `show_temp` → `show_temp_p1` + `show_temp_p2`. Main calls both:

```c
tmp = show_temp_p1(arg);
show_temp_p2(tmp);
```

Costs: two call sites in main, two xfer globals, phase2 prologue reloads.

**New:** `show_temp_p1`'s body ends with a tail-chain:

```asm
; ...show_temp_p1 work; live vars written to page1 globals...
ldi $c, SHOW_TEMP_P2_IDX
j _overlay_load       ; j, not jal
```

Because the loader ends with `j R_user`, the tail `j` path through the loader is a clean tail-call into `show_temp_p2`. When `show_temp_p2`'s `ret` executes, it pops the *original `jal show_temp`* return from main.

Main unchanged: just one `jal show_temp`. Phase boundaries are invisible to main.

**Phase 7 collapse** (pseudocode):
```python
def _auto_split_functions(self, functions):
    for f in functions:
        if _estimated_size(f) <= R_USER_SIZE:
            yield f; continue
        chain = _split_into_chain(f, R_USER_SIZE)  # N pieces
        for i, piece in enumerate(chain):
            if i < len(chain) - 1:
                # tail: save live vars to page1, then tail-chain
                piece.body.append(_emit_xfer_save(live_at_boundary[i]))
                piece.body.append(('tail_chain', chain[i+1].idx))
            yield piece
```

No more N-way live-var special casing. Live vars across all phase boundaries go through page 1 globals. Uniform.

### 4.6 Manifest

```asm
__manifest:                              ; 3 bytes per entry
    byte PAGE_TAG, OFFSET, SIZE_AND_REGION
    byte PAGE_TAG, OFFSET, SIZE_AND_REGION
    ...
```

`SIZE_AND_REGION`: low 7 bits = size (0-127B; fits both regions comfortably), high bit = region (0=R_user, 1=R_helper).

Since sizes fit 7 bits (R_user ≤ 60B, R_helper ≤ 40B), packing is cleaner than a separate region table. `~3B × (user_overlays + helper_overlays)`. Manifest stays in page 3 after kernel image.

### 4.7 Compiler pipeline after redesign

```
parse → typecheck → codegen
  → Phase 7 (split-if-needed, emit tail-chains)
  → Helper classification (leaf vs overlay, by leaf rule §4.3)
  → Emit kernel (loader, main, leaf helpers, thunks)
  → Emit overlays (user + helper) + manifest
  → Stage-1 init + self-copy
```

Gone from the pipeline:

- Step 8b knapsack (replaced by simple leaf-set determination)
- Step 9 bundling
- Step 9b per-overlay validation
- Step 15 wrap-safety retry
- `_NO_OVERLAY` mutations
- `_ovN` renaming

## 5. Migration plan

### Phase 0 — py_asm byte-equivalence (HARD PREREQUISITE, 0.5-2 days)

**No work on Phase A may start until this is complete.** During the 2026-04-22 session I found that `mk1_py_asm.py` and the ESP32 `assembler.h` emit different bytes for the same source around `jnz LABEL; j LABEL2` sequences (py_asm drops one byte). The overlay redesign touches loader byte sequencing heavily; debugging it with divergent assemblers would be untenable.

1. **Audit py_asm against `assembler.h`**. For each opcode that takes an immediate (jnz, jz, jc, jnc, j, jal, ldi, cmpi, tst, addi, subi, andi, ori, ddrb_imm, ddrb2_imm, ddrb3_imm, push_imm, out_imm, derefp3 with offset, etc.): compile a tiny program exercising it, diff the ESP32 DUMP output against py_asm's output. File each divergence.
2. **Decision fork based on audit results:**
   - If ≤3 distinct divergences: **patch py_asm** in place.
   - If ≥4 divergences: **port `assembler.h` to Python** as a mechanical mirror (Option C in §6 risks). Treat `assembler.h` as the canonical spec; py_asm becomes its Python translation. This is more honest than accumulating patches.
3. **Add a byte-equivalence regression** that compiles every program in the corpus through both assemblers and fails if any byte differs. Run it before every compiler commit going forward.
4. **Verify on hardware** that the known-hung programs from 2026-04-22 (lcd_temp.c, overlay_dashboard, etc.) produce identical bytes between py_asm and ESP32 after the fix.

Gate: only after Phase 0 passes — `overlay_regression_test.py` + byte-equivalence regression + hardware spot-check — does Phase A begin.

### Phase A — infrastructure behind flag (2 days)

1. Write new `_overlay_load` with region dispatch in a new function `_emit_loader_v2`
2. Add `__manifest` generation with region flag bit (§4.6)
3. Emit helper thunks for a hardcoded set of helpers (`__lcd_chr`, `__lcd_cmd`, `__print_u8_dec`)
4. **Gate behind `MK1_HELPER_OVERLAY=1` env var** — old path still default
5. Test one program (lcd_temp.c) in both modes, verify semantic equivalence on hardware

### Phase B — default flip (1 day)

1. Make new path the default; old path behind `MK1_LEGACY_OVERLAY=1` for emergency revert
2. Verify 13/13 regression still passes
3. Verify ~8 of 11 currently-failing programs now compile
4. Debug holdouts (they likely need the tail-chain from Phase C)

### Phase C — tail-chain Phase 7 (1 day)

1. New `_auto_split_functions` emits chains (see pseudocode §4.5)
2. Emit `tail_chain` pseudo-instruction; codegen lowers to `ldi $c, N; j _overlay_load`
3. Delete old Phase 7 per-live-var branches (0/1/2 special cases)

### Phase D — delete cruft (0.5 day)

1. Remove `_NO_OVERLAY`, bundling, knapsack, wrap-safety retry, `_ovN` renaming (§2 cruft inventory)
2. Remove legacy-mode gate once new path is confirmed stable
3. Remove dead imports, unused params
4. Re-run corpus + regression
5. Update memory notes: retire `project_compiler_overlay_system.md`, add new note pointing to this doc

**Total: ~5-6.5 days careful work** (Phase 0 + A + B + C + D). Risk is contained because Phase 0 catches assembler divergences up front, and Phases A/B are gated behind a flag.

## 6. Risks and honest tradeoffs

### Performance

Every helper call now costs a page-3 read + copy into R_helper. Measured on hardware (2026-04-22): ~4269 cycles per `lcd_char` call including the helper load + I2C transmission. Helper copy alone is ~6 cycles per byte = ~250-400 cycles per load depending on body size. A program with 30 `lcd_char` calls spends ~10k cycles (~40ms at 250kHz) on helper loading — **dwarfed by I2C bus time (~4ms per char) and any LCD-timing delays**, so acceptable for LCD work.

For tight inner loops (`__i2c_sb` in a byte-send), this overhead would be fatal, which is why `__i2c_sb` stays resident (leaf rule §4.3).

### Nested overlay loads

The redesign **assumes helpers don't call other overlay helpers.** If `__lcd_chr` calls `__lcd_send` and both are overlays, the second load clobbers the first mid-execution. Mitigation: the leaf rule (§4.3) forces any helper-called-from-another-helper to be resident. The MK1 helper graph is shallow (depth ≤ 2), so this is not onerous.

### Stage-1 interaction

Init-only helpers stay on their current path. `__lcd_init`, `__delay_cal`, `__i2c_st`/`__i2c_sp` when only used at init — still live in stage-1 and are wiped by self-copy. Zero changes there.

Stage-1 mini-copy is still needed for the leaf helpers + thunks that live in page 3 after self-copy. Same mechanism, smaller set to copy.

### Size regression on passing programs

Programs that today fit comfortably with bundling might grow because the helper thunks + loader add overhead. Rough estimate:
- Programs with ≤2 overlay helpers: gain nothing or lose 5-15B
- Programs with ≥3 overlay helpers: win 30-80B

Measure on corpus before committing. Expect small (2-5%) regressions on the 13 regression tests, big wins on the 11 failing programs.

### py_asm divergence from ESP32 assembler (RESOLVED — see Phase 0)

Found during 2026-04-22 debug: `mk1_py_asm.py` emits different bytes around sequences like `CE 04 3D 1D` (jnz then j). ESP32 is correct; py_asm collapses bytes. This caused confusion during wrap-safety debugging.

**Decision (2026-04-22):** fix py_asm to match ESP32 byte-for-byte, add a byte-equivalence regression that runs on every commit. Fallback to a mechanical port of `assembler.h` if the audit finds 4+ distinct divergences. Offline simulation is valuable enough to justify keeping py_asm if it can be made trustworthy; the regression test prevents re-divergence.

See Phase 0 of the migration plan (§5).

### What this doesn't solve

Programs where `_main` itself is too big. After init extraction `_main` is usually ≤50B, but a program like `oled_text` with a lot of control flow in main might still exceed. Phase 7 currently splits main at I2C→LCD boundaries; that stays. If `_main` still won't fit after the redesign, "main as chain" is a Phase E follow-up.

## 7. Open questions

1. **Leaf-helper rule** — is the dependency graph really depth ≤ 2 across all current and plausibly-future helpers? Need a quick audit of helper call-graph before committing.
2. **Two fixed regions vs one region with re-loading** — two regions is simpler but wastes budget when a program uses only user overlays or only helper overlays. Worth a prototype measurement on the corpus.
3. **py_asm cleanup sequencing** — before, during, or after the redesign? Argues for before; the redesign touches a lot of loader byte sequencing, and we need a trustworthy local simulator during development.
4. **Init-phase classification cleanup** — `INIT_COMPAT_HELPERS` has grown organically. Worth replacing with an AST-level marker as part of the Phase D cleanup pass.

## 8. Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-04-22 | Design accepted (this doc) | Per-overlay bundling mathematically cannot close wrap gap; two-region design is the simplest structural fix |
| 2026-04-22 | Today's stage-1 + wrap-safety fixes kept as-is | Real bugs, not superseded by redesign; wrap-safety check becomes an assertion that should never fire after redesign |
| 2026-04-22 | `__delay_cal` init-only kept | Orthogonal to redesign; fixes `twinkle`/`twinkle_v2` immediately |
| 2026-04-22 | py_asm cleanup is Phase 0 prerequisite | Divergence between py_asm and ESP32 caused real confusion during wrap-safety debugging; would compound during an overlay-system rewrite. Fix-in-place + byte-equivalence regression test; fall back to mechanical port if audit finds ≥4 divergences. |
| 2026-04-22 | Phase 0 partially complete (42/60 corpus bytes-equiv) | Fixed: missing 2-byte flags on `jnz`/`jnc` (microcode `has_imm` was True but not in py_asm's set), flag-skip opcodes `jcf`/`jzf`/`je0`/`je1` (microcode has_imm=False but are 2-byte via PE), `stor $pc, [$sp]` (post-hacked in microcode, flag not updated), `cmp N` translation (py_asm emitted `cmp imm` opcode 0x86; ESP32 emits `cmpi` 0xFD), `data_code`/`stack_code`/`page3_code` section byte emission (py_asm wrote nothing or to wrong buffer). Remaining 18 corpus divergences are in overlay programs — small (2-20 bytes each) and concentrated in manifest/overlay-body layout that the redesign will rewrite from scratch. Deferring the final cleanup until after Phase A lands and the new loader/manifest format stabilises. |
| 2026-04-22 | Phase A spike works on hardware | Hand-assembled proof of concept at `MK1_CPU/programs/spikes/helper_overlay_v1.asm`. Emits A0, A1, B0, A2 in order — demonstrating: (1) kernel thunk (`__hello`) dispatches to helper loader, (2) loader copies helper from page3 into R_helper (code[230..]) and tail-jumps, (3) helper body executes and `ret`s directly back to `_main`'s caller, skipping the loader's stack frame. 183 cycles from A1→B0 (includes the copy loop of 3 bytes). Architecture is sound; moving to compiler integration. One non-obvious gotcha found: `org N` inside `section page3_code` in ESP32's assembler emits HLT pad bytes up to N into the page3 buffer, not just bumping the virtual PC — use raw `section page3` with `byte` directives for helper bodies that don't need internal label resolution. |
| 2026-04-22 | Phase A compiler integration: first helper live | `_apply_helper_overlay_transform` in `mk1cc2.py` gated on `MK1_HELPER_OVERLAY=1`. Moves `__lcd_chr` and `__lcd_init` to a shared R_helper region (sized dynamically past the loader). Kernel shrinks ~44B on the test program. Works end-to-end on hardware: lcd_init + lcd_char('A') + lcd_char('B') displays "AB" on the LCD. Four gotchas landed: (1) body bytes must be snapshotted POST-peephole or instruction encoding diverges (`ldi $a,N; push $a` doesn't collapse to `push_imm N`, causing $a clobber of the caller's argument); (2) external label addresses must come from POST-peephole assembly too, off-by-1 per peephole collapse before the helper; (3) body assembly needs `org R_HELPER_BASE` so internal `.local:` labels resolve to runtime addresses, not org 0; (4) R_HELPER_BASE must be computed DYNAMICALLY after kernel-end measurement — hardcoding (180) collides with the loader's own code. |
| 2026-04-22 | Three-layer Phase A regression test | `MK1_CPU/code/helper_overlay_test.py` committed. Layer 1 offline: byte-semantic equivalence with internal-jump rebasing (would catch today's LCD bug in <1s). Layer 2 hardware: OI marker trace with HLT_GRACE-aware matching. Layer 3 hardware: resident vs overlay I/O side-effect equivalence via RTC-temp round-trip (catches subtle I2C corruption neither layer above would see). Every future widening of HELPER_OVERLAY_NAMES runs through all three before declaring "done". |
| 2026-04-22 | Leaf-rule enforcement + "no room" fallback | Extending the overlay set to `__print_u8_dec` exposed the leaf-rule violation the design doc warned about: `__print_u8_dec` calls `__lcd_chr`; if both overlay into R_helper, the nested load clobbers the caller mid-execution. User saw the symptom: printf produced "lots of 4 digits" on the LCD instead of "42". Two safeguards added: (a) transform scans each candidate's body for `jal` into the overlay set and demotes callers to resident before emission, restarting until the set is leaf-consistent; (b) when the transform would overflow the 250B code page, the transform reverts its own mutations (restores `_saved_pre_transform`) and the compile falls back to resident helpers for that program. Programs that genuinely benefit still get the win; programs that can't fit silently use the existing path. |
| 2026-04-22 | Overlay-mode Phase A still pending | Current transform is flat-mode only — it skips (`return`) when invoked on an overlay-mode program, falling back to the existing bundling path. This is the point of the design: ~11 corpus programs that today silently emit broken code or fail to compile are all overlay-mode. Phase A without overlay-mode support is a proof of mechanism, not a real win. Follow-up must carve R_helper from within the existing user overlay region (or immediately above it) and integrate thunks + manifest into `_overlay_partition`'s output. Concretely: reserve code[250-R_HELPER_SIZE..249] for R_helper, shrink OVERLAY_REGION's upper bound accordingly, emit helper thunks in the kernel, and emit `_load_helper` alongside `_overlay_load`. |
| 2026-04-22 | Phase A overlay-mode inline split + cost-benefit guard | `_split_helpers_for_overlay` runs inside `_overlay_partition` after T2.1 and before kernel sizing. Bodies of helpers in `HELPER_OVERLAY_NAMES` that land in `runtime_resident_helpers` (the natural classification set) are replaced with 4B thunks and `_load_helper` is appended. `OVERLAY_REGION` then sizes correctly against the reduced kernel. The ceiling check at line ~5778 and the final `avail = 250 - OVERLAY_REGION` shrink by `R_HELPER_SIZE` so user overlays cannot extend into R_helper. Post-partition emission (`_emit_helper_overlay_bodies`) pre-assembles bodies with external labels resolved from a full-program assembly pass, then writes raw `byte` directives in page3 — manifest entries (`byte __h_body_N; byte size`) resolve correctly at the assembler's second pass. **Cost-benefit guard** in `_split_helpers_for_overlay`: reject when `len < 2` or `kernel_save <= overlay_cost`. Single-helper extraction paid 28B loader + max(body) reserve to save `body - 4B` — measured -32B net on lcd_temp_overlay, so the guard rejects it. |
| 2026-04-22 | Phase B attempt found: needs unified loader + per-program decision + Phase C | Phase B step-2 ("verify 13/13 regression still passes") and step-3 ("~8 of 11 failing programs now compile") did **not** land. Three concrete findings: **(1) Disabling bundling wholesale regresses 16 programs** — they depend on the knapsack keeping SOME helpers resident and bundling others. The design assumes every non-leaf helper is paged, but that only wins when the loader (~28B) is amortized across multiple extractable helpers AND R_HELPER_SIZE (max body) fits within the overlay-region gain. For programs with one big helper (e.g. __lcd_chr at 41B), paging costs 41+28 = 69B vs resident costs 41B → paging is -28B. **(2) Pinning helper-paging candidates resident (keeping them in `_NO_OVERLAY`) regresses 8 programs.** Candidates grow the kernel beyond the available budget; extracting them back shrinks it but the net often isn't enough to re-fit the overlays. **(3) None of the ~10 failing-baseline programs compile with helper-paging alone.** They fail because overlay bodies are 70-90B while R_user ≈ 40-50B. Paging does grow R_user (by kernel_save-R_HELPER_SIZE) but not enough to cross the gap. Design doc §5 Phase B step-4 already flagged this: "debug holdouts (they likely need the tail-chain from Phase C)". What's still missing before Phase B lands: **(a) Unified loader (§4.2)** — one loader for R_user + R_helper saves ~28B kernel over the current two-loader setup; **(b) Per-helper paging decision** instead of a global flag — knapsack extended to consider (resident / bundled / paged) per helper and pick the cheapest; **(c) Phase C tail-chain** to eliminate 10-20B per overlay from Phase 7 split boundaries. Kept from this session: the widened HELPER_OVERLAY_NAMES set ({__lcd_chr, __lcd_cmd, __lcd_send, __print_u8_dec, __print_u8_hex, __i2c_rb, __i2c_rs}), auto-inclusion of __lcd_send when __lcd_chr/__lcd_cmd are used (it's emitted implicitly), and the fall-through terminator injection (append `j __lcd_send` when __lcd_cmd body has no ret/j/jal, so the extracted body doesn't run off into HLT padding). Cost-benefit guard restored to the strict form; 0 corpus diffs between flag on/off. |
