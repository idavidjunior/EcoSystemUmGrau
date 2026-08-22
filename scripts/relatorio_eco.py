#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatório Eco — dashboard HTML estático autocontido (stdlib puro).

Gera um único arquivo .html com os dados embutidos (abre offline, sem servidor,
sem processo residente) a partir de:
- HSC (runtime/hsc): fidelidade, checks do validator, conflitos por conhecimento
- Memórias (conhecimento/memoria/memories.json): tipos, projetos, recentes
- Runtime (runtime/state.json): projeto ativo, objetivo, pendências
- Integridade: registros suspeitos (kind inválido, campos vazios, ids duplicados)

Uso:
  python scripts/relatorio_eco.py             # gera e abre no navegador
  python scripts/relatorio_eco.py --no-open   # só gera
  python scripts/relatorio_eco.py --saida X.html
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HSC_DIR = ROOT / "runtime" / "hsc"
MEMORIES_FILE = ROOT / "conhecimento" / "memoria" / "memories.json"
STATE_FILE = ROOT / "runtime" / "state.json"
SAIDA_PADRAO = ROOT / "runtime" / "relatorios" / "relatorio_eco.html"

ORDEM_CHECKS = ["numeros", "datas", "entidades", "negacoes",
                "grau_certeza", "fatos_criticos"]
KINDS_VALIDOS = {"decisao", "erro", "padrao", "episodio",
                 "preferencia", "experiencia", "melhoria"}
LIMITE_RECENTES = 20
THRESHOLD_FID = 0.85


def _json(caminho, default):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


# ---------------------------------------------------------------- coleta HSC
def coletar_hsc():
    index = _json(HSC_DIR / "index.json", {}) or {}
    itens = []
    for kid in sorted(index.get("items", {})):
        rec = _json(HSC_DIR / f"{kid}.json", None)
        if not rec:
            continue
        v = rec.get("validation") or {}
        m = rec.get("metrics") or {}
        checks = v.get("checks") or {}
        itens.append({
            "id": rec.get("knowledge_id") or kid,
            "titulo": rec.get("title") or "(sem título)",
            "fid": v.get("compression_fidelity_score"),
            "pass": bool(v.get("pass")),
            "ratio_essence": round(m.get("compression_ratio_essence") or 0, 4),
            "ratio_summary": round(m.get("compression_ratio_summary") or 0, 4),
            "checks": {k: checks.get(k) for k in ORDEM_CHECKS},
            "conflitos": len(rec.get("conflicts") or []),
            "criado_em": rec.get("created_at"),
        })

    fids = [i["fid"] for i in itens if isinstance(i["fid"], (int, float))]
    medias_checks = {}
    for k in ORDEM_CHECKS:
        vals = [i["checks"][k] for i in itens
                if isinstance(i["checks"].get(k), (int, float))]
        if vals:
            medias_checks[k] = round(sum(vals) / len(vals), 3)

    return {
        "itens": itens,
        "total": len(itens),
        "fid_media": round(sum(fids) / len(fids), 4) if fids else None,
        "pass_count": sum(1 for i in itens if i["pass"]),
        "conflitos_total": sum(i["conflitos"] for i in itens),
        "medias_checks": medias_checks,
    }


# ----------------------------------------------------------- coleta memórias
def _data_iso(valor):
    try:
        return datetime.fromisoformat(str(valor)).isoformat()
    except Exception:
        return ""


def coletar_memorias():
    dados = _json(MEMORIES_FILE, [])
    if not isinstance(dados, list):
        return {"erro": "memories.json não é uma lista"}

    problemas = []
    vistos = {}
    for r in dados:
        mid = r.get("id")
        kind = str(r.get("kind") or "")
        if kind not in KINDS_VALIDOS:
            problemas.append({"id": mid,
                              "problema": "kind inválido",
                              "detalhe": kind[:60] or "(vazio)"})
        if not (r.get("task") or "").strip():
            problemas.append({"id": mid, "problema": "task vazia",
                              "detalhe": ""})
        conf = r.get("confidence")
        if conf is None or not (0 <= float(conf) <= 1):
            problemas.append({"id": mid, "problema": "confidence fora de [0,1]",
                              "detalhe": str(conf)})
        vistos[mid] = vistos.get(mid, 0) + 1
    for mid, n in vistos.items():
        if n > 1:
            problemas.append({"id": mid, "problema": "id duplicado",
                              "detalhe": f"{n}x"})

    tipos = Counter(
        r.get("kind") if r.get("kind") in KINDS_VALIDOS else "inválido"
        for r in dados)
    projetos = Counter(
        (r.get("project") or "").strip() or "(sem projeto)" for r in dados)
    recentes = sorted(dados,
                      key=lambda r: _data_iso(r.get("created_at")),
                      reverse=True)[:LIMITE_RECENTES]
    confs = [float(r["confidence"]) for r in dados
             if isinstance(r.get("confidence"), (int, float))
             and 0 <= float(r["confidence"]) <= 1]

    return {
        "total": len(dados),
        "por_tipo": dict(tipos),
        "projetos_top": dict(projetos.most_common(5)),
        "conf_media": round(sum(confs) / len(confs), 2) if confs else None,
        "recentes": [{"id": r.get("id"), "kind": r.get("kind"),
                      "data": _data_iso(r.get("created_at"))[:10],
                      "task": (r.get("task") or "")[:90]}
                     for r in recentes],
        "_problemas": problemas,
    }


