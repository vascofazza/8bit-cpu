# MK1 Overlay System Design

## Overview

The MK1 compiler (`mk1cc2.py`) automatically partitions C programs that exceed
the 250-byte code page into overlays — self-contained code segments stored in
SRAM pages and loaded to the code page on demand. Users write standard C
without worrying about code size.

## Architecture

### Two-Stage Boot

```
Stage 1 (init):  Full 256B code page
  VIA init → delay calibration → LCD init → self-copy → j 0

Stage 2 (runtime):  Kernel + overlay region
  code[0..K-1]           = Kernel (loader + main + resident helpers)
  code[K..249]           = Overlay region (loaded on demand)
```

The kernel is stored in page 3 and self-copied to the code page. Init code
runs once and is overwritten by the kernel.

### Storage Hierarchy

| Tier | Storage | Capacity | Access | Speed |
|------|---------|----------|--------|-------|
| 1 | Page 3 SRAM | ~170B | `derefp3` | fast |
| 2 | Page 1 SRAM | ~210B | `deref` | fast |
| 3 | Page 2 SRAM | ~196B | `deref2` | fast (DISABLED — bug) |
| 4 | EEPROM | ~4000B | I2C seq read | ~300µs/byte (TODO) |

### Manifest (Page Table)

Stored in page 3 after the kernel image:

```
__manifest:  [offset0, size0, offset1, size1, ...]  (2 bytes each)
__pages:     [page0, page1, ...]                     (1 byte each)
```

Page values: 1=page1, 2=page2, 3=page3. Future: 0=EEPROM.

### Overlay Loader

The loader (in the kernel) reads the manifest, dispatches to the correct
page's copy loop, copies overlay code to the overlay region, performs I2C bus
recovery, and returns. The **caller** handles argument passing and calls the
overlay directly via `jal __ov_entry`.

```
Caller:                         Loader:
  push $a         ; save arg      _overlay_load:
  ldi $a,<idx>                      manifest read → C,D,B
  jal _overlay_load                 page dispatch → copy loop
  pop $a          ; restore        bus recovery
  jal __ov_entry  ; call overlay   ret
```

## Helper Bundling

Helpers (I2C, LCD, tone) are **bundled** into overlays rather than kept
permanently resident. Each overlay gets its own copy of needed helpers,
with per-overlay label suffixes (`_ov0`, `_ov1`) to avoid assembler conflicts.

### Knapsack Optimization

A cost-model decides which helpers to keep resident vs bundle:
- For each helper H of size S needed by N overlays:
  - value = (N-1) × S (bytes saved from not duplicating)
  - If value ≥ S: keep resident
- Helpers used by only 1 overlay → always bundled
- Helpers used by many overlays → kept resident

### Placement Retry

When an overlay exceeds all SRAM page capacities, the compiler automatically
promotes the largest bundled helper in that overlay to resident and retries.
This handles SRAM fragmentation without user intervention.

### Residency Propagation

If a resident helper calls or jumps to another helper, that target must also
stay resident. Propagates transitively until no more changes.

### Init Copies

ALL kernel helpers get `_init` suffixed copies in the init code section,
because kernel helper labels (at OVERLAY_REGION addresses) aren't available
during init (the code page has init code, not the kernel).

## Call Graph Analysis

Tarjan's SCC algorithm determines which functions share overlay slots. Only
mutually recursive functions must be in the same slot. One-way calls (A→B)
allow A and B to be separate overlays.

## Known Limitations

1. **Page 2 disabled** — deref2 works in isolation but overlay system produces
   wrong data. Needs investigation.
2. **No EEPROM overlay tier** — large programs that exceed SRAM spill nowhere.
3. **LCD + tone combo** — init code exceeds 256B (too many renamed helpers).
4. **No auto function splitting** — functions mixing I2C + LCD must be manually
   separated into read and display functions.
5. **Fat main** — 4+ overlay calls from main bloats the kernel.
