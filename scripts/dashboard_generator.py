#!/usr/bin/env python3
"""Gera o dashboard cadeia-supervisao.html com dados reais do ecossistema.

Roda em loop: a cada 10 segundos lê os state files, verifica processos
e regenera o HTML. O navegador recarrega automaticamente via meta refresh.
"""
import json, time, os, sys
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

BASE = Path(__file__).parent.parent
RUNTIME = BASE / "runtime"
SCRIPTS = BASE / "scripts"
HTML_OUT = RUNTIME / "cadeia-supervisao.html"

MAESTRO_STATE = RUNTIME / "maestro_estado.json"
GUARDIAN_STATE = SCRIPTS / "guardian_state.json"
GUARDIAN_LOG = SCRIPTS / "guardian_log.txt"
MAESTRO_LOG = RUNTIME / "maestro.log"

SVC_META = {
    'runtime_maestro.py': {'display': 'Maestro', 'owner': 'maestro'},
    'widget_edge.py':     {'display': 'Widget',  'owner': 'guardian'},
    'tts_service.py':     {'display': 'TTS',     'owner': 'guardian'},
    'jarvis_bridge.py':   {'display': 'Bridge',  'owner': 'guardian'},
    'dialogo.py':         {'display': 'Dialogo', 'owner': 'manual'},
    'system_guardian.py': {'display': 'Guardian', 'owner': 'system'},
    'vigilante.ps1':      {'display': 'Vigilante', 'owner': 'system'},
    'watchdog.ps1':       {'display': 'Keeper',  'owner': 'system'},
}

PROTECTED_SERVICES = ['tts_service.py', 'widget_edge.py', 'dialogo.py', 'jarvis_bridge.py']


def _ler_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _ler_log(path, n=20):
    lines = []
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('['):
                    lines.append(line)
        return lines[-n:]
    except Exception:
        return []


