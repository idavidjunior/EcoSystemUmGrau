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

# ---------------------------------------------------------------------------
# Pontes inter-cluster (Cerebro Vivo) ---------------------------------------
# O grafo, por construcao, so cria arestas por tag/fonte/hub — o que deixa os
# clusters isolados (0 arestas entre clusters). Estas arestas curadas conectam
# nos de clusters DIFERENTES que compartilham semantica real, transformando o
# grafo em um cerebro integrado. Cada ponte e (fragA, fragB): substrings que
# devem casar exatamente UM no cada — se ambiguas ou ausentes, a ponte e
# ignorada com aviso (nunca impede a geracao). O prefixo '-encoding UTF-8' e
# escrito com aspas para evitar falsa quebra de linha.
# ---------------------------------------------------------------------------

BRIDGES_CLUSTERS = [
    # Android <-> cognicao: snapshot imutavel
    ('Framework de Persistencia com Snapshot Imutavel',
     'Salvar cria novo arquivo timestampado'),
    # Ler <-> general: escrita atomica (persistencia JSON)
    ('Escrita atomica sempre', 'Estado persiste em JSON'),
    ('Escrita atomica sempre', 'Crash no meio do json'),
    # Cognicao <-> Mp3player: scoring / fallback multi-fonte
    ('Modelo de scoring para busca multi-resultado',
     'iTunes search with scoring thresholds'),
    ('Estrategia de fallback em cadeia',
     'Metadata busca em multi-fontes: AcoustID'),
    # Cognicao <-> Ecossistema: aprendizado continuo / failover
    ('Framework de Aprendizado Continuo', 'captura de conhecimento do ecossistema'),
    ('Estrategia de fallback em cadeia', 'failover inteligente'),
    # Ecossistema <-> Navegacao: seguranca de chaves / protocolo MCP
    ('Chaves API exclusivamente em env vars',
     'Nunca armazenar API keys em config files'),
    ('MCP tool naming', 'MCP server handshake obrigatorio'),
    ('MCP JSON-RPC notification handling', 'MCP server handshake obrigatorio'),
    # Ler <-> Android: encoding UTF-8 no Windows
    ('Encoding UTF-8 explicito em Python no Windows',
     'in javac'),
    # Ecossistema <-> Ler: separacao causa-efeito-temporal
    ('Principio da separacao causa-efeito-temporal',
     'deactivates on song change'),
    # Ecossistema <-> Ler: escrita atomica em bug real
    ('Escrita atomica sempre', 'json.dump corrompia arquivo'),
    # Cognicao <-> Navegacao: espera adaptativa / fallback em cascata
    ('Espera adaptativa por tipo de recurso', 'Velocidade = evitar esperas fixas'),
    ('Estrategia de fallback em cadeia', 'Cascata de Interacao'),
    ('Heuristica de isolamento de falha', 'Retry com backoff exponencial'),
    ('Ciclo OODA aplicado a navegacao', 'OODA-Nav'),
    # Navegacao <-> Android: automatizacao de UI no dispositivo
    ('Android View hierarchy scanning', 'ListView + BaseAdapter Pattern'),
    ('Package/activity launch pattern', 'ADB Workflow'),
    ('Sempre fechar teclado virtual Android', 'Vibration Pattern'),
    # Android <-> Cognicao: persistencia
    ('JSON Persistence Pattern', 'Padrao de escrita atomica para persistencia'),
    ('Checkpoints salvos antes de cada iteracao',
     'Framework de Persistencia com Snapshot Imutavel'),
    # Ecossistema <-> Cognicao: failover em cadeia
    ('Server failover com auto-return', 'Arvore de Decisao para Fallback de Servico'),
]


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
_PLACEHOLDER_FIX = {'', '---', '-----', '-------', '-----------', '-'}


def eh_lixo_issue(text):
    """Issue sem conteudo real (so hifens)."""
    t = (text or '').strip()
    if not t:
        return True
    return all(c in ' -\n\t\r' for c in t)


def bug_status(b):
    """Deriva o status do bug a partir dos campos fix/root_cause."""
    issue = (b.get('issue') or '').strip()
    fix = (b.get('fix') or '').strip()
    rc = (b.get('root_cause') or '').strip()
    low = ' '.join((issue + ' ' + fix + ' ' + rc)).lower()

    # Limitacao conhecida: sem correcao real e sintomas de limitacao aceita
    if fix in _PLACEHOLDER_FIX:
        if any(k in low for k in ('nao-critica', 'non-critic',
                                  'accepted', 'always', 'sempre falha', 'workaround',
                                  'known', 'key invalida', 'api key invalida')):
            return 'conhecido'
        # Track best score / explicit redirect sao registros de "como fazer melhor",
        # sem ser um bug ativo: marcar como conhecido/pendente
        if 'track the best' in low or 'redirect' in low:
            return 'pendente'
        return 'pendente'

    # Ha uma correcao descrita.
    if any(k in fix.lower() for k in ('nao-critica', 'non-critic',
                                      'accepted', 'workaround')):
        return 'conhecido'
    return 'resolvido'


def make_id(prefix, text):
    slug = slugify(text)
    if not slug:
        return None
    return f'{prefix}-{slug}'


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
        cl = cluster or (_SOURCE_CLUSTER.get(source, 'geral') if source else 'geral')
        # Se source nao esta no CLUSTERS, tenta cluster_of(source)
        if not cl or cl == 'geral':
            cl = cluster_of(source) if source else 'geral'
        n = {'id': nid, 'label': label, 'categoria': categoria,
             'tags': tags or [], 'title': title, 'cl': cl, 'grau': 0,
             'source': source}
        nos.append(n)
        nos_por_id[nid] = n

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
            n['status'] = status

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
    physics: {{ barnesHut: {{ gravitationalConstant:-3000, springLength:120, springConstant:0.04, damping:0.09 }},
               stabilization: {{ iterations:300 }} }},
    interaction: {{ hover:true, tooltipDelay:120, navigationButtons:true }}
  }};
  const network = new vis.Network(container, {{ nodes, edges }}, options);

  // Posicao/zoom/cam posicao inicial capturados quando a fisica estabilizar
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
      // Congela a fisica: o layout padrao fica fixo para sempre,
      // entao Home restaura cores + camera sem os nos se moverem.
      network.setOptions({{ physics: {{ enabled: false }} }});
    }}
  }};
  network.once('stabilized', () => setTimeout(guardaInicial, 400));
  setTimeout(guardaInicial, 2500);

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
