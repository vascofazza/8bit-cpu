// MK1 Web IDE — HTML/CSS/JS served from flash

#pragma once

static const char WEB_PAGE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MK1 CPU</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
header { background: #16213e; padding: 6px 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #0f3460; flex-shrink: 0; overflow-x: auto; }
header h1 { font-size: 16px; color: #e94560; font-weight: 700; letter-spacing: 1px; }
header select { background: #0f3460; color: #e0e0e0; border: 1px solid #e94560; border-radius: 4px; padding: 4px 8px; font-size: 13px; }
.btn { border: none; border-radius: 4px; padding: 6px 12px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn:active { transform: scale(0.97); }
.btn-run { background: #e94560; color: white; }
.btn-run:hover { background: #c73550; }
.btn-sec { background: #0f3460; color: #e0e0e0; border: 1px solid #335; }
.btn-sec:hover { background: #1a4a7a; }
.btn-warn { background: #6a3000; color: #ffa040; border: 1px solid #804000; }
.btn-warn:hover { background: #804000; }
.spacer { flex: 1; }
#status { font-size: 12px; color: #888; }
.btn-step { background: #1a5c3a; color: #4ecca3; border: 1px solid #2a7a4a; }
.btn-step:hover { background: #2a7a4a; }
#cpubar { background: #0d0d1a; border-bottom: 1px solid #0f3460; padding: 4px 12px; font-family: monospace; font-size: 11px; display: flex; gap: 16px; align-items: center; flex-shrink: 0; }
#cpubar .lbl { color: #666; }
#cpubar .val { color: #4ecca3; }
#cpubar .val.off { color: #e94560; }
main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.editor-wrap { flex: 1; display: flex; overflow: hidden; min-height: 0; position: relative; }
#lines { width: 38px; background: #0d0d1a; color: #555; border: none; padding: 12px 4px 12px 0; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; text-align: right; overflow: hidden; user-select: none; -webkit-user-select: none; }
#editor { flex: 1; background: transparent; color: transparent; caret-color: #a8d8a8; border: none; outline: none; padding: 12px 12px 12px 8px; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; resize: none; tab-size: 2; white-space: pre; overflow-wrap: normal; overflow: auto; position: relative; z-index: 2; }
#highlight { position: absolute; top: 0; left: 38px; right: 0; bottom: 0; background: #0a0a1a; color: #a8d8a8; padding: 12px 12px 12px 8px; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; white-space: pre; overflow: hidden; pointer-events: none; z-index: 1; margin: 0; }
.hl-cmt { color: #555; } .hl-lbl { color: #e94560; } .hl-dir { color: #f0c040; } .hl-reg { color: #4ecca3; } .hl-num { color: #f0a060; } .hl-mn { color: #7ab8f0; }
#output { background: #0d0d1a; border-top: 1px solid #0f3460; padding: 6px 12px; font-family: monospace; font-size: 11px; min-height: 24px; max-height: 120px; overflow-y: auto; white-space: pre-wrap; flex-shrink: 0; }
.err { color: #e94560; }
.ok { color: #4ecca3; }
.info { color: #888; }
.modal-bg { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:100; justify-content:center; align-items:center; }
.modal-bg.show { display:flex; }
.modal { background:#16213e; border:1px solid #0f3460; border-radius:8px; padding:16px; min-width:300px; max-width:90vw; max-height:70vh; display:flex; flex-direction:column; }
.modal h2 { font-size:15px; color:#e94560; margin-bottom:12px; }
.modal-list { flex:1; overflow-y:auto; margin-bottom:12px; }
.modal-list .prog-item { display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:4px; cursor:pointer; }
.modal-list .prog-item:hover { background:#0f3460; }
.modal-list .prog-item .prog-name { flex:1; font-size:13px; }
.modal-list .prog-item .prog-del { color:#e94560; cursor:pointer; font-size:15px; font-weight:bold; border:none; background:none; padding:2px 6px; }
.modal-list .prog-item .prog-del:hover { color:#ff6b80; }
.modal-input { display:flex; gap:8px; margin-bottom:12px; }
.modal-input input { flex:1; background:#0a0a1a; border:1px solid #335; border-radius:4px; padding:6px 8px; color:#e0e0e0; font-size:13px; }
.modal-close { align-self:flex-end; }
.empty-msg { color:#555; font-size:13px; padding:8px; }
</style>
</head>
<body>
<header>
  <h1>MK1 CPU</h1>
  <select id="examples" onchange="loadExample()">
    <option value="">Examples...</option>
    <option value="counter">Counter (inc)</option>
    <option value="countold">Counter (addi)</option>
    <option value="fibonacci">Fibonacci</option>
    <option value="xortest">XOR test</option>
    <option value="swaptest">SWAP + XOR test</option>
    <option value="negtest">NEG test</option>
    <option value="page3">Page 3 test</option>
    <option value="incdec">INC/DEC + JNZ</option>
    <option value="stackrel">Stack-relative (C-style calls)</option>
    <option value="stresstest">Stress test (clock speed)</option>
  </select>
  <button class="btn btn-sec" onclick="showPrograms()">Programs</button>
  <button class="btn btn-sec" onclick="downloadAsm()">&#x2B07;</button>
  <div class="spacer"></div>
  <span id="status"></span>
  <button class="btn btn-step" onclick="mk1step()">Step</button>
  <button class="btn btn-sec" onclick="mk1resume()">Resume</button>
  <button class="btn btn-warn" onclick="mk1reset()">Reset</button>
  <button class="btn btn-warn" onclick="mk1halt()">Halt</button>
  <select id="clksel" onchange="setClk()" title="ESP32 clock (SW3 must be manual)">
    <option value="">Clock...</option>
    <option value="0">Off (monitor)</option>
    <option value="150">150 Hz (min)</option>
    <option value="500">500 Hz</option>
    <option value="1000">1 kHz</option>
    <option value="10000">10 kHz</option>
    <option value="50000">50 kHz</option>
    <option value="100000">100 kHz</option>
    <option value="250000">250 kHz</option>
    <option value="500000">500 kHz (max)</option>
  </select>
  <button class="btn btn-sec" onclick="i2cScan()">I2C Scan</button>
  <button class="btn btn-run" onclick="asmRun()">Assemble &amp; Run</button>
</header>
<div id="cpubar">
  <span><span class="lbl">STATE </span><span class="val" id="cpu-state">---</span></span>
  <span><span class="lbl">CLK </span><span class="val" id="cpu-clk">---</span></span>
  <span><span class="lbl">BUS </span><span class="val" id="cpu-bus">---</span></span>
  <span><span class="lbl">CYCLES </span><span class="val" id="cpu-cycles">---</span></span>
  <span id="step-info" style="display:none"><span class="lbl">PC </span><span class="val" id="step-pc">--</span> <span class="lbl">OP </span><span class="val" id="step-op">--</span> <span class="lbl">STEP </span><span class="val" id="step-num">-</span></span>
</div>
<main>
  <div class="editor-wrap">
    <pre id="lines">1</pre>
    <pre id="highlight"></pre>
    <textarea id="editor" spellcheck="false" placeholder="; Enter MK1 assembly here..."></textarea>
  </div>
  <div id="output"><span class="info">Ready. Connect to MK1 and press Assemble &amp; Run.</span></div>
</main>
<div class="modal-bg" id="progModal" onclick="if(event.target===this)closePrograms()">
  <div class="modal">
    <h2>Programs</h2>
    <div class="modal-input">
      <input id="progName" placeholder="Program name" onkeydown="if(event.key==='Enter')saveProgram()">
      <button class="btn btn-run" onclick="saveProgram()">Save</button>
    </div>
    <div class="modal-list" id="progList"><span class="empty-msg">Loading...</span></div>
    <button class="btn btn-sec modal-close" onclick="closePrograms()">Close</button>
  </div>
</div>
<script>
const examples = {
  counter: '; Simple counter (uses inc)\nmain:\n  inc\n  out\n  j main\n',
  countold: '; Simple counter (original addi)\nmain:\n  addi 1 $a\n  out\n  j main\n',
  fibonacci: '; Fibonacci sequence\ninit:\n  ldi $a 1\n  ldi $b 1\n\nloop:\n  out $a\n  mov $a $c\n  add $b $a\n  jc end\n  mov $c $b\n  j loop\n\nend:\n  hlt\n',
  xortest: '; XOR test (no swap, isolates XOR)\n; Should show: 255, then 240, then halt\n  ldi $a 0xFF\n  ldi $b 0x0F\n  out $a       ; display 255\n  xor          ; A = 0xFF XOR 0x0F = 0xF0 = 240\n  out $a       ; display 240\n  hlt\n',
  swaptest: '; SWAP + XOR test\n; Should cycle: 255, 15, 240, 15...\n  ldi $a 0xFF\n  ldi $b 0x0F\n\nloop:\n  out $a\n  xor\n  swap\n  j loop\n',
  negtest: '; NEG test: negate counter\n; Counts 1,255,2,254,3,253...\n  ldi $a 0\n\nloop:\n  addi 1 $a\n  out $a\n  neg\n  out $a\n  neg\n  j loop\n',
  page3: '; Page 3 test: store/load from page 3\n; Stores 42 to page 3 addr 0, reads it back\n  ldi $a 42\n  stp3 0\n  ldi $a 0\n  out $a       ; display 0\n  ldp3 0\n  out $a       ; should display 42\n  hlt\n',
  incdec: '; INC/DEC test\n; Count up to 5, then down to 0, repeat\n  ldi $a 0\n\nup:\n  inc\n  out\n  cmp 5\n  jnz up         ; keep going if A != 5\n\ndown:\n  dec\n  out\n  cmp 0\n  jnz down       ; keep going if A != 0\n  j up\n',
  stackrel: '; Stack-relative load demo\n; Shows C-style function calls with arguments\n; max(a,b) accesses args via ldsp\n;\n; Expected output: 25, 200\n\n  ; max(10, 25)\n  ldi $a 10\n  push $a          ; arg1\n  ldi $a 25\n  push $a          ; arg2\n  jal max\n  pop $d           ; clean arg2\n  pop $d           ; clean arg1\n  out              ; display 25\n\n  ; max(200, 150)\n  ldi $a 200\n  push $a          ; arg1\n  ldi $a 150\n  push $a          ; arg2\n  jal max\n  pop $d           ; clean arg2\n  pop $d           ; clean arg1\n  out              ; display 200\n  hlt\n\n; max(arg1, arg2) -> $a\n; Stack: [SP+1]=ret, [SP+2]=arg2, [SP+3]=arg1\nmax:\n  ldsp 3           ; A = arg1\n  mov $a $b        ; B = arg1\n  ldsp 2           ; A = arg2\n  cmp $b           ; arg2 vs arg1\n  jc .done         ; CF=1: arg2 >= arg1, keep A\n  mov $b $a        ; arg1 was bigger\n.done:\n  ret\n',
  stresstest: '; Clock speed stress test\n; Exercises ALU, stack, RAM, jumps, flags\n; Expected final output: 161\n; If you see a different number, the clock is too fast!\n; Board tested reliable up to ~550kHz, fails at ~600kHz\n;\n; Computes: sum of (i XOR 0xAA) for i=0..9\n; Uses function calls, stack args, XOR, INC, CMP\n\n  ldi $a 0\n  push $a           ; accumulator on stack\n  ldi $b 0          ; counter\n\n.loop:\n  ; compute (counter XOR 0xAA)\n  mov $b $a\n  push $a           ; save counter\n  ldi $b 0xAA\n  xor               ; A = counter XOR 0xAA\n  mov $a $c         ; C = xor result\n\n  ; add to accumulator\n  ldsp 2            ; A = accumulator\n  add $c $a         ; A = accum + xor_result\n  stsp 2            ; store back\n\n  ; restore counter and increment\n  pop $a            ; A = counter\n  mov $a $b         ; B = counter\n  inc               ; A = counter + 1\n  mov $a $b         ; B = new counter\n\n  ; loop if counter < 10\n  cmp 10\n  jnz .loop\n\n  ; output result\n  ldsp 1            ; A = final accumulator\n  pop $d            ; clean stack\n  out               ; should display 161\n  hlt\n',
};

const ed = document.getElementById('editor');
const ln = document.getElementById('lines');
const hl = document.getElementById('highlight');

const MN = new Set(['nop','hlt','mov','ldi','ld','st','ldp3','stp3','push','pop','add','sub','or','and','xor','not','neg','inc','dec','sll','slr','rll','rlr','cmp','addi','subi','andi','ori','out','j','jz','jnz','jc','jnc','jal','ret','swap','exw','exr','stsp','ldsp','deref','ideref','derefp3','iderefp3','adc','sbc','tst','out_imm','jal_r','ocall','push_imm','ldsp_b','gpio_read','clr','setz','setnz','setc','setnc']);

function highlightSource(src) {
  return src.split('\n').map(line => {
    let h = '', i = 0;
    while (i < line.length) {
      if (line[i] === ';') { h += '<span class="hl-cmt">' + esc(line.substring(i)) + '</span>'; break; }
      if (line[i] === '#') { let e=i+1; while(e<line.length&&/\w/.test(line[e]))e++; h+='<span class="hl-dir">'+esc(line.substring(i,e))+'</span>'; i=e; continue; }
      if (line[i] === '$') { let e=i+1; while(e<line.length&&/[a-z]/i.test(line[e]))e++; h+='<span class="hl-reg">'+esc(line.substring(i,e))+'</span>'; i=e; continue; }
      if (line[i]==='0'&&i+1<line.length&&(line[i+1]==='x'||line[i+1]==='b')) { let e=i+2; while(e<line.length&&/[0-9a-fA-F]/.test(line[e]))e++; h+='<span class="hl-num">'+esc(line.substring(i,e))+'</span>'; i=e; continue; }
      if (/\d/.test(line[i])&&(i===0||!/\w/.test(line[i-1]))) { let e=i; while(e<line.length&&/\d/.test(line[e]))e++; h+='<span class="hl-num">'+esc(line.substring(i,e))+'</span>'; i=e; continue; }
      if (/[a-z_.]/i.test(line[i])) {
        let e=i; while(e<line.length&&/[\w.]/.test(line[e]))e++;
        let w=line.substring(i,e);
        if (e<line.length&&line[e]===':') { h+='<span class="hl-lbl">'+esc(w+':')+'</span>'; i=e+1; continue; }
        if (MN.has(w.toLowerCase())) { h+='<span class="hl-mn">'+esc(w)+'</span>'; i=e; continue; }
        h+=esc(w); i=e; continue;
      }
      h+=esc(line[i]); i++;
    }
    return h;
  }).join('\n') + '\n';
}

function updateHighlight() { hl.innerHTML = highlightSource(ed.value); }

function updateLines() {
  const count = ed.value.split('\n').length;
  let s = '';
  for (let i = 1; i <= count; i++) s += i + '\n';
  ln.textContent = s;
  updateHighlight();
}

function syncScroll() { ln.scrollTop = ed.scrollTop; hl.scrollTop = ed.scrollTop; hl.scrollLeft = ed.scrollLeft; }

ed.addEventListener('input', updateLines);
ed.addEventListener('scroll', syncScroll);

function loadExample() {
  const sel = document.getElementById('examples');
  if (sel.value && examples[sel.value]) { ed.value = examples[sel.value]; updateLines(); }
  sel.value = '';
}

function log(msg, cls) {
  const o = document.getElementById('output');
  o.innerHTML += '<span class="' + (cls||'info') + '">' + esc(msg) + '</span>\n';
  o.scrollTop = o.scrollHeight;
}

function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

async function asmRun() {
  const o = document.getElementById('output');
  o.innerHTML = '';
  document.getElementById('status').textContent = 'Assembling...';
  try {
    const resp = await fetch('/assemble', {
      method: 'POST', headers: {'Content-Type': 'text/plain'}, body: ed.value
    });
    const result = await resp.json();
    if (result.errors && result.errors.length > 0) {
      result.errors.forEach(e => log('Line ' + e.line + ': ' + e.message, 'err'));
      document.getElementById('status').textContent = 'Errors';
      return;
    }
    const codePct = Math.round(result.code_size / 256 * 100);
    const dataPct = Math.round(result.data_size / 256 * 100);
    log('Code: ' + result.code_size + '/256 bytes (' + codePct + '%)  Data: ' + result.data_size + '/256 bytes (' + dataPct + '%)', 'ok');
    if (result.code_hex) {
      // Format hex dump with address column: 00: XX XX XX XX ...
      const bytes = result.code_hex.split(' ');
      let hexLines = '';
      for (let i = 0; i < bytes.length; i += 16) {
        const addr = i.toString(16).toUpperCase().padStart(3, '0');
        const chunk = bytes.slice(i, i + 16).join(' ');
        hexLines += addr + ': ' + chunk + '\n';
      }
      log('Code:', 'info');
      log(hexLines.trimEnd(), 'info');
      if (result.data_hex) {
        const dbytes = result.data_hex.split(' ');
        let dLines = '';
        for (let i = 0; i < dbytes.length; i += 16) {
          const addr = i.toString(16).toUpperCase().padStart(3, '0');
          const chunk = dbytes.slice(i, i + 16).join(' ');
          dLines += addr + ': ' + chunk + '\n';
        }
        log('Data:', 'info');
        log(dLines.trimEnd(), 'info');
      }
    }
    document.getElementById('status').textContent = 'Uploading...';

    const resp2 = await fetch('/upload', { method: 'POST' });
    const r2 = await resp2.json();
    if (r2.ok) {
      log('Uploaded and running!', 'ok');
      document.getElementById('status').textContent = 'Running';
    } else {
      log('Upload failed: ' + (r2.error || 'unknown'), 'err');
      document.getElementById('status').textContent = 'Error';
    }
  } catch(e) {
    log('Error: ' + e.message, 'err');
    document.getElementById('status').textContent = 'Error';
  }
}

async function mk1reset() {
  await fetch('/reset', { method: 'POST' });
  document.getElementById('status').textContent = 'Reset';
}

async function i2cScan() {
  const o = document.getElementById('output');
  o.innerHTML = '<span class="info">Scanning I2C bus (0x08-0x77)...</span>';
  document.getElementById('status').textContent = 'I2C Scanning...';
  try {
    const r = await fetch('/i2cscan');
    const j = await r.json();
    if (j.found && j.found.length > 0) {
      let msg = 'I2C devices found: ' + j.found.map(d => d.hex + ' (W:' + d.write + ' R:' + d.read + ')').join(', ');
      o.innerHTML = '<span class="ok">' + esc(msg) + '</span>';
    } else {
      o.innerHTML = '<span class="err">No I2C devices found</span>';
    }
    document.getElementById('status').textContent = j.found.length + ' device(s)';
  } catch(e) {
    o.innerHTML = '<span class="err">I2C scan failed: ' + esc(e.message) + '</span>';
    document.getElementById('status').textContent = 'Scan failed';
  }
}

async function mk1halt() {
  await fetch('/halt', { method: 'POST' });
  document.getElementById('status').textContent = 'Halted';
}

async function mk1step() {
  try {
    const r = await fetch('/step', { method: 'POST' });
    const j = await r.json();
    if (j.ok) {
      document.getElementById('cpu-bus').textContent = j.bus + ' (0x' + j.bus.toString(16).toUpperCase().padStart(2,'0') + ')';
      document.getElementById('cpu-cycles').textContent = j.cycles;
      const si = document.getElementById('step-info');
      si.style.display = '';
      document.getElementById('step-pc').textContent = '0x' + j.pc.toString(16).toUpperCase().padStart(2,'0');
      document.getElementById('step-op').textContent = '0x' + j.opcode.toString(16).toUpperCase().padStart(2,'0');
      document.getElementById('step-num').textContent = j.step;
    }
  } catch(e) {}
}

async function mk1resume() {
  await fetch('/resume', { method: 'POST' });
  document.getElementById('status').textContent = 'Running';
  document.getElementById('step-info').style.display = 'none';
}

async function setClk() {
  const sel = document.getElementById('clksel');
  if (sel.value === '') return;
  try {
    const r = await fetch('/clock?hz=' + sel.value, { method: 'POST' });
    const j = await r.json();
    if (j.ok) {
      log('Clock set to ' + (j.hz > 0 ? formatClk(j.hz) : 'off (monitoring)'), 'ok');
    } else {
      log('Clock refused: ' + j.error, 'err');
    }
  } catch(e) {
    log('Clock error: ' + e.message, 'err');
  }
  sel.value = '';
}

// Status polling
function formatClk(hz) {
  if (hz < 1) return 'stopped';
  if (hz < 1000) return hz.toFixed(1) + ' Hz';
  if (hz < 1000000) return (hz/1000).toFixed(1) + ' kHz';
  return (hz/1000000).toFixed(2) + ' MHz';
}

async function pollStatus() {
  try {
    const r = await fetch('/status');
    const s = await r.json();
    const stEl = document.getElementById('cpu-state');
    stEl.textContent = s.state.toUpperCase();
    stEl.className = 'val' + (s.state === 'halted' ? ' off' : '');
    const clkText = s.custom_clock_hz > 0
      ? formatClk(s.custom_clock_hz) + ' (ESP32)'
      : formatClk(s.clock_hz);
    document.getElementById('cpu-clk').textContent = clkText;
    document.getElementById('cpu-bus').textContent = s.bus + ' (0x' + s.bus.toString(16).toUpperCase().padStart(2,'0') + ')';
    document.getElementById('cpu-cycles').textContent = s.cycles;
  } catch(e) {}
}

setInterval(pollStatus, 1000);

async function showPrograms() {
  document.getElementById('progModal').classList.add('show');
  document.getElementById('progName').value = '';
  await refreshProgramList();
}

function closePrograms() {
  document.getElementById('progModal').classList.remove('show');
}

async function refreshProgramList() {
  const list = document.getElementById('progList');
  try {
    const r = await fetch('/programs');
    const programs = await r.json();
    if (programs.length === 0) {
      list.innerHTML = '<span class="empty-msg">No saved programs</span>';
      return;
    }
    list.innerHTML = '';
    programs.forEach(name => {
      const item = document.createElement('div');
      item.className = 'prog-item';
      item.innerHTML = '<span class="prog-name">' + esc(name) + '</span>' +
        '<button class="prog-del" title="Delete">&times;</button>';
      item.querySelector('.prog-name').onclick = () => loadProgram(name);
      item.querySelector('.prog-del').onclick = (e) => { e.stopPropagation(); deleteProgram(name); };
      list.appendChild(item);
    });
  } catch(e) {
    list.innerHTML = '<span class="err">Failed to load list</span>';
  }
}

async function saveProgram() {
  const name = document.getElementById('progName').value.trim();
  if (!name) { log('Enter a program name', 'err'); return; }
  try {
    const r = await fetch('/save?name=' + encodeURIComponent(name), {
      method: 'POST', headers: {'Content-Type': 'text/plain'}, body: ed.value
    });
    const j = await r.json();
    if (j.ok) {
      log('Saved: ' + name, 'ok');
      await refreshProgramList();
      document.getElementById('progName').value = '';
    } else {
      log('Save failed: ' + (j.error || 'unknown'), 'err');
    }
  } catch(e) { log('Save failed: ' + e.message, 'err'); }
}

async function loadProgram(name) {
  try {
    const r = await fetch('/load?name=' + encodeURIComponent(name));
    if (r.ok) {
      const text = await r.text();
      ed.value = text;
      updateLines();
      closePrograms();
      log('Loaded: ' + name, 'ok');
    }
  } catch(e) { log('Load failed: ' + e.message, 'err'); }
}

async function deleteProgram(name) {
  if (!confirm('Delete "' + name + '"?')) return;
  try {
    const r = await fetch('/programs/delete?name=' + encodeURIComponent(name), { method: 'POST' });
    const j = await r.json();
    if (j.ok) {
      log('Deleted: ' + name, 'ok');
      await refreshProgramList();
    }
  } catch(e) { log('Delete failed: ' + e.message, 'err'); }
}

async function loadSaved() {
  try {
    const resp = await fetch('/load');
    if (resp.ok) {
      const text = await resp.text();
      if (text.length > 0) { ed.value = text; updateLines(); }
    }
  } catch(e) {}
}

function downloadAsm() {
  const blob = new Blob([ed.value], {type: 'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'program.asm';
  a.click();
  URL.revokeObjectURL(a.href);
}

// Keyboard shortcuts + tab handling
ed.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    asmRun();
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    showPrograms();
    return;
  }
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = this.selectionStart;
    this.value = this.value.substring(0, s) + '  ' + this.value.substring(this.selectionEnd);
    this.selectionStart = this.selectionEnd = s + 2;
    updateLines();
  }
});

// Load saved program on startup
loadSaved();
updateLines();
setTimeout(updateHighlight, 500); // re-highlight after loadSaved completes
</script>
</body>
</html>
)rawliteral";