def _processos_vivos():
    """Varre a tabela de processos e retorna {script: {pid, vivo}}."""
    if not psutil:
        return {}
    achados = {}
    for p in psutil.process_iter(['pid', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            cmd = ' '.join(p.info['cmdline'] or []).lower()
            for script in SVC_META:
                if script.replace('.ps1', '') in cmd or script in cmd:
                    if script not in achados:
                        mem = 0
                        try:
                            mem = p.info['memory_info'].rss / (1024*1024)
                        except Exception:
                            pass
                        achados[script] = {
                            'pid': p.info['pid'],
                            'vivo': True,
                            'mem_mb': round(mem, 1),
                        }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return achados


def _ultimo_log_guardian(n=8):
    """Lê as últimas N entradas relevantes do guardian_log.txt."""
    entradas = []
    try:
        with open(GUARDIAN_LOG, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if any(k in line for k in ['reiniciando', 'Morto', 'RAM critica', 'fora do ar',
                                            'Bridge', 'TTS', 'Widget', 'Narrador', 'iniciado',
                                            'MAESTRO_OFFLINE', 'registrar:', 'parar:']):
                    entradas.append(line)
        return entradas[-n:]
    except Exception:
        return []


def _parse_log_line(line):
    """Extrai timestamp e formata uma linha de log."""
    try:
        ts = line[:19]
        rest = line[22:] if len(line) > 22 else line
        return {'ts': ts, 'raw': rest}
    except Exception:
        return {'ts': '', 'raw': line}


def montar_estado():
    """Junta dados de todas as fontes num dict único."""
    maestro = _ler_json(MAESTRO_STATE)
    guardian = _ler_json(GUARDIAN_STATE)
    vivos = _processos_vivos()

    servicos = {}
    # Começa pelos serviços do maestro
    for nome, info in maestro.get('servicos', {}).items():
        meta = SVC_META.get(nome, {'display': nome, 'owner': info.get('owner', '?')})
        vivo_real = nome in vivos
        servicos[nome] = {
            'display': meta['display'],
            'pid': vivos[nome]['pid'] if vivo_real else info.get('pid', 0),
            'owner': info.get('owner', '?'),
            'vivo': vivo_real,
            'mem_mb': vivos[nome].get('mem_mb', 0) if vivo_real else 0,
            'motivo': info.get('motivo_inatividade', ''),
            'heartbeat': info.get('last_heartbeat', 0),
        }

    # Adiciona serviços que estão vivos mas não estão no maestro
    for nome, info in vivos.items():
        if nome not in servicos:
            meta = SVC_META.get(nome, {'display': nome, 'owner': '?'})
            servicos[nome] = {
                'display': meta['display'],
                'pid': info['pid'],
                'owner': '?',
                'vivo': True,
                'mem_mb': info.get('mem_mb', 0),
                'motivo': '',
                'heartbeat': 0,
            }

    # Guardian
    gc_status = guardian.get('status', 'ok')
    gc_ram = guardian.get('ram_mb', 0)
    gc_disk = guardian.get('disk_gb', 0)
    gc_actions = guardian.get('actions', [])

    # Log do guardian
    log_lines = _ultimo_log_guardian(10)
    log_parsed = [_parse_log_line(l) for l in log_lines]

    # Log do maestro (últimas 15 linhas)
    maestro_lines = _ler_log(MAESTRO_LOG, 15)
    maestro_log_parsed = [_parse_log_line(l) for l in maestro_lines]

    return {
        'servicos': servicos,
        'guardian': {
            'status': gc_status,
            'ram_mb': gc_ram,
            'disk_gb': gc_disk,
            'actions': gc_actions,
        },
        'log_guardian': log_parsed,
        'log_maestro': maestro_log_parsed,
        'timestamp': datetime.now().isoformat(),
    }


def gerar_html(estado):
    """Gera o HTML completo com os dados embutidos."""
    s = json.dumps(estado, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="10">
<title>Cadeia de Supervisão</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#080b12;--surface:#0e1218;--card:#111620;--border:#1e2636;--border-h:#2a3650;--accent:#38bdf8;--accent2:#22d3ee;--accent3:#a78bfa;--ok:#22c55e;--warn:#f59e0b;--err:#ef4444;--dim:#475569;--text:#f0f4f8;--text2:#94a3b8;--text3:#64748b}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;padding:24px 32px;min-height:100vh;display:flex;flex-direction:column;align-items:center}}
.header{{text-align:center;width:100%;max-width:1100px;margin-bottom:28px}}
.header h1{{font-size:22px;font-weight:600;letter-spacing:.3px;margin-bottom:4px}}
.header .pid{{font-size:26px;color:var(--accent);font-family:'Courier New',monospace;opacity:.7}}
.header .sub{{font-size:13px;color:var(--text3);margin-top:2px}}
.narrativa{{width:100%;max-width:1100px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;font-size:14px;line-height:1.5;min-height:48px}}
.narrativa .pulse{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.narrativa .pulse.ok{{background:var(--ok);box-shadow:0 0 8px var(--ok)}}
.narrativa .pulse.warn{{background:var(--warn);box-shadow:0 0 8px var(--warn)}}
.narrativa .pulse.err{{background:var(--err);box-shadow:0 0 8px var(--err)}}
.narrativa .msg{{flex:1}}.narrativa .tempo{{font-size:11px;color:var(--text3);white-space:nowrap}}
.gc-section{{width:100%;max-width:1100px;margin-bottom:24px}}
.gc-section h3{{font-size:13px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;font-weight:500}}
.gc-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.gc-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;transition:border-color .2s}}
.gc-card:hover{{border-color:var(--border-h)}}
.gc-top{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.gc-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.gc-dot.ok{{background:var(--ok);box-shadow:0 0 8px var(--ok)}}.gc-dot.err{{background:var(--err);box-shadow:0 0 8px var(--err)}}.gc-dot.warn{{background:var(--warn);box-shadow:0 0 8px var(--warn)}}
.gc-title{{font-size:14px;font-weight:500;flex:1}}
.gc-badge{{font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}}
.gc-badge.ok{{background:rgba(34,197,94,.15);color:var(--ok)}}.gc-badge.warn{{background:rgba(245,158,11,.15);color:var(--warn)}}.gc-badge.err{{background:rgba(239,68,68,.15);color:var(--err)}}
.gc-metrics{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px}}
.gc-metric{{text-align:center}}.gc-metric .val{{font-size:18px;font-weight:600;color:var(--accent)}}.gc-metric .lbl{{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px}}
.gc-actions{{border-top:1px solid var(--border);padding-top:8px;max-height:140px;overflow-y:auto}}
.gc-actions .act{{font-size:11px;color:var(--text2);padding:2px 0;border-bottom:1px solid rgba(255,255,255,.03);line-height:1.4;word-break:break-all}}
.gc-actions .act:last-child{{border-bottom:none}}
.gc-actions .act .ts{{color:var(--dim);margin-right:6px}}
.servicos{{width:100%;max-width:1100px;margin-bottom:24px}}
.servicos h3{{font-size:13px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;font-weight:500}}
.svc-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.svc{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 14px;transition:border-color .2s}}
.svc:hover{{border-color:var(--border-h)}}
.svc-top{{display:flex;align-items:center;gap:8px;margin-bottom:6px}}
.svc-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.svc-dot.vivo{{background:var(--ok);box-shadow:0 0 6px var(--ok)}}.svc-dot.morto{{background:var(--err);box-shadow:0 0 6px var(--err)}}
.svc-name{{font-size:12px;color:var(--text2);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.svc-status{{font-size:11px;color:var(--text3)}}
.svc-pid{{font-size:13px;font-family:'Courier New',monospace;color:var(--accent)}}
.svc-owner{{font-size:11px;color:var(--text3)}}
.svc-heart{{font-size:10px;color:var(--dim);margin-top:4px}}
.svc-mem{{font-size:10px;color:var(--accent3);margin-top:2px}}
.flow{{width:100%;max-width:1100px;margin-bottom:24px}}
.flow h3{{font-size:13px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;font-weight:500}}
.chain{{display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;padding:16px 12px;background:var(--surface);border:1px solid var(--border);border-radius:12px}}
.node{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 18px;text-align:center;min-width:105px;transition:border-color .2s}}
.node:hover{{border-color:var(--accent)}}
.node .n-label{{font-size:11px;color:var(--text2);margin-bottom:3px}}.node .n-freq{{font-size:14px;font-weight:600;color:var(--accent)}}.node .n-pid{{font-size:11px;color:var(--text3);font-family:'Courier New',monospace}}
.arrow{{color:var(--accent);font-size:18px;opacity:.4;margin:0 2px}}
.guerra{{width:100%;max-width:1100px;margin-bottom:28px}}
.guerra h3{{font-size:13px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;font-weight:500}}
.shields{{display:flex;justify-content:center;gap:20px;flex-wrap:wrap}}
.s-card{{width:155px;text-align:center;position:relative}}.s-card:hover .s-ring{{border-color:var(--accent)}}
.s-ring{{width:96px;height:96px;border-radius:50%;border:2px solid var(--border);margin:0 auto 6px;display:flex;align-items:center;justify-content:center;background:var(--bg);transition:border-color .2s}}
.s-ring svg{{width:44px;height:44px}}
.s-name{{font-size:13px;color:var(--text2);font-weight:500}}.s-status{{font-size:11px;margin-top:2px}}.s-status.ok{{color:var(--ok)}}.s-status.off{{color:var(--err)}}
.s-pid{{font-size:11px;color:var(--text3);font-family:'Courier New',monospace;margin-top:2px}}
.log{{width:100%;max-width:1100px;margin-bottom:28px}}
.log h3{{font-size:13px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;font-weight:500}}
.log-box{{background:#06080d;border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-family:'Courier New',monospace;font-size:11px;line-height:1.7;max-height:140px;overflow-y:auto;color:var(--text2)}}
.log-box .info{{color:var(--text3)}}.log-box .alerta{{color:var(--err)}}.log-box .warn{{color:var(--warn)}}.log-box .ok{{color:var(--ok)}}
.log-box .ts{{color:var(--dim)}}.log-box .hl{{color:var(--accent)}}
.glossario{{width:100%;max-width:1100px}}
.gloss-toggle{{background:none;border:1px solid var(--border);border-radius:8px;padding:10px 16px;width:100%;text-align:left;font-size:13px;color:var(--text3);cursor:pointer;display:flex;align-items:center;gap:8px;transition:border-color .2s}}
.gloss-toggle:hover{{border-color:var(--border-h)}}
.gloss-toggle .arr{{transition:transform .2s;color:var(--dim)}}.gloss-toggle .arr.open{{transform:rotate(90deg)}}
.gloss-list{{display:none;margin-top:10px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px 20px;font-size:12px;color:var(--text2);line-height:1.8}}
.gloss-list.show{{display:block}}.gloss-list strong{{color:var(--text);font-weight:500}}
.tooltip{{position:fixed;max-width:260px;background:var(--card);border:1px solid var(--border-h);border-radius:8px;padding:8px 12px;font-size:13px;color:var(--text);line-height:1.5;pointer-events:none;opacity:0;transition:opacity .12s;z-index:1000;box-shadow:0 4px 20px rgba(0,0,0,.6)}}
.tooltip.visible{{opacity:1}}
.tooltip .arrow{{position:absolute;width:8px;height:8px;background:var(--card);border:1px solid var(--border-h);transform:rotate(45deg)}}
.tooltip .arrow.above{{bottom:-5px;left:calc(50% - 4px);border-top:none;border-left:none}}
.tooltip .arrow.below{{top:-5px;left:calc(50% - 4px);border-bottom:none;border-right:none}}
.refresh-bar{{width:100%;max-width:1100px;height:2px;background:var(--border);border-radius:1px;margin-bottom:20px;overflow:hidden}}
.refresh-bar .fill{{height:100%;background:var(--accent);width:0%;animation:refresh 10s linear infinite}}
@keyframes refresh{{0%{{width:0%}}100%{{width:100%}}}}
@media(max-width:1100px){{.svc-grid{{grid-template-columns:repeat(2,1fr)}}.gc-grid{{grid-template-columns:1fr}}.shields{{gap:14px}}.s-card{{width:135px}}}}
@media(max-width:600px){{body{{padding:16px}}.svc-grid{{grid-template-columns:1fr}}.gc-grid{{grid-template-columns:1fr}}.shields{{gap:10px}}.s-card{{width:120px}}.chain{{flex-direction:column}}.arrow{{transform:rotate(90deg)}}}}
</style>
</head>
<body>
<div class="refresh-bar"><div class="fill"></div></div>
<div class="header">
  <div class="pid" data-tip="Process ID do maestro no sistema operacional">PID do Processo</div>
  <h1>Cadeia de Supervisão</h1>
  <div class="sub">Watchdog → Vigilante → Guardian → Maestro</div>
</div>
<div class="narrativa"><div class="pulse ok" id="nP"></div><div class="msg" id="nM"></div><div class="tempo" id="nT"></div></div>
<div class="gc-section"><h3>Guardian — Motor de Correção Automática</h3><div class="gc-grid">
  <div class="gc-card" data-tip="Vigia processos, mata duplicatas e reinicia serviços mortos. Consulta o Maestro antes de cada ação.">
    <div class="gc-top"><div class="gc-dot ok" id="gcDot"></div><div class="gc-title">Status do Guardian</div><div class="gc-badge ok" id="gcBadge">MONITORANDO</div></div>
    <div class="gc-metrics"><div class="gc-metric"><div class="val" id="gcRam">—</div><div class="lbl">RAM Livre</div></div><div class="gc-metric"><div class="val" id="gcDisk">—</div><div class="lbl">Disco Livre</div></div><div class="gc-metric"><div class="val" id="gcAcoes">0</div><div class="lbl">Ações</div></div></div>
    <div class="gc-actions" id="gcAct"></div>
  </div>
  <div class="gc-card" data-tip="Serviços que o Guardian protege automaticamente.">
    <div class="gc-top"><div class="gc-dot" style="background:var(--accent)"></div><div class="gc-title">Serviços Protegidos</div></div>
    <div id="gcProt" style="font-size:12px;color:var(--text2);line-height:1.8"></div>
  </div>
</div></div>
<div class="servicos" id="sSec"><h3>Serviços Registrados</h3><div class="svc-grid" id="sGrid"></div></div>
<div class="flow"><h3>Cadeia de Execução</h3><div class="chain">
  <div class="node" data-tip="Mantém o Vigilante vivo. Reabre em 20s se morrer."><div class="n-label">Keeper</div><div class="n-freq">20s</div><div class="n-pid" id="pK">watchdog</div></div>
  <div class="arrow">→</div>
  <div class="node" data-tip="Orquestra timers, vigia arquivos, sync git."><div class="n-label">Vigilante</div><div class="n-freq">5min</div><div class="n-pid" id="pV">vigilante</div></div>
  <div class="arrow">→</div>
  <div class="node" data-tip="Protege, mata duplicatas, reinicia serviços mortos."><div class="n-label">Guardian</div><div class="n-freq">20s</div><div class="n-pid" id="pG">—</div></div>
  <div class="arrow">→</div>
  <div class="node" data-tip="Ponto único de decisão: singleton, cooldown 15s."><div class="n-label">Maestro</div><div class="n-freq">Fase 2</div><div class="n-pid" id="pM">—</div></div>
</div></div>
<div class="guerra"><h3>Escudo do Sistema</h3><div class="shields" id="shields"></div></div>
<div class="log"><h3>Log do Guardian</h3><div class="log-box" id="logG"></div></div>
<div class="log"><h3>Log do Maestro</h3><div class="log-box" id="logM"></div></div>
<div class="glossario"><button class="gloss-toggle" onclick="document.getElementById('gL').classList.toggle('show');document.getElementById('gA').classList.toggle('open')"><span class="arr" id="gA">▶</span> Glossário</button>
<div class="gloss-list" id="gL"><strong>Watchdog</strong> — Vigia o Vigilante. Reabre em 20s.<br><strong>Vigilante</strong> — Orquestra timers e sync git.<br><strong>Guardian</strong> — Motor de correção: vigia, mata, reinicia. Consulta o Maestro.<br><strong>Maestro</strong> — Decisão única: singleton, cooldown, inventário.<br><strong>Singleton</strong> — Apenas 1 instância por serviço.<br><strong>Cooldown</strong> — 15s mínimo entre reinícios.<br><strong>Heartbeat</strong> — Sinal de vida periódico.<br><strong>Degraded</strong> — Funciona mas com alerta.<br><strong>Órfão</strong> — Processo sobrado de sessão anterior.<br><strong>Fallback</strong> — Plano B se Maestro cair.<br><strong>PID</strong> — Número único do processo no OS.<br><strong>FileSystemWatcher</strong> — Vigia mudanças em arquivos.</div></div>
<div class="tooltip" id="tip"><div class="arrow" id="tA"></div><span id="tT"></span></div>
<script>
const D={s};
function now(){{return Date.now()/1000}}
function ago(sec){{if(!sec)return'—';const d=now()-sec;if(d<60)return Math.floor(d)+'s';if(d<3600)return Math.floor(d/60)+'min';if(d<86400)return Math.floor(d/3600)+'h';return Math.floor(d/86400)+'d'}}
function render(){{const sv=D.servicos;const vivos=Object.values(sv).filter(v=>v.vivo);const mortos=Object.entries(sv).filter(([,v])=>!v.vivo);
const np=document.getElementById('nP'),nm=document.getElementById('nM'),nt=document.getElementById('nT');
if(vivos.length===0){{np.className='pulse err';nm.textContent='Nenhum serviço ativo.'}}
else if(mortos.length>0){{np.className='pulse warn';nm.textContent=vivos.length+' vivo(s). Mortos: '+mortos.map(([k,v])=>v.display).join(', ')}}
else{{np.className='pulse ok';nm.textContent='Todos os '+vivos.length+' serviços ativos.'}}
nt.textContent='atualizado '+new Date().toLocaleTimeString('pt-BR');
const gc=D.guardian;const gd=document.getElementById('gcDot'),gb=document.getElementById('gcBadge');
if(gc.status==='ok'){{gd.className='gc-dot ok';gb.className='gc-badge ok';gb.textContent='MONITORANDO'}}
else if(gc.status==='degraded'){{gd.className='gc-dot warn';gb.className='gc-badge warn';gb.textContent='DEGRADED'}}
else{{gd.className='gc-dot err';gb.className='gc-badge err';gb.textContent='OFFLINE'}}
document.getElementById('gcRam').textContent=gc.ram_mb?Math.round(gc.ram_mb)+'MB':'—';
document.getElementById('gcDisk').textContent=gc.disk_gb?gc.disk_gb.toFixed(1)+'GB':'—';
document.getElementById('gcAcoes').textContent=gc.actions?gc.actions.length:0;
const ga=document.getElementById('gcAct');ga.innerHTML='';
(gc.actions||[]).forEach(a=>{{const m=typeof a==='string'?a:JSON.stringify(a);ga.innerHTML+='<div class="act"><span class="ts"></span>'+m+'</div>'}});
if(!gc.actions||gc.actions.length===0)ga.innerHTML='<div class="act" style="color:var(--text3)">Sem ações corretivas</div>';
const gp=document.getElementById('gcProt');gp.innerHTML='';
['tts_service.py','widget_edge.py','dialogo.py','jarvis_bridge.py'].forEach(p=>{{const svc=sv[p];const vivo=svc&&svc.vivo;const st=vivo?'<span style="color:var(--ok)">● vivo</span>':'<span style="color:var(--err)">● morto</span>';const pid=svc?' — PID '+svc.pid:'';gp.innerHTML+='<div>'+(svc?svc.display:p.replace('.py',''))+': '+st+pid+'</div>'}});
const sg=document.getElementById('sGrid');sg.innerHTML='';
Object.entries(sv).forEach(([k,v])=>{{const d=document.createElement('div');d.className='svc';d.innerHTML='<div class="svc-top"><div class="svc-dot '+(v.vivo?'vivo':'morto')+'"></div><div class="svc-name">'+v.display+'</div><div class="svc-status">'+(v.vivo?'VIVO':'MORTO')+'</div></div><div class="svc-pid">PID '+v.pid+'</div><div class="svc-owner">owner: '+v.owner+'</div>'+(v.mem_mb?'<div class="svc-mem">'+v.mem_mb+'MB RAM</div>':'')+(v.motivo?'<div class="svc-heart">'+v.motivo+'</div>':'');sg.appendChild(d)}});
const pm=sv['runtime_maestro.py'];
document.getElementById('pM').textContent=pm?'PID '+pm.pid:'—';
document.getElementById('pG').textContent=sv['system_guardian.py']?'PID '+sv['system_guardian.py'].pid:'guardian';
const sh=document.getElementById('shields');sh.innerHTML='';
const shieldMap=[['widget_edge.py','Widget'],['jarvis_bridge.py','Bridge'],['tts_service.py','TTS'],['dialogo.py','Dialogo']];
shieldMap.forEach(([k,n])=>{{const svc=sv[k];const vivo=svc&&svc.vivo;
sh.innerHTML+='<div class="s-card"><div class="s-ring"><svg viewBox="0 0 24 24" fill="none" stroke="var(--ok)" stroke-width="1.8"><path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>'+(vivo?'<path d="M9 12l2 2 4-4"/>':'<path d="M15 9l-6 6m0-6l6 6"/>')+'</svg></div><div class="s-name">'+n+'</div><div class="s-status '+(vivo?'ok':'off')+'">'+(vivo?'ONLINE':'OFFLINE')+'</div><div class="s-pid">'+(svc?'PID '+svc.pid:'')+'</div></div>'}});
function renderLog(lines,boxId){{const b=document.getElementById(boxId);b.innerHTML='';
lines.forEach(l=>{{const cls=l.raw.includes('ALERTA')?'alerta':l.raw.includes('WARNING')||l.raw.includes('warn')?'warn':l.raw.includes('reiniciando')||l.raw.includes('Morto')?'ok':'info';
const m=l.raw.replace(/(pid=\\d+)/g,'<span class="hl">$1</span>');
b.innerHTML+='<div><span class="ts">'+l.ts+'</span> <span class="'+cls+'">'+m+'</span></div>'}});
b.scrollTop=b.scrollHeight}}
renderLog(D.log_guardian||[],'logG');renderLog(D.log_maestro||[],'logM');
}}
const tip=document.getElementById('tip'),tT=document.getElementById('tT'),tA=document.getElementById('tA');let tTgt=null;
document.querySelectorAll('[data-tip]').forEach(el=>{{el.onmouseenter=e=>{{tTgt=e.target;tT.textContent=e.target.getAttribute('data-tip');tip.classList.add('visible');pT(e.target)}};el.onmouseleave=()=>{{tip.classList.remove('visible');tTgt=null}}}});
function pT(t){{if(!tTgt)return;const r=t.getBoundingClientRect(),tw=260,th=tip.offsetHeight,vw=window.innerWidth,vh=window.innerHeight;let tl,tt,pos;const cx=r.left+r.width/2;
if(r.top>=th+14){{tt=r.top-th-10;pos='above'}}else if(vh-r.bottom>=th+14){{tt=r.bottom+10;pos='below'}}else{{tt=Math.max(8,Math.min(r.top,vh-th-8));pos='above'}}
tl=Math.max(8,Math.min(cx-tw/2,vw-tw-8));tip.style.left=tl+'px';tip.style.top=tt+'px';
tA.className='arrow';if(pos==='above')tA.classList.add('above');else if(pos==='below')tA.classList.add('below')}}
window.addEventListener('scroll',()=>{{if(tTgt)pT(tTgt)}},{{passive:true}});
render();
</script>
</body></html>'''


def main():
    print("[dashboard] Iniciando gerador...")
    while True:
        try:
            estado = montar_estado()
            html = gerar_html(estado)
            HTML_OUT.write_text(html, encoding='utf-8')
            n_vivos = sum(1 for s in estado['servicos'].values() if s['vivo'])
            n_total = len(estado['servicos'])
            print(f"[dashboard] {datetime.now().strftime('%H:%M:%S')} — {n_vivos}/{n_total} serviços vivos")
        except Exception as e:
            print(f"[dashboard] Erro: {e}")
        time.sleep(10)


if __name__ == '__main__':
    main()