# -------------------------------------------------------------- coleta state
def coletar_state():
    s = _json(STATE_FILE, {}) or {}
    pend = s.get("pending") or []
    return {
        "projeto_ativo": s.get("projeto_ativo") or "(nenhum)",
        "objetivo": s.get("objetivo") or "",
        "ultima_tarefa": s.get("ultima_tarefa") or "",
        "pendencias_abertas": sum(1 for p in pend if not p.get("done")),
        "pendencias_total": len(pend),
    }


# ------------------------------------------------------- integridade geral
def coletar_integridadade(hsc, mem):
    achados = list(mem.get("_problemas", []))
    for i in hsc["itens"]:
        if i["pass"] is False and i["fid"] is not None \
                and i["fid"] < THRESHOLD_FID:
            pass  # fid baixa já aparece na tabela; não duplica aqui
    return {"total_problemas": len(achados), "achados": achados[:30]}


# ------------------------------------------------------------------ template
TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório Eco</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--borda:#30363d;--tx:#c9d1d9;--dim:#8b949e;
--azul:#58a6ff;--verde:#3fb950;--verm:#f85149;--amar:#d29922}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--tx);
font:14px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;padding:24px}
h1{font-size:20px;font-weight:600} h2{font-size:15px;font-weight:600;
margin:28px 0 10px;color:var(--azul)}
header{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;
justify-content:space-between;margin-bottom:18px}
.meta{color:var(--dim);font-size:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:12px;margin-bottom:6px}
.card{background:var(--card);border:1px solid var(--borda);border-radius:8px;
padding:14px}
.card .num{font-size:26px;font-weight:700;margin-top:4px}
.card .rot{color:var(--dim);font-size:11px;text-transform:uppercase;
letter-spacing:.05em}
.ok{color:var(--verde)} .ruim{color:var(--verm)} .neutro{color:var(--amar)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
gap:16px}
canvas{background:var(--card);border:1px solid var(--borda);border-radius:8px;
width:100%;height:240px;display:block}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--borda);border-radius:8px;overflow:hidden;font-size:13px}
th{background:#21262d;text-align:left;padding:8px 10px;color:var(--dim);
font-size:11px;text-transform:uppercase}
td{padding:8px 10px;border-top:1px solid var(--borda)}
tr:hover td{background:#1c2129}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;
font-weight:600}
.badge.p{background:#12351f;color:var(--verde)}
.badge.f{background:#3d1618;color:var(--verm)}
.badge.i{background:#3a2c10;color:var(--amar)}
.busca{padding:6px 10px;background:var(--bg);border:1px solid var(--borda);
border-radius:6px;color:var(--tx);margin-bottom:8px;width:260px}
.integ-ok{color:var(--verde)} .integ-item{padding:6px 0;
border-bottom:1px dashed var(--borda);font-size:13px}
.recente{display:flex;gap:8px;padding:5px 0;border-bottom:1px solid #21262d;
font-size:13px}
.recente .k{min-width:86px;color:var(--amar);font-size:11px;
text-transform:uppercase;padding-top:2px}
footer{margin-top:30px;color:var(--dim);font-size:11px;text-align:center}
</style>
</head>
<body>
<header>
  <div><h1>Relatório Eco</h1>
    <div class="meta" id="meta-proj"></div></div>
  <div class="meta" id="meta-ger"></div>
</header>

<div class="cards" id="cards-topo"></div>

<h2>Fidelidade da compressão (limiar 0.85)</h2>
<canvas id="g-fid" height="240"></canvas>

<div class="grid">
 <div><h2>Média dos checks do validador</h2><canvas id="g-checks" height="240"></canvas></div>
 <div><h2>Memórias por tipo</h2><canvas id="g-mem" height="240"></canvas></div>
</div>

<h2>Conhecimentos comprimidos (HSC)</h2>
<input class="busca" id="q" placeholder="filtrar...">
<table id="t-hsc"><thead><tr>
<th>ID</th><th>Título</th><th>Fid.</th><th>Status</th>
<th>Essence</th><th>Summary</th><th>Conflitos</th><th>Criado em</th>
</tr></thead><tbody></tbody></table>

<h2>Integridade dos dados</h2>
<div class="card" id="integ"></div>

<h2>Memórias recentes</h2>
<div class="card" id="rec"></div>

<footer>gerado localmente, sem servidor — regenere com
python scripts/relatorio_eco.py</footer>

<script>window.ECO_DADOS=%%PAYLOAD%%;</script>
<script>
const D=window.ECO_DADOS,TH=__THRESHOLD__;
const $=id=>document.getElementById(id);

function cor(v){return v>=TH?'var(--verde)':v>=0.7?'var(--amar)':'var(--verm)'}

function barras(cv,rotulos,valores,opts={}){
  const dpr=devicePixelRatio||1,W=cv.clientWidth,H=cv.clientHeight;
  cv.width=W*dpr;cv.height=H*dpr;
  const c=cv.getContext('2d');c.scale(dpr,dpr);
  const pad={l:44,r:12,t:14,b:opts.inclina?58:24};
  const max=opts.max??Math.max(...valores,1)*1.08;
  const iw=W-pad.l-pad.r,ih=H-pad.t-pad.b,n=valores.length||1;
  const bw=Math.min(iw/n*0.62,46);
  c.strokeStyle='#30363d';c.fillStyle='#8b949e';c.font='10px sans-serif';
  c.textAlign='right';
  for(let g=0;g<=4;g++){const y=pad.t+ih*g/4;
    c.beginPath();c.moveTo(pad.l,y);c.lineTo(W-pad.r,y);c.stroke();
    c.fillText((max*(1-g/4)).toFixed(opts.dec??1),pad.l-5,y+3);}
  valores.forEach((v,i)=>{
    const x=pad.l+iw*(i+.5)/n-bw/2,h=max?v/max*ih:0,y=pad.t+ih-h;
    c.fillStyle=opts.cor?opts.cor(v,i):(v>=TH?'#3fb950':'#58a6ff');
    c.fillRect(x,y,bw,h);
    c.save();c.translate(pad.l+iw*(i+.5)/n,pad.t+ih+12);
    if(opts.inclina){c.rotate(-Math.PI/4);c.textAlign='right';
      c.fillStyle='#8b949e';c.fillText(String(rotulos[i]),0,0);}
    else{c.textAlign='center';c.fillStyle='#8b949e';
      c.fillText(String(rotulos[i]).slice(0,14),0,10);}
    c.restore();});
  if(opts.valorTopo){c.textAlign='center';c.font='bold 10px sans-serif';
    valores.forEach((v,i)=>{if(!max)return;
      const x=pad.l+iw*(i+.5)/n,y=pad.t+ih-v/max*ih-4;
      c.fillStyle='#c9d1d9';c.fillText(String(v),x,y);});}
}

function card(rot,num,cls=''){return `<div class="card">
<div class="rot">${rot}</div><div class="num ${cls}">${num}</div></div>`}

(function topo(){
  $('meta-ger').textContent='gerado em '+D.gerado_em;
  $('meta-proj').textContent='projeto ativo: '+D.state.projeto_ativo+
    (D.state.ultima_tarefa?' · última tarefa: '+trunc(D.state.ultima_tarefa,70):'');
  const h=D.hsc,m=D.memorias,st=D.state,integ=D.integridade.total_problemas;
  let html='';
  html+=card('conhecimentos',h.total);
  html+=card('fidelidade média',h.fid_media??'—',
    h.fid_media==null?'':(h.fid_media>=TH?'ok':'ruim'));
  html+=card('conflitos',h.conflitos_total,
    h.conflitos_total?'neutro':'ok');
  html+=card('memórias',m.total);
  html+=card('pendências',st.pendencias_abertas+'/'+st.pendencias_total,
    st.pendencias_abertas?'neutro':'ok');
  html+=card('integridade',integ?integ+' problema'+(integ>1?'s':''):'OK',
    integ?'ruim':'ok');
  $('cards-topo').innerHTML=html;
})();

function trunc(s,n){return s.length>n?s.slice(0,n)+'…':s}

(function grafFid(){
  const it=D.hsc.itens;if(!it.length)return void($('g-fid').outerHTML=
    '<div class="card meta">nenhum conhecimento comprimido ainda</div>');
  barras($('g-fid'),it.map(i=>i.id),it.map(i=>i.fid||0),
    {max:1,dec:1,inclina:true,valorTopo:true});
})();

(function grafChecks(){
  const mc=D.hsc.medias_checks,chaves=Object.keys(mc);
  if(!chaves.length)return void($('g-checks').outerHTML=
    '<div class="card meta">sem checks registrados</div>');
  barras($('g-checks'),chaves.map(k=>k.replace('_',' ')),chaves.map(k=>mc[k]),
    {max:1,dec:2,inclina:true,valorTopo:true});
})();

(function grafMem(){
  const t=D.memorias.por_tipo,chaves=Object.keys(t);
  if(!chaves.length)return void($('g-mem').outerHTML=
    '<div class="card meta">sem memórias</div>');
  barras($('g-mem'),chaves,chaves.map(k=>t[k]),
    {dec:0,inclina:true,valorTopo:true});
})();

(function tabela(){
  const tb=document.querySelector('#t-hsc tbody'),q=$('q');
  function render(){
    const f=(q.value||'').toLowerCase();
    tb.innerHTML=D.hsc.itens.filter(i=>
      !f||(i.id+' '+i.titulo).toLowerCase().includes(f)).map(i=>{
      const fid=i.fid==null?'—':i.fid.toFixed(4);
      return `<tr><td>${i.id}</td><td>${esc(i.titulo)}</td>
<td style="color:${cor(i.fid||0)};font-weight:600">${fid}</td>
<td><span class="badge ${i.pass?'p':'f'}">${i.pass?'PASS':'FAIL'}</span></td>
<td>${i.ratio_essence}</td><td>${i.ratio_summary}</td>
<td>${i.conflitos||''}</td><td class="meta">${(i.criado_em||'').slice(0,10)}</td></tr>`;
    }).join('')||'<tr><td colspan="8" class="meta">nada</td></tr>';}
  q.oninput=render;render();
})();

function esc(s){return String(s).replace(/&/g,'&amp;')
  .replace(/</g,'&lt;').replace(/>/g,'&gt;')}

(function integridade(){
  const el=$('integ'),a=D.integridade.achados,n=D.integridade.total_problemas;
  if(!n)return void(el.innerHTML='<span class="integ-ok">'+
    'Nenhum registro suspeito encontrado.</span>');
  el.innerHTML='<span class="ruim">'+n+' problema(s):</span>'+a.map(p=>
    `<div class="integ-item"><span class="badge i">${esc(p.problema)}</span>
 memória ${p.id} — <span class="meta">${esc(p.detalhe||'')}</span></div>`).join('');
})();

(function recentes(){
  $('rec').innerHTML=(D.memorias.recentes||[]).map(r=>
    `<div class="recente"><span class="k">#${r.id} ${esc(String(r.kind||''))}</span>
<span>${esc(trunc(r.task||'(sem título)',110))}
${r.data?'<span class="meta">· '+r.data+'</span>':''}</span></div>`).join('')
   ||'<span class="meta">nenhuma</span>';
})();
</script>
</body>
</html>
"""


def gerar_html(coleta: dict) -> str:
    payload = json.dumps(coleta, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("%%PAYLOAD%%", payload) \
                   .replace("__THRESHOLD__", str(THRESHOLD_FID))


def main():
    ap = argparse.ArgumentParser(description="Relatório Eco estático")
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()

    hsc = coletar_hsc()
    mem = coletar_memorias()
    problemas = mem.pop("_problemas", []) if isinstance(mem, dict) else []

    integridade = {
        "total_problemas": len(problemas),
        "achados": problemas[:30],
    }
    coleta = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hsc": hsc,
        "memorias": mem,
        "state": coletar_state(),
        "integridade": integridade,
    }

    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = saida.with_suffix(".tmp")
    tmp.write_text(gerar_html(coleta), encoding="utf-8")
    os.replace(tmp, saida)
    print(f"[OK] relatório gerado: {saida}")

    if not a.no_open:
        try:
            os.startfile(str(saida))  # Windows
        except Exception:
            print("(abra manualmente no navegador)")


if __name__ == "__main__":
    sys.exit(main())
