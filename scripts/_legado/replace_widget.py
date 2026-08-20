import re

with open('C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/scripts/unified_bridge.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the WIDGET_HTML start
start = content.find('WIDGET_HTML = """<!DOCTYPE html>')
if start == -1:
    print("ERROR: WIDGET_HTML start not found")
    exit(1)

# Find the end - look for </div>\n</div>\n<script>
end_marker = '</div>\n</div>\n<script>'
end = content.find(end_marker, start)
if end == -1:
    # Try alternative
    end_marker2 = '</div></div><script>'
    end = content.find(end_marker2, start)
    if end == -1:
        print("ERROR: End marker not found")
        exit(1)
    end_marker = end_marker2

end += len(end_marker)

old_length = end - start
print(f"Found WIDGET_HTML from {start} to {start + old_length} (length {old_length})")

# New HTML content
new_widget = """WIDGET_HTML = \"\"\"<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="icon" href="jarvis.ico" type="image/x-icon">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;
background:#1e1e2e;color:#cdd6f4;width:100%;height:100%;font-size:13px;}
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:#181825;}
::-webkit-scrollbar-thumb{background:#45475a;border-radius:3px;}
.topbar{background:#313244;height:28px;cursor:move;
display:flex;align-items:center;justify-content:space-between;
padding:0 10px;font-size:12px;color:#a6adc8;user-select:none;
flex-shrink:0;}
.drag{flex:1;cursor:move;min-height:28px;display:flex;align-items:center;gap:6px;}
.title{display:flex;align-items:center;gap:6px;font-weight:600;}
.close{background:#f38ba8;width:18px;height:18px;border-radius:4px;
display:flex;align-items:center;justify-content:center;
font-size:11px;line-height:1;cursor:pointer;color:#1e1e2e;font-weight:bold;
flex-shrink:0;}
.main{padding:10px;display:flex;flex-direction:column;height:calc(100% - 28px);overflow-y:auto;
min-height:0;}
.row{display:flex;gap:8px;flex-wrap:wrap;}
.row .btn{flex:1 1 45%; min-width:0;}
.btn{display:flex;align-items:center;justify-content:space-between;
padding:8px 10px;border:none;border-radius:6px;cursor:pointer;
font-size:13px;background:#313244;color:#cdd6f4;transition:.15s;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.btn:hover{background:#45475a;}
.btn.on{background:#a6e3a1;color:#1e1e2e;}
.btn.off{background:#f38ba8;color:#1e1e2e;}
.btn.stop{background:#f28465;color:#1e1e2e;}
.sw{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0;}
.sw.on{background:#a6e3a1;box-shadow:0 0 6px #a6e3a1;}
.sw.off{background:#f38ba8;}
.section{margin-top:10px;}
.section-title{font-size:10px;color:#6c7086;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:5px;}
.info{font-size:12px;color:#6c7086;word-break:break-word;padding:8px 10px;
background:#181825;border-radius:6px;min-height:22px;}
.info.falando{color:#a6e3a1;font-weight:500;}
.modes{display:flex;gap:6px;margin-bottom:8px;}
.mode-btn{flex:1;padding:6px;border:none;border-radius:5px;cursor:pointer;
font-size:11px;background:#181825;color:#a6adc8;transition:.15s;white-space:nowrap;}
.mode-btn.active{background:#89b4fa;color:#1e1e2e;font-weight:600;}
.mode-btn:hover{background:#313244;}
.sys-row{display:flex;gap:10px;font-size:10px;color:#a6adc8;margin-top:4px;flex-wrap:wrap;}
.sys-val{color:#a6e3a1;font-weight:500;}
.sys-val.warn{color:#f9e2af;}
.sys-val.crit{color:#f38ba8;}
.txt-input{display:flex;gap:6px;margin-top:8px;}
.txt-input input{flex:1;padding:8px 10px;border:1px solid #45475a;border-radius:5px;
background:#181825;color:#cdd6f4;font-size:12px;outline:none;min-width:0;}
.txt-input input:focus{border-color:#89b4fa;}
.txt-input button{padding:8px 14px;border:none;border-radius:5px;
background:#89b4fa;color:#1e1e2e;font-size:12px;cursor:pointer;font-weight:600;
flex-shrink:0;white-space:nowrap;}
.txt-input button:hover{background:#74c7ec;}
.notif{font-size:10px;color:#a6adc8;padding:4px 0;border-bottom:1px solid #313244;line-height:1.4;}
.notif:last-child{border:none;}
.hist{font-size:10px;color:#6c7086;padding:4px 0;border-bottom:1px solid #181825;line-height:1.4;}
.hist:last-child{border:none;}
.hist .cmd{color:#89b4fa;}
.mic-active{animation:pulse 1s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}

/* Responsive: small widths */
@media (max-width: 260px) {
  html,body {font-size:11px;}
  .topbar {height:24px;padding:0 8px;font-size:11px;}
  .drag {min-height:24px;gap:4px;}
  .close {width:16px;height:16px;font-size:10px;}
  .main {padding:8px;height:calc(100% - 24px);}
  .row {gap:6px;}
  .row .btn {flex:1 1 100%;}
  .btn {padding:7px 8px;font-size:12px;}
  .sw {width:8px;height:8px;margin-right:5px;}
  .txt-input input {padding:6px 8px;font-size:11px;}
  .txt-input button {padding:6px 10px;font-size:11px;}
  .modes {gap:4px;}
  .mode-btn {padding:5px;font-size:10px;}
  .section-title {font-size:9px;}
  .info {font-size:11px;padding:6px 8px;}
  .txt-input {gap:4px;}
  .txt-input button {padding:6px 8px;font-size:11px;}
}

/* Very small widths */
@media (max-width: 200px) {
  html,body {font-size:10px;}
  .topbar {height:22px;padding:0 6px;}
  .drag {gap:3px;}
  .close {width:14px;height:14px;}
  .main {padding:6px;}
  .btn {padding:5px 6px;font-size:10px;}
  .section-title {font-size:8px;}
  .info {font-size:10px;padding:4px 6px;min-height:18px;}
  .modes {gap:3px;}
  .mode-btn {padding:4px;font-size:9px;}
}

</style>
</head><body>
<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>🎙️ Jarvis</span>
  </div>
  <div class="close" id="closeBtn" title="Fechar">✕</div>
</div>
<div class="main">
  <div class="modes" id="modes">
    <button class="mode-btn active" data-m="narrador">Narrador</button>
    <button class="mode-btn" data-m="dialogo">Diálogo</button>
    <button class="mode-btn" data-m="silencioso">Silencioso</button>
  </div>
  <div class="row">
    <button class="btn off" id="btnVoz"><span><span class="sw off" id="swVoz"></span>Voz</span><span id="lblVoz">OFF</span></button>
    <button class="btn stop" id="btnFala"><span>⏹ Parar</span></button>
  </div>
  <div class="row">
    <button class="btn off" id="btnMic"><span><span class="sw off" id="swMic"></span>Mic</span><span id="lblMic">OFF</span></button>
    <button class="btn" id="btnRepetir" title="Repetir último resumo">🔁 Repetir</button>
  </div>
  <div class="txt-input">
    <input type="text" id="txtCmd" placeholder="Digite um comando..." />
    <button id="btnSend">▶</button>
  </div>
  <div class="section">
    <div class="section-title">Status</div>
    <div class="info" id="info">conectando...</div>
  </div>
  <div class="section" id="sysSection" style="display:none;">
    <div class="section-title">Sistema</div>
    <div class="sys-row">
      <span>CPU: <span class="sys-val" id="sysCpu">-</span></span>
      <span>RAM: <span class="sys-val" id="sysRam">-</span></span>
      <span>Disco: <span class="sys-val" id="sysDisk">-</span></span>
    </div>
  </div>
  <div class="section" id="notifSection" style="display:none;">
    <div class="section-title">Notificações</div>
    <div id="notifList"></div>
  </div>
  <div class="section" id="histSection" style="display:none;">
    <div class="section-title">Histórico</div>
    <div id="histList"></div>
  </div>
  <div class="row" style="margin-top:auto;padding-top:8px;">
    <button class="btn" id="minimizeBtn" title="Minimizar">_</button>
    <button class="btn" id="topoBtn" title="Sempre no topo">Top</button>
    <button class="btn" id="fixBtn" title="Fixar atrás">Trás</button>
  </div>
</div>"""

# Find exact markers in content
start_marker = 'WIDGET_HTML = """<!DOCTYPE html>'
start = content.find(start_marker)
if start == -1:
    print("ERROR: WIDGET_HTML start not found")
    exit(1)

# Find end marker - try multiple variants
end = -1
for marker in ['</div>\n</div>\n<script>', '</div></div><script>', '</div>\n</div>\n    <script>']:
    pos = content.find(marker, start)
    if pos != -1:
        end = pos + len(marker)
        break

if end == -1:
    print("ERROR: Could not find end marker")
    exit(1)

old_len = end - start
print(f"Replacing WIDGET_HTML: {old_len} chars at position {start}")

# Build new content
new_content = content[:start] + new_widget + content[end:]

with open('C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/scripts/unified_bridge.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"SUCCESS: Replaced {old_len} chars with {len(new_widget)} chars")