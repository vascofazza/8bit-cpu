# RUNLOG Findings - 2026-04-07

## Counter wrapping bug in stopwatch on RUNLOG

### Simple counter (hardcoded delay, no SQW): WORKS
- `[0,1,2,...66]` — 67 ticks, no wrapping, perfectly incrementing

### No-beep stopwatch (SQW calibration + deref delay): 
- Run 1: `[0,...15, 0,...10, 0,...7]` — wraps at 15, then shorter each time
- Run 2: `[0,...35]` — no wrapping in 36 ticks (inconsistent with run 1!)

### Beep stopwatch:
- Run 1: `[0,...22]` — stops at 22 (2 ticks after beep at 20)
- Run 2: `[0,...31, 0,...3]` — wraps at 31 (1 tick after beep at 30)

### On auto clock:
- Beeps correctly at 010 and 020
- No beep at 030
- Display continues counting past 022 (no hard crash)
- OI rate stays rock steady at 1.0/s for 10+ minutes
- User reported gradual slowdown after many minutes

### Key observations:
1. Beep causes counter reset (D register clobbered)
2. The wrap point varies between runs (not deterministic)  
3. Simple counter with same delay loop structure works fine
4. The difference: SQW stopwatch uses `deref` (data page read) vs hardcoded `ldi $b, 3`
5. On auto clock, OI rate is constant but display/beep behavior degrades

### Hypothesis:
The beep subroutine's VIA operations (exw 0 1, exw 0 3) leave some hardware 
state that eventually corrupts the D register during subsequent deref or delay
operations. The corruption is non-deterministic and accumulates over multiple beeps.

## Isolation test results (2026-04-07 evening)

| Variant | VIA operations | Result |
|---------|---------------|--------|
| D: NOPs only | none | OK (60 ticks, max=59) |
| B: DDRA only | exw 0 3 | OK (61 ticks, max=60) |
| A: Full beep | exw 0 3 + exw 0 1 | OK (241 ticks, max=240) |
| C: ORA only | exw 0 1 (no DDRA) | **WRAPS at 10** — D corrupted |

### Key finding
`exw 0 1` (ORA write) WITHOUT DDRA configured corrupts D register.
With DDRA=0x02 set first (PA1 as output), ORA writes are safe.
The real stopwatch beep sets DDRA before ORA — should be safe.

### Remaining mystery
On auto clock, beep stops after tick 020 (no beep at 030+).
On RUNLOG, full beep variant A counts to 240+ without issues.
The auto clock behavior differs from RUNLOG for beep functionality.
