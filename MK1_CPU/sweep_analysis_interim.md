# Address Sweep Analysis - 2026-04-07

## STATUS: ALL OVERNIGHT DATA IS CONTAMINATED

### Problems discovered:
1. **Two sweep processes ran simultaneously**, contending for ESP32 HTTP server. 
   Responses were interleaved, causing wrong data to be recorded.
2. **ESP32 OI capture is broken after reflash.** `out_imm 42; hlt` returns 
   val=234 (wrong) at us=1, and doesn't capture at us=5/10.
3. The contaminated data showed patterns (odd/even alternating, "address bit 0 
   issue") that were likely artifacts of the contention, not real CPU behavior.

### What IS reliable from this session:
- The working stopwatch at 205-251 bytes on auto 126kHz clock is confirmed
- The address-dependent delay bug on auto clock IS real (tested manually)
- DDRA=0x02 persistently breaks the delay loop (tested manually)
- ldsp carry propagation bug is confirmed (tested manually with intermittent values)
- The 64-iteration inner loop calibration works (D=51 at 126kHz)

### What needs to be done:
1. Fix ESP32 OI capture (may need investigating run_cycles handler)
2. Re-run sweep with SINGLE process, VERIFIED OI capture
3. Compare results on auto clock vs run_cycles to distinguish CPU bugs from 
   run_cycles timing artifacts
4. Test sequential vs J vs JNZ vs JAL to isolate the vulnerable instruction

### Key question: Is the address-dependent bug a CPU hardware issue or a 
run_cycles timing artifact?
The bug manifests on AUTO clock too (stopwatch fails at certain code layouts),
so it's not purely a run_cycles issue. But run_cycles may have additional 
timing problems that make the sweep data unreliable.
