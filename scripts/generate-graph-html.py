"""Gera um grafo interativo HTML (vis-network) do conhecimento do ecossistema.

Le o vault Obsidian (conhecimento/notas/*.md) e produz um arquivo HTML
standalone (vis-network via CDN) que abre em qualquer navegador. O vault e a
fonte viva: notas + links [[wikilinks]] (incluindo os criados pelo Smart
Connections no Obsidian). Assim o grafico reflete exatamente o que esta no
Obsidian — sinapses semanticas incluidas.

Nos:   cada nota .md (conhecimento + hubs)
Arestas: links bidirecionais [[wikilinks]] presentes em cada nota
Cores:  por categoria (paleta fixa)
Tamanho: hubs e nos muito conectados ficam maiores

Uso:
  python scripts/generate-graph-html.py [output.html]

Exit: 0 = sucesso.
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
VAULT_DIR = os.path.join(BASE, 'conhecimento', 'notas')
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


# --- Status dos bugs ------------------------------------------------------
# Bugs da base sao historicos: a maioria ja foi corrigido. O campo `fix`
# registra a correcao. Permitimos distinguir visualmente no grafo.
STATUS_LABEL = {
    'resolvido': 'Resolvido',
    'pendente': 'Pendente',
    'conhecido': 'Limitacao conhecida',
}
STATUS_COR = {
    'resolvido': '#2ecc71',
    'pendente': '#e74c3c',
    'conhecido': '#f1c40f',
}

# ---------------------------------------------------------------------------
# Leitura do vault Obsidian (fonte viva do conhecimento) -------------------
# O gerador agora le o vault conhecimento/notas/*.md em vez do JSON.
# Assim tudo que existe no Obsidian (notas + links criados pelo Smart
# Connections ou manualmente) aparece no grafo do widget automaticamente.
# O JSON continua sendo a entrada/semente via generate-obsidian-notes.py.
# ---------------------------------------------------------------------------

WIKI_LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

# Mapeia tags de fonte (ex: 'mp3player-metadata-rescue') -> cluster
_SOURCE_CLUSTER = {}
for _cl, _fontes in CLUSTERS.items():
    for _f in _fontes:
        _SOURCE_CLUSTER[_f] = _cl

# Tags genericas que nao sao fontes/semanticas
_GENERIC_TAGS = frozenset({
    'padrao', 'decisao', 'bug', 'cognitivo', 'heuristica', 'framework',
    'missao', 'hub', 'geral', 'general', 'leraprendizado', 'episodio',
})


def _parse_frontmatter(content):
    """Parse YAML frontmatter simples. Retorna (dict_fm, body_str)."""
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    fm_text = parts[1]
    body = parts[2]
    fm = {}
    for line in fm_text.strip().split('\n'):
        line = line.rstrip()
        if not line.strip() or line.strip().startswith('#'):
            continue
        # linha sem indentacao = nova key
        if not line.startswith(' ') and ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if val.startswith('[') and val.endswith(']'):
                fm[key] = [v.strip() for v in val[1:-1].split(',') if v.strip()]
            else:
                fm[key] = val
    return fm, body


def _extract_wikilinks(text):
    """Extrai todos os alvos [[wikilink]] do texto (body da nota)."""
    return set(m.group(1).strip() for m in WIKI_LINK_RE.finditer(text))


def _source_from_tags(tags):
    """Resolve qual fonte/cluster a nota pertence a partir das tags."""
    for t in tags:
        if t not in _GENERIC_TAGS:
            return t
    return ''


def extrair_nos():
    """Constrói nós e arestas a partir do vault Obsidian vivo.

    Cada .md vira um nó; cada [[wikilink]] vira uma aresta.
    Isso capta automaticamente conexões criadas pelo Smart Connections.
    """
    nos = []
    arestas = set()
    nos_por_id = {}

    def add_no(nid, label, categoria, tags, title, source='', cluster=''):
        # Notas duplicadas podem existir em pastas de categoria diferentes
        # (ex: cognitivo/X.md e missoes/X.md). Reuse a mesma nota para evitar
        # id duplicado no vis.DataSet, que lanca 'Cannot add item: id already
        # exists' e aborta a criacao da rede -> grafo em branco.
        if nid in nos_por_id:
            return nos_por_id[nid]
        cl = cluster or (_SOURCE_CLUSTER.get(source, 'geral') if source else 'geral')
        # Se source nao esta no CLUSTERS, tenta cluster_of(source)
        if not cl or cl == 'geral':
            cl = cluster_of(source) if source else 'geral'
        n = {'id': nid, 'label': label, 'categoria': categoria,
             'tags': tags or [], 'title': title, 'cl': cl, 'grau': 0,
             'source': source}
        nos.append(n)
        nos_por_id[nid] = n
        return n

    # ---- ler TODAS as notas do vault (incl. _hubs) ----
    md_files = sorted(Path(VAULT_DIR).rglob('*.md'))
    no_cache = {}  # slug -> set of wikilinks (guardado antes de add_no perder body)

    for f in md_files:
        rel = f.relative_to(VAULT_DIR)
        is_hub = rel.parts[0] == '_hubs'
        cat_from_folder = 'hub' if is_hub else rel.parts[0]
        slug = f.stem
        content = f.read_text(encoding='utf-8')
        fm, body = _parse_frontmatter(content)
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        aliases = fm.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases]

        # categoria interna
        categoria_map = {
            'padroes': 'padroes', 'decisoes': 'decisoes',
            'bugs': 'bugs', 'cognitivo': 'cognitivo',
            'heuristicas': 'heuristicas', 'frameworks': 'frameworks',
            'missoes': 'missoes', 'hub': 'hub',
        }
        categoria = categoria_map.get(cat_from_folder, cat_from_folder)

        source = _source_from_tags(tags)
        cluster = _SOURCE_CLUSTER.get(source, '') or ''

        # label = aliases[0] ou heading
        label = aliases[0] if aliases else slug
        h_match = re.search(r'^# (.+)$', body, re.MULTILINE)
        if h_match:
            label = h_match.group(1).strip()

        # Para hubs: tenta resolver cluster pelo nome (cluster-hub-X)
        if is_hub and 'cluster-hub-' in slug:
            cluster = slug.replace('cluster-hub-', '').strip()

        # title (tooltip) = body curto
        body_clean = re.sub(r'##\s+\S+', '', body)  # remove secoes
        body_excerpt = ' '.join(body_clean.split())[:250]
        title = body_excerpt if body_excerpt else label

        # status de bug
        status = None
        if categoria == 'bugs':
            status = _inferir_status_bug(body)

        n = add_no(slug, label, categoria, tags, title, source, cluster)
        if status:
            nos_por_id[slug]['status'] = status

        # armazenar wikilinks desta nota (antes de possivelmente ser usado)
        links = _extract_wikilinks(body)
        no_cache[slug] = links

    # ---- construir arestas a partir dos wikilinks reais ----
    id_set = set(nos_por_id)
    for slug, links in no_cache.items():
        for link in links:
            # link pode ser 'nota-slug' ou 'nota-slug|alias' — pega so o slug
            link_slug = link.split('|')[0].strip()
            if link_slug in id_set and slug in id_set:
                arestas.add(tuple(sorted((slug, link_slug))))

    print(f'  Lidos {len(md_files)} notas do vault -> {len(nos)} nos, '
          f'{len(arestas)} arestas')
    return nos, arestas


def _inferir_status_bug(body):
    """Deriva status de bug a partir do conteudo da nota no vault."""
    low = body.lower()
    # secao Correcao
    has_correcao = '## correcao' in low or 'correcao' in low and '##' in body
    if not has_correcao:
        return 'pendente'
    correcao_match = re.search(r'## Correcao\s*\n(.*)', body, re.DOTALL | re.IGNORECASE)
    correcao_texto = correcao_match.group(1).strip() if correcao_match else ''
    if not correcao_texto or all(c in ' \t-\n\r' for c in correcao_texto):
        return 'pendente'
    if any(k in correcao_texto.lower() for k in (
        'aceito', 'accepted', 'limitacao', 'known', 'nao-critica',
        'non-critic', 'workaround')):
        return 'conhecido'
    return 'resolvido'


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
        if n['categoria'] == 'bugs':
            cor = STATUS_COR.get(n.get('status'), cor)
        size = 10 + int(14 * (n['grau'] / max_grau)) if max_grau else 10
        if n['categoria'] == 'hub':
            size = max(size, 30)
        label = n['label']
        if n['categoria'] == 'bugs':
            st = n.get('status', 'pendente')
            label = f"{'✔' if st == 'resolvido' else ('†' if st == 'conhecido' else '✖')} {label}"
        node_obj = {
            'id': n['id'],
            'label': label,
            'color': cor,
            'size': size,
            'title': titles[n['id']] or n['label'],
            'cat': n['categoria'],
            'cl': n['cl'],
        }
        if n['categoria'] == 'bugs':
            node_obj['st'] = n.get('status', 'resolvido')
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
    legend_st = ''.join(
        f'<button class="lg" data-filter="st" data-value="{st}" data-color="{cor}">'
        f'<span class="dot" style="background:{cor}"></span>Bug: {label}</button>'
        for st, label in STATUS_LABEL.items())
    legend_st = '<span style="opacity:.6">|</span> ' + legend_st

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
  #wrap {{ display:flex; }}
  #net {{ flex:1; height:calc(100vh - 100px); }}
  #painel {{ display:none; width:320px; margin:10px 12px 10px 0; background:#181825; border:1px solid #313244;
            border-radius:8px; padding:12px; overflow-y:auto; max-height:calc(100vh - 120px); }}
  #painel.visivel {{ display:block; }}
  #painel h2 {{ font-size:13px; margin:0 0 10px; display:flex; align-items:center; gap:6px; }}
  #painel .count {{ font-size:10px; color:#a6adc8; font-weight:normal; }}
  #painel ul {{ list-style:none; margin:0; padding:0; }}
  #painel li {{ padding:7px 8px; border-bottom:1px solid #232335; font-size:11px; cursor:pointer; }}
  #painel li:hover {{ background:#232335; }}
  #painel li.sel {{ background:#313244; border-left:3px solid #89b4fa; }}
  .titulo-sel {{ color:#ffffff; }}
  #painel .titulo {{ color:#cdd6f4; font-weight:600; }}
  #painel .spec {{ color:#a6adc8; margin-top:2px; max-height:2.4em; overflow:hidden; display:-webkit-box;
                  -webkit-line-clamp:2; -webkit-box-orient:vertical; }}
</style>
<script src="vendor/vis-network.min.js"></script>
</head>
<body>
<div id="header">
  <h1>Cerebro Vivo — Grafo do Conhecimento</h1>
  <div id="legend">
    {legend_cat}
    {legend_cl}
    {legend_st}
    <button class="lg home" data-filter="home" data-value="" data-color="#89b4fa">🏠 Home</button>
    <button class="lg" data-filter="all" data-value="" data-color="#888">✕ Limpar</button>
  </div>
  <div id="stats">{len(nos)} nos | {len(arestas)} conexoes — clique em uma categoria ou cluster para destacar</div>
</div>
<div id="wrap">
  <div id="net"></div>
  <div id="painel"></div>
</div>
<script>
  const nodes = new vis.DataSet([{ ','.join(nodes_js)}]);
  const edges = new vis.DataSet([{ ','.join(edges_js)}]);
  const container = document.getElementById('net');
  const options = {{
    nodes: {{ shape:'dot', font:{{ size:11, color:'#cdd6f4' }} }},
    edges: {{ smooth:{{ type:'continuous' }} }},
    // Movimento organico: SEM estabilizacao, timestep lento, velocidade
    // limitada -> a rede nunca "congela", respira em movimento perpetuo.
    physics: {{
      enabled: true,
      solver: 'barnesHut',
      barnesHut: {{
        theta: 0.5,
        gravitationalConstant: -620,
        centralGravity: 0.28,
        springLength: 120,
        springConstant: 0.03,
        damping: 0.88,
        avoidOverlap: 0.55
      }},
      minVelocity: 0,
      maxVelocity: 6,
      timestep: 0.2,
      adaptiveTimestep: false,
      stabilization: false
    }},
    interaction: {{ hover:true, tooltipDelay:120, navigationButtons:true, zoomSpeed:0.6 }}
  }};
  const network = new vis.Network(container, {{ nodes, edges }}, options);

  // Enquadra o grafo e liberta a fisica para o balanco organico perpetuo.
  setTimeout(() => network.fit({{ animation: true }}), 1200);

  // Posicao/zoom iniciais capturados; a fisica NAO congela (cerebro vivo).
  let viewInical = null;
  let scaleInical = null;
  let posIniciais = {{}};
  const guardaInicial = () => {{
    if (network.getScale && !viewInical) {{
      viewInical = network.getViewPosition();
      scaleInical = network.getScale();
      posIniciais = {{}};
      nodes.get().forEach(n => {{
        const p = network.getPositions([n.id])[n.id];
        posIniciais[n.id] = {{ x: p.x, y: p.y }};
      }});
      // Mantem o cerebro vivo: balanco lento e respirando.
      network.setOptions({{ physics: {{ barnesHut: {{
        gravitationalConstant: -620, springLength: 120, springConstant: 0.018,
        damping: 0.92, centralGravity: 0.30, avoidOverlap: 0.55
      }} }} }});
    }}
  }};
  setTimeout(guardaInicial, 2500);

  // --- Respiracao do layout ------------------------------------------------
  // Ciclo lento (~22s) que alterna a energia da fisica: "inspira" (mais
  // repulsao, espaca) e "expira" (mais coesao, aproxima) sem nunca parar.
  let _respirando = 1;
  setInterval(() => {{
    _respirando = 0.78 + 0.22 * Math.sin(Date.now() * 0.00028);
    network.setOptions({{ physics: {{ barnesHut: {{
      gravitationalConstant: -620 * _respirando,
      centralGravity: 0.30 * (1.35 - _respirando),
      springConstant: 0.018 * (1.6 - _respirando)
    }} }} }});
  }}, 3000);

  // =========================================================================
  // ZOOM-MICROSCOPIO + EXPANDIR
  // O zoom ganha papel narrativo: recuar para ver o todo ("microscopio de
  // visao ampla") e avancar para ver o detalhe ("microscopio focalizado").
  // =========================================================================
  var _lastClusterScale = 1;
  var _clusterFactor = 0.55;
  var _clusterAtivo = false;

  // --- MICROSCOPIO ---
  // Mantem as etiquetas legiveis ao ampliar: o canvas do vis-network sobe a
  // escala do node, mas a fonte cresce junto (torna ilegivel). Compensamos
  // com font.size = base / scale (fonte volta ao tamanho "real" na tela).
  // Quando as etiquetas estiverem ocultas pelo usuario, mantemos 0.
  function _ajustarFontes() {{
    var oculto = (typeof localStorage !== 'undefined' &&
                  localStorage.getItem('labelsOcultos') === 'true');
    if (oculto) return; // usuario escondeu: nao forca visibilidade via zoom
    var scale = network.getScale ? network.getScale() : 1;
    if (scale < 0.4) scale = 0.4; // nunca fique muito pequena
    var tam = Math.round(13 / scale);
    if (tam > 22) tam = 22;
    nodes.update(nodes.get().map(function(n) {{
      if (n.isHidden) return null;
      return {{ id: n.id, font: Object.assign({{}}, n.font, {{ size: tam }}) }};
    }}).filter(Boolean));
  }}

  // --- EXPANDIR (clustering por proximidade de folhas) ---
  // Em zoom-out, agrupa nos-folha (grau baixo) cercando-os. Em zoom-in,
  // abre os clusters revelando os nos internos (efeito "expandir").
  function _fazerClusteres() {{
    if (nodes.get().length <= 80) return; // so para grafos com volume
    var grau = {{}};
    edges.get().forEach(function(e) {{
      grau[e.from] = (grau[e.from] || 0) + 1;
      grau[e.to] = (grau[e.to] || 0) + 1;
    }});
    // candidatos: nos-folha (grau 1)
    var folhas = nodes.get().filter(function(n) {{
      return !n.isHidden && (grau[n.id] || 0) <= 1;
    }});
    // agrupa folhas adjacentes a um mesmo no em clusters de ~8
    var agrupados = {{}};
    var usados = new Set();
    for (var i = 0; i < folhas.length; i++) {{
      var f = folhas[i];
      if (usados.has(f.id)) continue;
      // pega uma folha, agrupa ela + ate 7 adjacentes
      var grupo = [f.id]; usados.add(f.id);
      var adjacentes = edges.get()
        .filter(function(e) {{ return e.from === f.id || e.to === f.id; }})
        .slice(0, 7);
      adjacentes.forEach(function(e) {{
        var o = e.from === f.id ? e.to : e.from;
        if (!usados.has(o) && grupo.length < 8) {{ grupo.push(o); usados.add(o); }}
      }});
      try {{
        network.cluster({{
          joinCondition: function(n) {{ return grupo.indexOf(n.id) !== -1; }},
          edgesBetween: true,
          clusterNode: {{ shape: 'box', label: grupo.length.toString(),
            font: {{ size: 10, color: '#89b4fa' }}, color: {{ background: 'rgba(137,180,250,0.18)' } },
            borderWidth: 1, size: Math.max(8, Math.min(24, grupo.length))
          }}
        }});
      }} catch(e) {{ }}
    }}
  }}

  function _expandirTudo() {{
    var lst = network.getClusters ? network.getClusters() : [];
    try {{ lst = Object.keys(network.body.nodes).filter(function(id) {{
      return network.body.nodes[id].isCluster; }}); }} catch(e) {{ lst = []; }}
    if (!lst.length) return;
    lst.forEach(function(id) {{
      try {{ network.openCluster(id); }} catch(e) {{ }}
    }});
  }}

  network.on('zoom', function(params) {{
    _ajustarFontes();
    var scale = params.scale != null ? params.scale : network.getScale();
    if (params.direction === '-') {{
      // zoom-out: clustera para "ver o todo"
      if (!_clusterAtivo && scale < _lastClusterScale * _clusterFactor) {{
        _lastClusterScale = scale; _clusterAtivo = true; _fazerClusteres();
      }}
    }} else if (params.direction === '+') {{
      // zoom-in: expande para "ver o detalhe"
      if (_clusterAtivo && scale > _lastClusterScale * (1/_clusterFactor)) {{
        _lastClusterScale = scale; _clusterAtivo = false; _expandirTudo();
      }}
    }}
    if (!_clusterAtivo) _lastClusterScale = scale;
  }});

  // ajusta fontes na primeira interacao e a cada movimento de zoom
  setTimeout(_ajustarFontes, 1500);
  network.on('dragEnd', _ajustarFontes);

  // --- Movimento organico: "cerebro vivo" cognitivo ---
  // Heartbeat: respiracao suave dos nos + pulsos de sinapse aleatorios.
  let _tickPausado = false;
  let _ultimoSpike = 0;
  network.on('tick', () => {{
    if (_tickPausado) return;
    const agora = Date.now();
    const base = 0.86 + 0.14 * Math.sin(agora * 0.0015);
    // --- opacidade: leve, a cada tick (barata) ---
    const opUpd = [];
    nodes.get().forEach(n => {{ opUpd.push({{ id: n.id, opacity: base, shadow: true }}); }});
    nodes.update(opUpd);
    // --- tamanho/glow: pulsa so vezes em pouco (caro), ~3x/s, com fase unica
    if (!window.__pulseT || (agora - window.__pulseT) > 300) {{
      window.__pulseT = agora;
      const szUpd = [];
      nodes.get().forEach(n => {{
        const fase = typeof n.id === 'string'
          ? Array.from(n.id).reduce((a,b)=>(((a<<5)-a)+b.charCodeAt(0))|0, 0)
          : (n.id * 2654435761);
        const pulso = Math.sin(agora * 0.0012 + (fase % 97)) * 0.06;
        szUpd.push({{
          id: n.id,
          size: Math.max(6, (original[n.id] ? original[n.id].size : 12) * (1 + pulso * 0.4)),
          shadowSize: Math.round(16 + 4 * pulso)
        }});
      }});
      nodes.update(szUpd);
    }}
    // pulso cognitivo: a cada ~3.5-5s, acende ALEATORIAMENTE 1-3 arestas
    // (sinapses disparando em cascata), mantendo o resto sutil.
    let arestasUpd = [];
    edges.get().forEach(e => {{
      arestasUpd.push({{ id: e.id, color: arestaOriginal[e.id] ? arestaOriginal[e.id].color : '#999', width: arestaOriginal[e.id] ? arestaOriginal[e.id].width : 1, opacity: 0.25 }});
    }});
    if (agora - _ultimoSpike > _proxSpike()) {{
      _ultimoSpike = agora;
      const todas = edges.get();
      if (todas.length) {{
        const alvos = [];
        const qtd = 1 + Math.floor(Math.random() * 3);
        for (let i = 0; i < qtd && todas.length; i++) {{
          alvos.push(todas[Math.floor(Math.random() * todas.length)].id);
        }}
        arestasUpd = arestasUpd.map(a =>
          alvos.includes(a.id)
            ? {{ ...a, color: '#ffffff', width: 4.5, opacity: 0.9 }}
            : a);
        // leve glow no no destino de cada sinapse
        alvos.forEach(edgeId => {{
          const _ed = todas.find(x => x.id === edgeId);
          if (!_ed) return;
          const _dstOrig = original[_ed.to] || {{color:'#4e79a7', size:15}};
          nodes.update([{{ id: _ed.to, color: '#89b4fa', size: 22, shadow: true, shadowSize: 22 }}]);
          setTimeout(() => nodes.update([{{ id: _ed.to, color: _dstOrig.color, size: _dstOrig.size }}]), 700);
        }});
      }}
    }}
    edges.update(arestasUpd);
  }});
  // pausa o balanco organico ao pairar sobre um no
  network.on('hoverNode', () => {{ _tickPausado = true; }});
  network.on('blurNode', () => {{ _tickPausado = false; }});

  // Intervalo aleatorio entre pulsos de sinapse (3.2s a 5.5s)
  function _proxSpike() {{ return 3200 + Math.random() * 2300; }}

  // --- Cascata de sinapses quando o vault atualiza ---
  // O widget adiciona 'rc=<timestamp>' na URL ao detectar mudanca de versao.
  // Apos o reload, a presenca de 'rc' dispara uma onda de sinapses em cascata
  // para dar a sensacao de "cognicao viva no momento do aprendizado".
  (function() {{
    var rcParam = new URLSearchParams(window.location.search).get('rc');
    if (!rcParam) return;
    setTimeout(() => {{
      const todas = edges.get();
      if (!todas.length) return;
      // onda: acende ~10% das arestas em sequencia, uma a uma
      const qtd = Math.max(3, Math.floor(todas.length * 0.10));
      const seq = todas.slice().sort(() => Math.random() - 0.5).slice(0, qtd);
      seq.forEach((ed, i) => {{
        setTimeout(() => {{
          const up = edges.get().map(a => {{
            if (a.id === ed.id) return {{ id: a.id, color: '#ffffff', width: 5, opacity: 1 }};
            return a;
          }});
          edges.update(up);
          if (original[ed.to]) nodes.update([{{ id: ed.to, color: '#89b4fa', size: 26, shadow: true, shadowSize: 26 }}]);
          setTimeout(() => {{
            const rup = edges.get().map(a => {{
              if (a.id === ed.id) return {{ id: a.id, color: arestaOriginal[a.id].color, width: arestaOriginal[a.id].width, opacity: 0.25 }};
              return a;
            }});
            edges.update(rup);
            if (original[ed.to]) nodes.update([{{ id: ed.to, color: original[ed.to].color, size: original[ed.to].size }}]);
          }}, 550);
        }}, i * 90);
      }});
    }}, 600);
  }})();

  const original = {{}};
  nodes.get().forEach(n => {{
    original[n.id] = {{ color: n.color, size: n.size }};
  }});
  const arestaOriginal = {{}};
  edges.get().forEach(e => {{
    arestaOriginal[e.id] = {{ color: e.color || '#999', width: e.width || 1 }};
  }});

  function clarear(hex, fator) {{
    hex = hex.replace('#', '');
    const r = Math.min(255, Math.round(parseInt(hex.substring(0,2),16) * fator + 255 * (1 - fator)));
    const g = Math.min(255, Math.round(parseInt(hex.substring(2,4),16) * fator + 255 * (1 - fator)));
    const b = Math.min(255, Math.round(parseInt(hex.substring(4,6),16) * fator + 255 * (1 - fator)));
    return '#' + [r,g,b].map(x => x.toString(16).padStart(2,'0')).join('');
  }}

  function limpar() {{
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const atualizacoes = nodes.get().map(n => ({{
      id: n.id, color: original[n.id].color, size: original[n.id].size,
      opacity: 1, borderWidth: 0, borderWidthSelected: 0, shadow: false,
      font: {{ size: 11, color: '#cdd6f4', face: 'Segoe UI', bold: false }}
    }}));
    nodes.update(atualizacoes);
    const arestasUp = edges.get().map(e => ({{
      id: e.id, color: arestaOriginal[e.id].color, width: arestaOriginal[e.id].width, opacity: 1
    }}));
    edges.update(arestasUp);
    document.getElementById('painel').classList.remove('visivel');
    document.getElementById('painel').innerHTML = '';
  }}

  function telaInicial() {{
    limpar();
    if (viewInical && network.moveTo) {{
      // restaura as posicoes originais dos nos e a visao inicial
      const atualizacoes = Object.keys(posIniciais).map(id => ({{
        id, x: posIniciais[id].x, y: posIniciais[id].y, fixed: false
      }}));
      nodes.update(atualizacoes);
      network.moveTo({{
        position: viewInical,
        scale: scaleInical
      }});
    }} else {{
      network.fit({{ animation: true }});
    }}
  }}

  function focarVizinhanca(id, corGrupo) {{
    // vizinhanca direta: nos de 1 pulo
    const viz = new Set([id]);
    edges.get().forEach(e => {{
      if (e.from === id) viz.add(e.to);
      if (e.to === id) viz.add(e.from);
    }});

    const corNo = clarear(corGrupo, 0.42);
    const corViz = clarear(corGrupo, 0.25);

    // no central: maior, brilhante, glow forte
    // vizinhos: cor viva, borda, glow
    // resto: apagado
    const atualizacoes = [];
    nodes.get().forEach(n => {{
      if (n.id === id) {{
        atualizacoes.push({{
          id: n.id, color: corNo, borderColor: '#ffffff', borderWidth: 4, borderWidthSelected: 4,
          shadow: true, shadowColor: '#ffffff', shadowSize: 28,
          size: original[n.id].size + 16, font: {{ size: 16, color: '#ffffff', face: 'Segoe UI', bold: true }}
        }});
      }} else if (viz.has(n.id)) {{
        atualizacoes.push({{
          id: n.id, color: corViz, borderColor: corNo, borderWidth: 2, borderWidthSelected: 2,
          shadow: true, shadowColor: corViz, shadowSize: 16,
          size: original[n.id].size + 6
        }});
      }} else {{
        atualizacoes.push({{ id: n.id, color: '#10101a', size: 3, opacity: 0.05,
                            borderWidth: 0, borderWidthSelected: 0, shadow: false, font: {{ size: 6, color: '#293241' }} }});
      }}
    }});
    nodes.update(atualizacoes);

    // arestas da vizinhanca brilhantes; resto apagado
    const arestasUp = [];
    edges.get().forEach(e => {{
      const interno = viz.has(e.from) || viz.has(e.to);
      const central = (e.from === id) || (e.to === id);
      if (central) {{
        arestasUp.push({{ id: e.id, color: corNo, width: 4.5, opacity: 1 }});
      }} else if (interno) {{
        arestasUp.push({{ id: e.id, color: corViz, width: 2, opacity: 0.8 }});
      }} else {{
        arestasUp.push({{ id: e.id, color: '#2a2a3a', width: 0.3, opacity: 0.06 }});
      }}
    }});
    edges.update(arestasUp);

    // zoom preciso na vizinhanca
    network.fit({{
      nodes: Array.from(viz),
      animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }}
    }});
  }}

  function mostrarLista(grupo, corGrupo, titulo) {{
    const painel = document.getElementById('painel');
    const itens = nodes.get()
      .filter(n => grupo.has(n.id))
      .sort((a, b) => (a.label || '').localeCompare(b.label || ''));

    let html = `<h2><span class="dot" style="background:${{corGrupo}}"></span>${{titulo}}
      <span class="count">(${{itens.length}})</span></h2><ul>`;
    itens.forEach(n => {{
      const spec = (n.title || '').split('\\n')[0];
      html += `<li data-id="${{n.id}}"><div class="titulo">${{n.label}}</div>
               <div class="spec">${{spec}}</div></li>`;
    }});
    html += '</ul>';
    painel.innerHTML = html;
    painel.classList.add('visivel');

    // clique no item -> destaca o no + vizinhos e da zoom preciso
    painel.querySelectorAll('li').forEach(li => {{
      li.addEventListener('click', () => {{
        painel.querySelectorAll('li').forEach(x => x.classList.remove('sel'));
        li.classList.add('sel');
        focarVizinhanca(li.dataset.id, corGrupo);
      }});
    }});
  }}

  function destacar(filtro, valor, corGrupo) {{
    if (filtro === 'home') {{
      telaInicial();
      return;
    }}
    if (filtro === 'all') {{
      limpar();
      return;
    }}
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const alvo = document.querySelector(`.lg[data-filter="${{filtro}}"][data-value="${{valor}}"]`);
    if (alvo) alvo.classList.add('active');

    // conjunto de nos do grupo
    const grupo = new Set();
    nodes.get().forEach(n => {{
      if (filtro === 'cat' && n.cat === valor) grupo.add(n.id);
      else if (filtro === 'cl' && n.cl === valor) grupo.add(n.id);
      else if (filtro === 'st' && n.st === valor) grupo.add(n.id);
    }});

    const corViva = clarear(corGrupo, 0.35);

    // nos: dentro do grupo ficam vivos; fora ficam apagados
    const atualizacoes = [];
    nodes.get().forEach(n => {{
      if (grupo.has(n.id)) {{
        atualizacoes.push({{
          id: n.id,
          color: corViva,
          borderColor: '#ffffff',
          borderWidth: 3,
          borderWidthSelected: 3,
          shadow: true,
          shadowColor: corViva,
          shadowSize: 22,
          size: original[n.id].size + 8
        }});
      }} else {{
        atualizacoes.push({{ id: n.id, color: '#14141f', size: 3, opacity: 0.08,
                            borderWidth: 0, borderWidthSelected: 0, shadow: false }});
      }}
    }});
    nodes.update(atualizacoes);

    // arestas: entre nos do grupo = cor do grupo e grossas; do grupo p/ fora = finas; fora = apagadas
    const arestasUp = [];
    edges.get().forEach(e => {{
      const dentroDentro = grupo.has(e.from) && grupo.has(e.to);
      const dentroFora = grupo.has(e.from) !== grupo.has(e.to);
      if (dentroDentro) {{
        arestasUp.push({{ id: e.id, color: corViva, width: 3.5, opacity: 0.95 }});
      }} else if (dentroFora) {{
        arestasUp.push({{ id: e.id, color: '#888', width: 0.6, opacity: 0.35 }});
      }} else {{
        arestasUp.push({{ id: e.id, color: '#3a3a4a', width: 0.3, opacity: 0.10 }});
      }}
    }});
    edges.update(arestasUp);
    network.fit({{ animation: true }});

    // lista dos itens do grupo
    const nome = alvo ? alvo.textContent.trim() : valor;
    mostrarLista(grupo, corGrupo, nome, corGrupo);
  }}

  document.querySelectorAll('.lg').forEach(btn => {{
    btn.addEventListener('click', () => destacar(btn.dataset.filter, btn.dataset.value, btn.dataset.color));
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
