"""Gera um grafo interativo HTML (vis-network) do conhecimento do ecossistema.

Le o ler-runtime/knowledge/knowledge_graph.json e produz um arquivo HTML standalone
(vis-network via CDN) que abre em qualquer navegador — sem depender do Obsidian.

Nos:   cada item de conhecimento (padrao, decisao, bug, cognitivo, heuristica, framework)
Arestas: itens que compartilham tag/fonte/dominio + hubs de cluster
Cores:  por categoria (paleta fixa)
Tamanho: hubs e nos muito conectados ficam maiores

Uso:
  python scripts/generate-graph-html.py [output.html]

Exit: 0 = sucesso.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
GRAPH_FILE = os.path.join(BASE, 'ler-runtime', 'knowledge', 'knowledge_graph.json')
DEFAULT_OUTPUT = os.path.join(BASE, 'docs', 'grafo.html')

CATEGORIA_COR = {
    'padroes': '#4e79a7',
    'decisoes': '#f28e2b',
    'bugs': '#e15759',
    'cognitivo': '#59a14f',
    'heuristicas': '#76b7b2',
    'frameworks': '#edc948',
    'missoes': '#b07aa1',
}
CATEGORIA_LABEL = {
    'padroes': 'Padroes', 'decisoes': 'Decisoes', 'bugs': 'Bugs',
    'cognitivo': 'Cognitivo', 'heuristicas': 'Heuristicas',
    'frameworks': 'Frameworks', 'missoes': 'Missoes', 'hub': 'Hub',
}

CLUSTERS = {
    'android': ['android-pure-sdk', 'android_pure_sdk'],
    'mp3player': ['mp3player', 'mp3player-metadata-rescue'],
    'ler': ['ler', 'ler_arquitetura', 'ler_auditoria', 'ler_memory', 'ler_aprendizado'],
    'navegacao': ['treinamento_navegacao', 'session'],
    'ecossistema': ['ecossistema-opencode', 'opencode', 'sessao_seguranca', 'sessao_servermanager',
                    'sessao_rustdesk', 'sessao_providermanager', 'sessao_migracao_config',
                    'sessao_limpeza_auth', 'provider_mcp_debug', 'provider_mcp_server.py',
                    'provider_mcp_server.py:52-55', 'workspace_organization'],
    'cognicao': ['meta_cognition'],
}
CLUSTER_COR = {
    'android': '#8dd3c7', 'mp3player': '#ffffb3', 'ler': '#bebada',
    'navegacao': '#fb8072', 'ecossistema': '#80b1d3', 'cognicao': '#fdb462', 'geral': '#b3b3b3',
}


def cluster_of(source):
    src = (source or '').split('+')[0].strip()
    for cluster, sources in CLUSTERS.items():
        if src in sources:
            return cluster
    return 'geral'


def slugify(text, maxlen=60):
    import re
    text = re.sub(r'[^a-zA-Z0-9\u00C0-\u024F\u00E0-\u024F\s-]', '', str(text))
    text = re.sub(r'[-\s]+', '-', text.strip().lower()).strip('-')
    return text[:maxlen] if text else None


def make_id(prefix, text):
    slug = slugify(text)
    if not slug:
        return None
    return f'{prefix}-{slug}'


def extrair_nos():
    with open(GRAPH_FILE, encoding='utf-8') as f:
        g = json.load(f)

    nos = []  # dict id -> meta
    arestas = set()
    nos_por_categoria = defaultdict(list)
    nos_por_tag = defaultdict(list)

    def add_no(nid, label, categoria, tags, title, source=''):
        if source in CLUSTERS:
            cl = source
        else:
            cl = cluster_of(source) if source else 'geral'
        nos.append({'id': nid, 'label': label, 'categoria': categoria,
                    'tags': tags, 'title': title, 'cl': cl, 'grau': 0})

    # itens de conhecimento
    for p in g.get('patterns', []):
        t = (p.get('title', '') or '').strip()
        if not t:
            continue
        nid = make_id('p', t)
        if not nid or any(n['id'] == nid for n in nos):
            continue
        src = p.get('source', '')
        add_no(nid, t, 'padroes', ['padrao', slugify(src) or 'geral'], f'{src}\n\n{p.get("description","")}', src)
        nos_por_categoria['padroes'].append(nid)

    for d in g.get('decisions', []):
        t = (d.get('decision', '') or '').strip()
        if not t:
            continue
        nid = make_id('d', t[:80])
        if not nid or any(n['id'] == nid for n in nos):
            continue
        src = d.get('source', '')
        add_no(nid, t, 'decisoes', ['decisao', slugify(src) or 'geral'], f'{src}\n\n{d.get("rationale","")}', src)
        nos_por_categoria['decisoes'].append(nid)

    for b in g.get('bug_fixes', []):
        t = (b.get('issue', '') or '').strip()
        if not t or t.strip(' -\n\t\r') == '-----------':
            continue
        nid = make_id('b', t[:80])
        if not nid or any(n['id'] == nid for n in nos):
            continue
        src = b.get('source', '')
        add_no(nid, t, 'bugs', ['bug', slugify(src) or 'geral'], f'{src}\n\n{b.get("root_cause","")}', src)
        nos_por_categoria['bugs'].append(nid)

    for c in g.get('cognitive_patterns', []):
        t = c.get('title', '')
        nid = make_id('cog', t)
        if not nid or any(n['id'] == nid for n in nos):
            continue
        dom = slugify(c.get('domain', 'general')) or 'general'
        add_no(nid, t, 'cognitivo', ['cognitivo', dom], f'Dominio: {c.get("domain","")}\n\n{c.get("body","")}')
        nos_por_categoria['cognitivo'].append(nid)

    for h in g.get('heuristics', []):
        t = h.get('title', '')
        nid = make_id('h', t)
        if not nid or any(n['id'] == nid for n in nos):
            continue
        dom = slugify(h.get('domain', '')) or 'geral'
        add_no(nid, t, 'heuristicas', ['heuristica', dom], h.get('description', ''))
        nos_por_categoria['heuristicas'].append(nid)

    for fw in g.get('frameworks', []):
        t = fw.get('name', '')
        nid = make_id('fw', t)
        if not nid or any(n['id'] == nid for n in nos):
            continue
        src = fw.get('source', '')
        add_no(nid, t, 'frameworks', ['framework'], fw.get('description', ''), src)
        nos_por_categoria['frameworks'].append(nid)

    # indice para arestas
    por_tag = defaultdict(list)
    for n in nos:
        for tag in n['tags']:
            por_tag[tag].append(n['id'])

    # arestas: mesma tag/dominio/fonte
    for n in nos:
        for tag in n['tags']:
            if tag in ('geral', 'general', 'padrao', 'decisao', 'bug', 'cognitivo', 'heuristica', 'framework'):
                continue
            for outro in por_tag.get(tag, []):
                if outro != n['id']:
                    arestas.add(tuple(sorted((n['id'], outro))))

    # hubs de cluster
    for cl in CLUSTERS:
        membros = [n['id'] for n in nos if cluster_of(next((t for t in n['tags'] if t != 'padrao' and t != 'decisao' and t != 'bug'), '')) == cl or
                   any(cluster_of(t) == cl for t in n['tags'])]
        # resolve cluster pelo slug da fonte real: use a primeira tag que mapeia
        membros = [n['id'] for n in nos
                   if any(cluster_of(t) == cl and t not in ('geral', 'general') for t in n['tags'])]
        if not membros:
            continue
        hub = f'hub-{cl}'
        if not any(n['id'] == hub for n in nos):
            add_no(hub, f'★ {cl.capitalize()}', 'hub', [f'cluster:{cl}'],
                   f'Hub do cluster {cl} — {len(membros)} itens', cl)
        for m in membros:
            arestas.add(tuple(sorted((hub, m))))

    return nos, arestas


def grau_calcular(nos, arestas):
    graus = defaultdict(int)
    for a, b in arestas:
        graus[a] += 1
        graus[b] += 1
    for n in nos:
        n['grau'] = graus.get(n['id'], 0)


def gerar_html(nos, arestas, output_path):
    max_grau = max((n['grau'] for n in nos), default=1)
    cores = {}
    categorias_por_id = {n['id']: n['categoria'] for n in nos}
    titles = {n['id']: n['title'] for n in nos}
    graus = {n['id']: n['grau'] for n in nos}

    nodes_js = []
    for n in nos:
        cor = CATEGORIA_COR.get(n['categoria'], '#888')
        if n['categoria'] == 'hub':
            cor = CLUSTER_COR.get(n['cl'], '#666')
        size = 10 + int(14 * (n['grau'] / max_grau)) if max_grau else 10
        if n['categoria'] == 'hub':
            size = max(size, 30)
        node_obj = {
            'id': n['id'],
            'label': n['label'],
            'color': cor,
            'size': size,
            'title': titles[n['id']] or n['label'],
            'cat': n['categoria'],
            'cl': n['cl'],
        }
        nodes_js.append(json.dumps(node_obj, ensure_ascii=False))

    edges_js = [json.dumps({'from': a, 'to': b, 'color': '#999', 'width': 1}, ensure_ascii=False)
                for a, b in sorted(arestas)]

    legend_cat = ''.join(
        f'<button class="lg" data-filter="cat" data-value="{c}" data-color="{CATEGORIA_COR.get(c,"#888")}">'
        f'<span class="dot" style="background:{CATEGORIA_COR.get(c,"#888")}"></span>{CATEGORIA_LABEL.get(c,c)}</button>'
        for c in CATEGORIA_COR)
    legend_cl = ''.join(
        f'<button class="lg" data-filter="cl" data-value="{cl}" data-color="{cor}">'
        f'<span class="dot" style="background:{cor}"></span>{cl.capitalize()}</button>'
        for cl, cor in CLUSTER_COR.items())

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Cerebro Vivo — Grafo do Conhecimento</title>
<style>
  body {{ margin:0; font-family:'Segoe UI', sans-serif; background:#1e1e2e; color:#eee; }}
  #header {{ padding:10px 16px; background:#181825; border-bottom:1px solid #313244; }}
  #header h1 {{ font-size:16px; margin:0 0 8px; }}
  #legend {{ display:flex; gap:6px; flex-wrap:wrap; font-size:11px; }}
  .lg {{ display:inline-flex; align-items:center; gap:5px; padding:3px 9px; border-radius:12px;
        border:1px solid #313244; background:#1e1e2e; color:#eee; cursor:pointer; font-size:11px; }}
  .lg:hover {{ border-color:#cdd6f4; background:#313244; }}
  .lg.active {{ border-color:#89b4fa; background:#313244; box-shadow:0 0 6px #89b4fa66; }}
  .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
  #stats {{ margin-top:6px; font-size:11px; color:#a6adc8; }}
  #net {{ width:100vw; height:calc(100vh - 76px); }}
</style>
<script src="vendor/vis-network.min.js"></script>
</head>
<body>
<div id="header">
  <h1>Cerebro Vivo — Grafo do Conhecimento</h1>
  <div id="legend">
    {legend_cat}
    {legend_cl}
    <button class="lg" data-filter="all" data-value="" data-color="#888">✕ Limpar</button>
  </div>
  <div id="stats">{len(nos)} nos | {len(arestas)} conexoes — clique em uma categoria ou cluster para destacar</div>
</div>
<div id="net"></div>
<script>
  const nodes = new vis.DataSet([{ ','.join(nodes_js)}]);
  const edges = new vis.DataSet([{ ','.join(edges_js)}]);
  const container = document.getElementById('net');
  const options = {{
    nodes: {{ shape:'dot', font:{{ size:11, color:'#cdd6f4' }} }},
    edges: {{ smooth:{{ type:'continuous' }} }},
    physics: {{ barnesHut: {{ gravitationalConstant:-3000, springLength:120, springConstant:0.04, damping:0.09 }},
               stabilization: {{ iterations:300 }} }},
    interaction: {{ hover:true, tooltipDelay:120, navigationButtons:true }}
  }};
  const network = new vis.Network(container, {{ nodes, edges }}, options);

  const original = {{}};
  nodes.get().forEach(n => {{
    original[n.id] = {{ color: n.color, size: n.size }};
  }});

  function destacar(filtro, valor) {{
    const btns = document.querySelectorAll('.lg');
    btns.forEach(b => b.classList.remove('active'));
    const alvo = document.querySelector(`.lg[data-filter="${{filtro}}"][data-value="${{valor}}"]`);
    if (alvo) alvo.classList.add('active');

    const atualizacoes = [];
    nodes.get().forEach(n => {{
      let ativo = false;
      if (filtro === 'all') ativo = true;
      else if (filtro === 'cat') ativo = (n.cat === valor);
      else if (filtro === 'cl') ativo = (n.cl === valor);
      if (ativo) {{
        atualizacoes.push({{ id: n.id, color: original[n.id].color, size: original[n.id].size,
                            borderWidth: 2, borderWidthSelected: 2 }});
      }} else {{
        atualizacoes.push({{ id: n.id, color: '#2a2a3c', size: 3, opacity: 0.15,
                            borderWidth: 0, borderWidthSelected: 0 }});
      }}
    }});
    nodes.update(atualizacoes);
    network.fit({{ animation: true }});
  }}

  document.querySelectorAll('.lg').forEach(btn => {{
    btn.addEventListener('click', () => destacar(btn.dataset.filter, btn.dataset.value));
  }});
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Grafo gerado: {output_path}')
    print(f'  {len(nos)} nos | {len(arestas)} conexoes')


def main():
    output = DEFAULT_OUTPUT
    if len(sys.argv) > 1:
        output = sys.argv[1]
    nos, arestas = extrair_nos()
    grau_calcular(nos, arestas)
    gerar_html(nos, arestas, output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
