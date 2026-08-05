"""Gera um grafo interativo HTML (vis-network) do conhecimento do ecossistema.

Le o vault Obsidian (conhecimento/notas/*.md) e produz um arquivo HTML
standalone (vis-network via CDN) que abre em qualquer navegador. O vault e a
fonte viva: notas + links [[wikilinks]] (incluindo os criados pelo Smart
Connections no Obsidian). Assim o grafico reflete exatamente o que esta no
Obsidian â€” sinapses semanticas incluidas.

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
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(str(Path(__file__).resolve().parent), 'scripts'))
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
# Descricoes curtas para os tooltips dos botoes de categoria
CATEGORIA_DESC = {
    'padroes': 'Padroes e convencoes reutilizaveis do ecossistema',
    'decisoes': 'Decisoes arquiteturais e de projeto ja tomadas (ADRs)',
    'bugs': 'Bugs e limitacoes conhecidas, com status de resolucao',
    'cognitivo': 'Meta-cognicao, estrategias de raciocinio e debugging',
    'heuristicas': 'Heuristicas praticas e atalhos mentais validados',
    'frameworks': 'Frameworks, bibliotecas e ferramentas adotadas',
    'missoes': 'Missoes e objetivos em andamento do ecossistema',
    'hub': 'No central que agrupa e conecta um conjunto de notas',
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
# Descricoes curtas para os tooltips dos botoes de cluster
CLUSTER_DESC = {
    'android': 'Notas do projeto Android (SDK puro) e seu build',
    'mp3player': 'Notas do projeto MP3 Player e resgate de metadados',
    'ler': 'Notas do LER (runtime e agentes de execucao)',
    'navegacao': 'Notas de treinamento de navegacao e sessoes',
    'ecossistema': 'Notas do proprio EcoSystemUmGrau (config, MCP, agentes)',
    'cognicao': 'Notas de meta-cognicao e raciocinio',
    'geral': 'Notas sem cluster especifico ou de escopo geral',
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
STATUS_DESC = {
    'resolvido': 'Bug ja corrigido e validado',
    'pendente': 'Bug ainda aberto, aguardando correcao',
    'conhecido': 'Limitacao aceita e documentada, sem correcao prevista',
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
    'fonte', 'status', 'projeto', 'sdk', 'app', 'grafo', 'widget',
})


def _norm_fonte(s):
    """Normaliza uma fonte/tag para comparacao: minusculas, sem pontuacao."""
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def _dedupe_fonte(norm):
    """Se a string normalizada e uma repeticacao de si mesma (ex: 'xx' = 'x'*2,
    'androidpuresdkandroidpuresdk'), reduz para a forma simples. O RAKE e o
    slugify as vezes concatenam a mesma tag duas vezes no frontmatter."""
    n = len(norm)
    for k in range(1, n // 2 + 1):
        if n % k == 0 and norm == norm[:k] * (n // k):
            return norm[:k]
    return norm


def _resolver_cluster(tags, fonte='', mapper=None, categoria='', slug=''):
    """Resolve o cluster a partir das tags/fonte da nota, tolerando:
    - fontes com underscore que o slugify colapsou (ler_auditoria -> lerauditoria)
    - tags duplicadas concatenadas (android-pure-sdkandroid-pure-sdk)
    - variantes sem separador (treinamentonavegacao, androidpuresdk)
    Usa o ClusterMapper quando disponível (aprendizado + ousadia);
    senão, faz o match exato/substring com o mapeamento estático.
    Retorna o cluster ou 'geral'."""
    if mapper is not None:
        return mapper.resolver(tags, fonte, categoria, slug)
    for t in tags:
        if not t:
            continue
        t_clean = t
        if isinstance(t, str):
            t_clean = t.strip()
        if not t_clean or t_clean.lower() in _GENERIC_TAGS:
            continue
        n = _dedupe_fonte(_norm_fonte(t_clean))
        if not n:
            continue
        for cl, fontes in CLUSTERS.items():
            for f in fontes:
                if _norm_fonte(f) == n:
                    return cl
        for cl, fontes in CLUSTERS.items():
            for f in fontes:
                nf = _norm_fonte(f)
                if len(nf) >= 4 and nf in n:
                    return cl
    if categoria in ('cognitivo', 'heuristicas'):
        return 'cognicao'
    return 'geral'


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
    """ConstrÃ³i nÃ³s e arestas a partir do vault Obsidian vivo.

    Cada .md vira um nÃ³; cada [[wikilink]] vira uma aresta.
    Isso capta automaticamente conexÃµes criadas pelo Smart Connections.
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
        cl = cluster or 'geral'
        n = {'id': nid, 'label': label, 'categoria': categoria,
             'tags': tags or [], 'title': title, 'cl': cl, 'grau': 0,
             'source': source}
        nos.append(n)
        nos_por_id[nid] = n
        return n

    # ---- ler TODAS as notas do vault (incl. _hubs) ----
    md_files = sorted(Path(VAULT_DIR).rglob('*.md'))
    no_cache = {}  # slug -> set of wikilinks (guardado antes de add_no perder body)

    # ---- TREINO do ClusterMapper ----
    # Coleta os metadados de todas as notas ANTES de montar o grafo e aprende
    # as associações tag->cluster. Isso permite "ousar": resolver variantes que
    # não casam com o mapeamento estático (slug colapsado, tags duplicadas).
    # O aprendizado resultante é persistido como memória (JSON) para inspeção
    # e reuso em outras etapas (ex: gerador de notas).
    try:
        from cluster_mapper import ClusterMapper
        _mapper = ClusterMapper()
    except ImportError:
        _mapper = None
    _memoria_aprendizado = os.path.join(BASE, 'conhecimento', 'aprendizados', 'cluster_mapper.json')
    _dados_treino = []
    for f in md_files:
        rel = f.relative_to(VAULT_DIR)
        _is_hub = rel.parts[0] == '_hubs'
        _slug = f.stem
        _content = f.read_text(encoding='utf-8')
        _fm, _body = _parse_frontmatter(_content)
        _tags = _fm.get('tags', [])
        if isinstance(_tags, str):
            _tags = [_tags]
        _cat = 'hub' if _is_hub else rel.parts[0]
        _dados_treino.append({
            'tags': _tags,
            'fonte': _source_from_tags(_tags) if not _is_hub else _slug,
            'slug': _slug,
            'categoria': _cat,
            'cl_bruto': '',
        })
    if _mapper is not None:
        _mapper.treinar(_dados_treino)
        try:
            os.makedirs(os.path.dirname(_memoria_aprendizado), exist_ok=True)
            with open(_memoria_aprendizado, 'w', encoding='utf-8') as _fmemo:
                json.dump(_mapper.exportar_aprendizado(), _fmemo, ensure_ascii=False, indent=1)
        except Exception:
            pass

    # Atividade real por nota: mtime do arquivo (ultima edicao). Notas tocadas
    # recentemente = "quentes"; antigas e nunca editadas = "frias". Isso torna
    # o tamanho do no um termometro do uso real do vault, nao so do grau.
    agora_ts = time.time()
    mtime_por_id = {}
    for f in md_files:
        try:
            mtime_por_id[f.stem] = os.path.getmtime(f)
        except OSError:
            mtime_por_id[f.stem] = 0

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
        # Resolve o cluster com o ClusterMapper (aprendizado + ousadia).
        # Hubs de cluster (cluster-hub-X) mapeiam direto pelo nome.
        if is_hub and 'cluster-hub-' in slug:
            cluster = slug.replace('cluster-hub-', '').strip()
        else:
            cluster = _resolver_cluster(tags, source, _mapper, categoria, slug)

        # label = aliases[0] ou heading
        label = aliases[0] if aliases else slug
        h_match = re.search(r'^# (.+)$', body, re.MULTILINE)
        if h_match:
            label = h_match.group(1).strip()

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

        # Atividade real: mapa mtime -> 0..1 (decai exponencialmente e por janela
        # de dias). Notas editadas hoje = ~1; mais de ~90 dias sem toque = ~0.
        try:
            mt = mtime_por_id.get(slug, 0)
            if mt:
                dias = max(0, (agora_ts - mt) / 86400.0)
                atv = max(0.0, min(1.0, 1.0 - (dias / 90.0)))
                atv = max(atv, 0.12)  # nunca some totalmente
            else:
                atv = 0.5
            nos_por_id[slug]['atv'] = atv
        except Exception:
            nos_por_id[slug]['atv'] = 0.5

        # armazenar wikilinks desta nota (antes de possivelmente ser usado)
        links = _extract_wikilinks(body)
        no_cache[slug] = links

    # ---- construir arestas a partir dos wikilinks reais ----
    id_set = set(nos_por_id)
    for slug, links in no_cache.items():
        for link in links:
            # link pode ser 'nota-slug' ou 'nota-slug|alias' â€” pega so o slug
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
        # Tamanho por USO REAL: o no e "termometro" do vault. Tamanho base vem
        # do grau; a ATIVIDADE (mtime recente) adiciona ate +10 e evita o no
        # diminuir demais quando e central mas este sem edicao recente.
        atv = n.get('atv', 0.5)
        use_size = int(size * (0.75 + 0.5 * atv))
        size = max(size, use_size)
        if n['categoria'] == 'hub':
            size = max(size, 30)
        label = n['label']
        if n['categoria'] == 'bugs':
            st = n.get('status', 'pendente')
            label = f"{'âœ”' if st == 'resolvido' else ('â€ ' if st == 'conhecido' else 'âœ–')} {label}"
        node_obj = {
            'id': n['id'],
            'label': label,
            'color': cor,
            'size': size,
            'title': titles[n['id']] or n['label'],
            'cat': n['categoria'],
            'cl': n['cl'],
            'atv': round(n.get('atv', 0.5), 3),
            'tags': n.get('tags', []),
        }
        if n['categoria'] == 'bugs':
            node_obj['st'] = n.get('status', 'resolvido')
        # Tooltip organizado: cabecalho com contexto + resumo do corpo.
        # O vis-network renderiza o tooltip em texto simples; usamos quebras
        # de linha para um bloco legivel, nao HTML.
        cab = []
        cab.append(f'# {n["label"]}')
        cat_label = CATEGORIA_LABEL.get(n['categoria'], n['categoria'])
        cab.append(f'Categoria: {cat_label}')
        cl_label = CLUSTER_DESC.get(n['cl'], n['cl'].capitalize())
        cab.append(f'Cluster: {cl_label}')
        if n.get('status'):
            cab.append(f'Status: {STATUS_DESC.get(n["status"], n["status"])}')
        if n.get('tags'):
            cab.append('Tags: ' + ', '.join(str(t) for t in n['tags'][:8]))
        resumo = ' '.join(str(titles[n['id']] or n['label']).split())
        tooltip = '\n'.join(cab) + '\n---\n' + resumo[:400]
        node_obj['title'] = tooltip
        nodes_js.append(json.dumps(node_obj, ensure_ascii=False))

    edges_js = [json.dumps({'from': a, 'to': b, 'color': '#999', 'width': 1}, ensure_ascii=False)
                for a, b in sorted(arestas)]

    legend_cat = ''.join(
        f'<button class="lg" data-filter="cat" data-value="{c}" data-color="{CATEGORIA_COR.get(c,"#888")}" '
        f'title="Categoria: {CATEGORIA_DESC.get(c, c)}. Clique para destacar as notas desta categoria.">'
        f'<span class="dot" style="background:{CATEGORIA_COR.get(c,"#888")}"></span>{CATEGORIA_LABEL.get(c,c)}</button>'
        for c in CATEGORIA_COR)
    legend_cl = ''.join(
        f'<button class="lg" data-filter="cl" data-value="{cl}" data-color="{cor}" '
        f'title="Cluster: {CLUSTER_DESC.get(cl, cl)}. Clique para destacar as notas deste cluster.">'
        f'<span class="dot" style="background:{cor}"></span>{cl.capitalize()}</button>'
        for cl, cor in CLUSTER_COR.items())
    legend_st = ''.join(
        f'<button class="lg" data-filter="st" data-value="{st}" data-color="{cor}" '
        f'title="Status: {STATUS_DESC.get(st, st)}. Clique para destacar bugs com este status.">'
        f'<span class="dot" style="background:{cor}"></span>Bug: {label}</button>'
        for st, label in STATUS_LABEL.items())
    legend_st = '<span style="opacity:.6">|</span> ' + legend_st

    # Botoes de dominio: MCPs (notas com tag mcp) vs Conhecimento (restante).
    # Filtro por tag: qualquer tag que contenha 'mcp' classifica a nota.
    legend_dom = (
        '<span style="opacity:.6">|</span> '
        '<button class="lg" data-filter="dom" data-value="mcp" data-color="#cba6f7" '
        'title="Dominio: destaca as notas cujas tags citam MCP (servidores, config, skills).">'
        '<span class="dot" style="background:#cba6f7"></span>MCPs</button>'
        '<button class="lg" data-filter="dom" data-value="conhecimento" data-color="#a6e3a1" '
        'title="Dominio: destaca as notas que NAO sao de MCP (conhecimento geral do ecossistema).">'
        '<span class="dot" style="background:#a6e3a1"></span>Conhecimento</button>'
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Cerebro Vivo â€” Grafo do Conhecimento</title>
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

  /* Tooltip do vis-network: organizado, legivel e responsivo */
  .vis-tooltip {{
    position: absolute;
    max-width: min(420px, 85vw);
    max-height: 70vh;
    overflow-y: auto;
    background: rgba(24,24,37,0.96);
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 10px 12px;
    color: #cdd6f4;
    font-size: 12px;
    line-height: 1.45;
    white-space: pre-line;
    box-shadow: 0 4px 18px rgba(0,0,0,0.6);
    z-index: 10000;
  }}
  /* Tooltip dos botoes da legenda: estilo nativo (title) ja e suficiente;
     este bloco apenas garante que a legenda nao estoure em telas pequenas. */
  @media (max-width: 720px) {{
    #header {{ padding:8px 10px; }}
    #legend {{ gap:4px; font-size:10px; }}
    .lg {{ padding:2px 6px; font-size:10px; }}
    #net {{ height:calc(100vh - 80px); }}
    #painel {{ width:260px; }}
  }}
  /* Tooltip nativo (title) dos botoes: garante quebre de linha adequada */
  .lg[title]:hover {{
    position: relative;
    z-index: 9998;
  }}
</style>
<script src="vendor/vis-network.min.js"></script>
</head>
<body>
<div id="header">
  <h1>Cerebro Vivo â€” Grafo do Conhecimento</h1>
  <div id="legend">
    {legend_cat}
    {legend_cl}
    {legend_st}
    {legend_dom}
    <button class="lg home" data-filter="home" data-value="" data-color="#89b4fa"
      title="Home: restaura a visao inicial do grafo (posicao e zoom originais).">ðŸ  Home</button>
    <button class="lg" data-filter="all" data-value="" data-color="#888"
      title="Limpar: remove o destaque atual e restaura as cores e tamanhos originais dos nos.">âœ• Limpar</button>
  </div>
  <div id="stats" title="Resumo do grafo. Passe o mouse sobre os botoes acima para ver a explicacao de cada um.">{len(nos)} nos | {len(arestas)} conexoes â€” clique em uma categoria ou cluster para destacar</div>
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
    nodes: {{ shape:'dot', font:{{ size:0, color:'#cdd6f4' }} }},
    edges: {{ smooth:{{ type:'continuous' }} }},
    // Movimento organico: SEM estabilizacao, timestep lento, velocidade
    // limitada -> a rede nunca "congela", respira em movimento perpetuo.
    physics: {{
      enabled: true,
      solver: 'barnesHut',
      barnesHut: {{
        theta: 0.5,
        gravitationalConstant: -720,
        centralGravity: 0.30,
        springLength: 120,
        springConstant: 0.045,
        damping: 0.82,
        avoidOverlap: 0.55
      }},
      minVelocity: 0,
      maxVelocity: 13,
      timestep: 0.32,
      adaptiveTimestep: false,
      stabilization: false
    }},
    interaction: {{ hover:true, tooltipDelay:120, navigationButtons:true, zoomSpeed:0.35, smoothWheel:true }}
  }};
  const network = new vis.Network(container, {{ nodes, edges }}, options);

  // Enquadra o grafo e liberta a fisica para o balanco organico perpetuo.
  setTimeout(() => network.fit({{ animation: true }}), 1200);

  // =====================================================================
  // PSEUDO-3D â€” PROFUNDIDADE VIVA (sem WebGL)
  // Simulamos um eixo Z dentro do motor 2D do vis-network. Cada no recebe
  // uma profundidade inicial (hubs na FRENTE, folhas ao fundo) com um
  // jitter estavel, e DEPOIS "flutua" em z ao longo do tempo (onda lenta
  // por no, autonoma). O tamanho, a opacidade e o brilho do glow refletem
  // z: perto = grande/opaco/brilhante; longe = pequeno/translucido/apagado.
  // Resultado: uma "esfera de conhecimento" com relevo que respira na
  // profundidade. Nao usa dependencia WebGL e nao toca na fisica/clusters.
  // =====================================================================
  function _hashId(id) {{
    if (typeof id === 'number') return Math.abs(id * 2654435761) % 2147483647;
    var s = String(id), h = 0;
    for (var i = 0; i < s.length; i++) h = ((h << 5) - h) + s.charCodeAt(i);
    return Math.abs(h);
  }}
  function _zInicial(n) {{
    // base pela "centralidade" (size e proporcional ao grau): frente -> perto
    var base = 0.25 + 0.6 * Math.min(1, (n.size || 10) / 40);
    if (n.cat === 'hub') base = 0.92;          // hubs sempre na frente
    base += ((_hashId(n.id) % 100) / 100) * 0.22 - 0.11; // jitter estavel
    return Math.max(0.04, Math.min(1, base));
  }}
  var _zBase = {{}};
  var _zFase = {{}};
  nodes.get().forEach(function(n) {{
    _zBase[n.id] = _zInicial(n);
    _zFase[n.id] = (_hashId(n.id) % 628) / 100; // fase unica da onda
  }});
  // Profundidade efetiva num instante t: base + deriva viva + ONDA VIAJANTE.
  // A deriva (duas senoides por no) mantem cada no respirando no seu ritmo.
  // A ONDA VIAJANTE usa o angulo do no em torno do centro para criar um "giro
  // de profundidade": num lado os nos emergem (virao a frente), no outro
  // submergem (virao a tras) -> a malha gira como um globo, mais natural que
  // girar o quadro 2D. Mantem-se 0..1.
  function _zVivo(id, t) {{
    var z0 = _zBase[id] != null ? _zBase[id] : 0.5;
    var f = _zFase[id] != null ? _zFase[id] : 0;
    // respiracao organica propria de cada no
    var onda = Math.sin(t * 0.0011 * _velGlobal + f) + Math.sin(t * 0.00066 * _velGlobal + f * 2.3);
    // angulo/raio do no em torno do centro (via cache de posicoes) -> giro 3D
    var ang = f, raio = 0.5, c = _cacheCentro || {{ x: 0, y: 0 }};
    var p = _cachePos ? _cachePos[id] : null;
    if (p) {{
      ang = Math.atan2(p.y - c.y, p.x - c.x);
      raio = Math.min(1, Math.sqrt((p.x - c.x) * (p.x - c.x) + (p.y - c.y) * (p.y - c.y)) / 380);
    }}
    // onda gira em torno do centro: lado 0 sempre na "frente" por fase
    var viajante = Math.sin(t * 0.00050 * _waveVel * _velGlobal + ang + raio * 3.0) * 0.26 * _waveDir;
    var z = z0 + 0.20 * onda * 0.5 + viajante;
    return Math.max(0.04, Math.min(1, z));
  }}

  // Ajusta a velocidade global do movimento (ondas, pulsos e fisica).
  // Chamada pelo painel de controles do widget; v=1 eh o padrao.
  function _aplicarVelocidade(v) {{
    v = Number(v) || 1;
    _velGlobal = v;
    try {{
      network.setOptions({{ physics: {{ barnesHut: {{
        gravitationalConstant: -720 * Math.sqrt(v),
        springConstant: 0.045 * Math.sqrt(v),
        damping: Math.max(0.45, 0.82 / Math.sqrt(v)),
        centralGravity: 0.30 * Math.sqrt(v)
      }}, maxVelocity: 13 * v, timestep: 0.32 * Math.sqrt(v) }} }});
    }} catch(e) {{}}
  }}

  // =====================================================================
  // ROTACAO VIVA (sem WebGL) â€” a malha gira como um globo de conhecimento
  // Em vez de girar o canvas (artificial: o quadro inteiro vira como folha),
  // movemos a PROFUNDIDADE como uma ONDA VIAJANTE que rodeia o centro.
  // Cada no orbita em sua propria "camada"; com o tempo a profundidade sobe
  // num lado e desce no outro -> os nos da frente e de tras trocam de lugar
  // suavemente, lendo como uma esfera girando no espaco, nao um spin rigido.
  // O sentido e a velocidade da onda mudam aleatoriamente para nunca repetir.
  // As posicoes sao cacheadas a cada ~600ms (barato) para orientar a onda.
  // =====================================================================
  var _waveDir = 1;
  var _waveVel = 1;
  var _velGlobal = 1; // multiplicador de velocidade ajustado pelo usuario
  var _cachePos = {{}};
  var _cacheCentro = {{ x: 0, y: 0 }};
  (function() {{
    _waveDir = Math.random() < 0.5 ? 1 : -1;
    _waveVel = 0.6 + Math.random() * 0.9;
    var recomeca = function() {{
      _waveDir = Math.random() < 0.5 ? 1 : -1;
      _waveVel = 0.6 + Math.random() * 1.1;
      setTimeout(recomeca, 5000 + Math.random() * 5000);
    }};
    setTimeout(recomeca, 4000 + Math.random() * 4000);
    var atualizaCentro = function() {{
      try {{
        _cachePos = network.getPositions();
        // Referencia de movimento = CENTRO DO QUADRO visivel (viewport), nao o
        // centroide dos nos. Assim a onda/giro 3D orbita o meio do canvas
        // mesmo que o usuario de pan/zoom.
        if (network.getViewPosition) {{
          _cacheCentro = network.getViewPosition();
        }} else {{
          var k = 0, sx = 0, sy = 0;
          for (var id in _cachePos) {{ sx += _cachePos[id].x; sy += _cachePos[id].y; k++; }}
          if (k) {{ _cacheCentro = {{ x: sx / k, y: sy / k }}; }}
        }}
      }} catch (e) {{}}
    }};
    atualizaCentro();
    setInterval(atualizaCentro, 600);
  }})();

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
        gravitationalConstant: -720, springLength: 120, springConstant: 0.030,
        damping: 0.86, centralGravity: 0.34, avoidOverlap: 0.55
      }} }} }});
    }}
  }};
  setTimeout(guardaInicial, 2500);

  // --- Respiracao do layout ------------------------------------------------
  // Ciclo organico que alterna a energia da fisica: "inspira" (mais repulsao,
  // espaca) e "expira" (mais coesao, aproxima) sem nunca parar. As variacoes
  // sao mais fortes que antes para o movimento ficar perceptivel.
  let _respirando = 1;
  setInterval(() => {{
    _respirando = 0.72 + 0.28 * Math.sin(Date.now() * 0.00045);
    network.setOptions({{ physics: {{ barnesHut: {{
      gravitationalConstant: -720 * _respirando,
      centralGravity: 0.34 * (1.5 - _respirando),
      springConstant: 0.030 * (1.8 - _respirando)
    }} }} }});
  }}, 2500);

  // =========================================================================
  // ZOOM-MICROSCOPIO + EXPANDIR
  // O zoom ganha papel narrativo: recuar para ver o todo ("microscopio de
  // visao ampla") e avancar para ver o detalhe ("microscopio focalizado").
  // =========================================================================
  // =========================================================================
  // MOTOR DE CRITICALIDADE AUTO-ORGANIZADA + AVALANCHES NEURAIS (Beggs & Plenz)
  // O cerebro digital opera no ponto critico (ordem <-> caos): cada no e um
  // neuronio com potencial de membrana que acumula input das sinapses vizinhas
  // (excitacao/inibicao BALANCEADAS). Ao cruzar o limiar, DISPARA: produz um
  // pulso de glow e envia energia as sinapses vizinhas (RAMIFICACAO).
  // O parametro de ramificacao sigma ~1 (critico) produz avalanches power-law:
  // pequenos disparos frequentes + ocasionais cascatas enormes que varrem a
  // rede = transmissao otima de informacao, identica a um cerebro real.
  // =========================================================================
  let _memb = {{}};
  let _refrat = {{}};
  let _sigma = 0.96 + Math.random() * 0.05;   // critico: 0.9x..1.0x
  let _solo = 0.010;                            // "chao" de excitacao espontanea
  let _avalanche = {{ ativo: false, fila: [], maior: 0, size: 0 }};
  const _LIMIAR = 1.0;
  const _REF = 240;                             // fase refrataria (ms)

  // homeostase do ponto critico: sigma e o solo espontaneo variam lentamente
  function _reacerca() {{
    _sigma = 0.88 + Math.random() * 0.12;
    _solo = 0.007 + Math.random() * 0.006;
    setTimeout(_reacerca, 5000 + Math.random() * 6000);
  }}
  setTimeout(_reacerca, 5000);

  // inicializa os potenciais de membrana criados
  nodes.get().forEach(function(n) {{
    if (_memb[n.id] == null) _memb[n.id] = Math.random() * _LIMIAR * 0.7;
  }});

  var _lastClusterScale = 1;
  var _clusterFactor = 0.55;
  var _clusterAtivo = false;

  // --- MICROSCOPIO ---
  // Mantem as etiquetas legiveis ao ampliar: o canvas do vis-network sobe a
  // escala do node, mas a fonte cresce junto (torna ilegivel). Compensamos
  // com font.size = base / scale (fonte volta ao tamanho "real" na tela).
  // Quando as etiquetas estiverem ocultas pelo usuario, mantemos 0.
  function _ajustarFontes() {{
    // Padrao: etiquetas DESATIVADAS. Oculto = localStorage nao e 'false'
    // (ausente/'true' = oculto; apenas 'false' explicito = mostrar).
    var oculto = (typeof localStorage !== 'undefined' &&
                  localStorage.getItem('labelsOcultos') !== 'false');
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
            font: {{ size: 10, color: '#89b4fa' }},
            color: {{ background: 'rgba(137,180,250,0.18)' }},
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

  // --- REORGANIZACAO SUAVE AO ARRASTAR --------------------------------------
  // Ao soltar um no, os vizinhos recebem um leve "empurrao" (perturbacao na
  // fisica) e a rede se reorganiza em cascata suave — a sensacao de que as
  // forcas fluem do ponto arrastado. O pulso e breve e nao desmancha o layout.
  network.on('dragStart', function() {{ _tickPausado = true; }});
  network.on('dragEnd', function(params) {{
    _tickPausado = false;
    _ajustarFontes();
    if (!params || !params.nodes || !params.nodes.length) return;
    const movido = params.nodes[0];
    // disturbo na fisica local: graus de liberdade extras nos vizinhos
    try {{
      const viz = network.getConnectedNodes(movido);
      const agora = Date.now();
      viz.forEach((vid, i) => {{
        const pulso = Math.sin(agora * 0.02 + i * 0.7) * 0.25 + 0.75;
        network.physics ? network.physics.physicsBody : null;
        nodes.update([{{
          id: vid,
          x: (nodes.get(vid).x || 0) + Math.sin(i) * pulso * 3,
          y: (nodes.get(vid).y || 0) + Math.cos(i) * pulso * 3
        }}]);
      }});
    }} catch (e) {{}}
    // breve aceleracao da fisica para a cascata se dissipar organicamente
    try {{
      network.setOptions({{ physics: {{ barnesHut: {{
        gravitationalConstant: -760, springConstant: 0.050, damping: 0.78
      }} }} }});
      setTimeout(() => {{
        network.setOptions({{ physics: {{ barnesHut: {{
          gravitationalConstant: -720 * _respirando,
          springConstant: 0.030 * (1.8 - _respirando),
          damping: 0.82
        }} }} }});
      }}, 450);
    }} catch (e) {{}}
  }});

  // --- Movimento organico: "cerebro vivo" cognitivo ---
  // Heartbeat: respiracao suave dos nos + pulsos de sinapse aleatorios.
  // A profundidade VIVA (pseudo-3D) modula tamanho/opacidade/glow de cada no,
  // dando a ilusao de relevo e profundidade sem precisar de WebGL.
  let _tickPausado = false;
  let _destacado = false;
  let _ultimoSpike = 0;
  // --- ROTACAO ORBITAL REAL (flutuar com forcas fisicas) --------------------
  // Alem da profundidade (pseudo-3D), os nos ganham uma DERIVA ORBITAL suave:
  // cada no orbita o centro do quadro numa elipse lenta, com raio, excentricidade
  // e velocidade proprios (estaveis por id). A superposicao de orbitas quase
  // periodicas produz o "agito" organico de um grafo force-directed vivo — as
  // posicoes parecem flutuar, e arrastar um no puxa a orbita ao redor.
  // As forcas do vis-network (barnesHut) continuam dominando; a deriva e uma
  // pertubacao pequena (amplitude ~4-9px) para nao desmanchar a estrutura.
  const _orb = {{}};
  nodes.get().forEach(n => {{
    const h = _hashId(n.id);
    _orb[n.id] = {{
      ax: 4 + (h % 37) / 37 * 5,          // semi-eixo X  (4..9)
      ay: 3 + ((h >> 3) % 29) / 29 * 5,   // semi-eixo Y  (3..8)
      sp: 0.12 + ((h >> 5) % 53) / 53 * 0.22,  // velocidade angular
      ph: (h % 628) / 100,                // fase inicial
      ex: 0.25 + ((h >> 2) % 11) / 11 * 0.5,   // excentricidade 0.25..0.75
      inc: ((h >> 7) % 360) * Math.PI / 180,   // inclinacao da elipse
    }};
  }});
  function _derivaOrbital(id, t) {{
    const o = _orb[id];
    if (!o) return {{ dx: 0, dy: 0 }};
    const ang = t * 0.001 * o.sp * _velGlobal + o.ph;
    // elipse: x = a*cos, y = b*sin (com excentricidade no eixo x)
    const cx = Math.cos(o.inc), sy = Math.sin(o.inc);
    let ex = o.ax * Math.cos(ang), ey = o.ay * Math.sin(ang) * o.ex;
    // rotaciona a elipse pela inclinacao propria do no
    return {{ dx: ex * cx - ey * sy, dy: ex * sy + ey * cx }};
  }}
  network.on('tick', () => {{
    if (_tickPausado) return;
    // Quando ha um destaque/foco ativo (clicado em no, categoria, cluster),
    // congelamos a decoracao viva para NAO apagar o efeito visual escolhido.
    if (_destacado) return;
    const agora = Date.now();
    const base = 0.80 + 0.20 * Math.sin(agora * 0.0022);
    // --- pseudo-3D: calcula tamanho/opacidade/glow por profundidade viva ---
    // Perto (z->1): mais opaco, maior e mais brilhante. Longe (z->0):
    // translucido, menor e apagado -> efeito de relevo/esfera de conhecimento.
    const noUpd = [];
    const agoraPulso = (!window.__pulseT || (agora - window.__pulseT) > 220);
    if (agoraPulso) window.__pulseT = agora;
    nodes.get().forEach(n => {{
      const z = _zVivo(n.id, agora); // flutua autonomo no tempo
      const esc = 0.68 + 0.62 * z;   // fator de escala por profundidade
      const op = Math.min(1, base * (0.50 + 0.50 * z));
      let sz = (original[n.id] ? original[n.id].size : 12);
      let sombra = Math.round(14 + 18 * z);
      // deriva orbital: desloca o no suavemente em volta da posicao fisica
      const orb = _derivaOrbital(n.id, agora);
      if (agoraPulso) {{
        const fase = _zFase[n.id] != null ? _zFase[n.id] : ((_hashId(n.id) || 0) % 97);
        // Nos QUENTES (atividade real alta, mtime recente) latejam com mais
        // energia e brilham mais forte: o pulso escala com atv.
        const atv = (n.atv != null) ? n.atv : 0.5;
        const pulso = Math.sin(agora * 0.0020 * _velGlobal + fase) * (0.07 + 0.13 * atv);
        sz = Math.max(6, sz * (1 + pulso * 0.55) * esc);
        sombra = Math.round(sombra + (6 + 14 * atv) * pulso);
      }} else {{
        sz = Math.max(6, sz * esc);
      }}
      noUpd.push({{
        id: n.id,
        opacity: op,
        shadow: z > 0.3,
        shadowSize: sombra,
        size: sz,
        x: n.x + orb.dx,
        y: n.y + orb.dy
      }});
    }});
    nodes.update(noUpd);
    // --- arestas: opacidade pela profundidade media das pontas ---
    // Conexoes entre nos "perto" ficam mais visiveis; entre "longe" somem.
    let arestasUp = edges.get().map(e => {{
      const zA = _zVivo(e.from, agora);
      const zB = _zVivo(e.to, agora);
      const zM = (zA + zB) / 2;
      return {{ id: e.id, color: arestaOriginal[e.id] ? arestaOriginal[e.id].color : '#999',
                 width: arestaOriginal[e.id] ? arestaOriginal[e.id].width : 1,
                 opacity: 0.25 * (0.55 + 0.9 * zM) }};
    }});
    if (agora - _ultimoSpike > _proxSpike()) {{
      _ultimoSpike = agora;
      const todas = edges.get();
      if (todas.length) {{
        const alvos = [];
        const qtd = 2 + Math.floor(Math.random() * 4);
        for (let i = 0; i < qtd && todas.length; i++) {{
          alvos.push(todas[Math.floor(Math.random() * todas.length)].id);
        }}
        arestasUp = arestasUp.map(a =>
          alvos.includes(a.id)
            ? {{ ...a, color: '#ffffff', width: 5.5, opacity: 1 }}
            : a);
        // leve glow no no destino de cada sinapse
        alvos.forEach(edgeId => {{
          const _ed = todas.find(x => x.id === edgeId);
          if (!_ed) return;
          const _dstOrig = original[_ed.to] || {{color:'#4e79a7', size:15}};
          nodes.update([{{ id: _ed.to, color: '#89b4fa', size: 26, shadow: true, shadowSize: 28 }}]);
          setTimeout(() => nodes.update([{{ id: _ed.to, color: _dstOrig.color, size: _dstOrig.size }}]), 700);
        }});
      }}
    }}
    edges.update(arestasUp);
    // --- INTEGRACAO NEURAL (criticalidade + avalanche espontanea) ---
    _integracaoNeural(agora, noUpd);
  }});
  // pausa o balanco organico ao pairar sobre um no
  network.on('hoverNode', () => {{ _tickPausado = true; }});
  network.on('blurNode', () => {{ _tickPausado = false; }});

  // Intervalo aleatorio entre pulsos de sinapse (1.6s a 3.2s)
  function _proxSpike() {{ return 1600 + Math.random() * 1600; }}

  // --- DISPARO NEURAL + AVALANCHE (criticalidade auto-organizada) ---
  // Atualiza os potenciais de membrana de todos os nos (corrente de base) e,
  // quando um cruza o limiar, dispara uma avalanche: o pulso e visivel e a
  // energia e repassada aos vizinhos (ramificacao com parametro critico).
  // Evita excursion em nos em fase refrataria.
  var _sinapsePorNo = null; // cache {{id: [vizinhos]}}
  function _vizinhos(id) {{
    if (!_sinapsePorNo) {{
      _sinapsePorNo = {{}};
      edges.get().forEach(function(e) {{
        (_sinapsePorNo[e.from] = _sinapsePorNo[e.from] || []).push(e.to);
        (_sinapsePorNo[e.to] = _sinapsePorNo[e.to] || []).push(e.from);
      }});
    }}
    return _sinapsePorNo[id] || [];
  }}
  function _disparo(no) {{
    // Disparou: pulso de glow no no e nas sinapses que chegam a ele.
    // Restauramos a cor/size originais logo apos o pulso (deterministico).
    const noOrig = original[no.id];
    if (noOrig) {{
      nodes.update([{{
        id: no.id,
        color: '#a6e3a1', // verde-neuro: excitacao
        shadow: true,
        shadowSize: 30,
        size: (noOrig ? noOrig.size : 12) + 6
      }}]);
      (function(id, cor, tam) {{
        setTimeout(function() {{
          try {{ nodes.update([{{ id: id, color: cor, shadow: false, shadowSize: 0, size: tam }}]); }} catch(e) {{}}
        }}, 650);
      }})(no.id, noOrig.color, noOrig.size);
    }}
    // acende as sinapses aderentes a este no e as apaga depois
    const ligadas = edges.get().filter(function(e) {{
      return e.from === no.id || e.to === no.id;
    }});
    if (ligadas.length) {{
      edges.update(ligadas.map(function(e) {{
        return {{ id: e.id, color: '#a6e3a1', width: 4, opacity: 0.95 }};
      }}));
      ligadas.forEach(function(e) {{
        const base = arestaOriginal[e.id];
        setTimeout(function() {{
          try {{
            edges.update([{{
              id: e.id,
              color: base ? base.color : '#999',
              width: base ? base.width : 1,
              opacity: 0.25
            }}]);
          }} catch(err) {{}}
        }}, 600);
      }});
    }}
  }}
  function _ruidoEspontaneo(id, agora) {{
    // "consciencia de fundo": mesmo em repouso ha corrente espontanea que,
    // ocasionalmente, cruza o limiar e inicia pequenas avalanches, e raramente
    // uma grande. Soma astrocial lenta (calcio) e pequena flutuacao.
    return _solo * (0.6 + 0.8 * Math.random())
         + 0.03 * Math.sin(agora * 0.0020 + _zFase[id])  // onda glial
         + 0.020 * Math.sin(agora * 0.0007 + _zFase[id] * 1.7);
  }}
  function _integracaoNeural(agora, noUpd) {{
    const todas = edges.get();
    if (!todas.length) return;
    const agoraMs = agora;
    // 1) corrente de base espontanea em todos os nos
    nodes.get().forEach(function(n) {{
      const id = n.id;
      if (_refrat[id] && agoraMs - _refrat[id] < _REF) return; // refratario
      _memb[id] = (_memb[id] || 0) + _ruidoEspontaneo(id, agoraMs);
    }});
    // 2) avalanche ativa: propaga energia dos disparos ja em curso
    if (_avalanche.ativo) {{
      const passo = _avalanche.fila.splice(0, _avalanche.fila.length);
      passo.forEach(function(seed) {{
        const viz = _vizinhos(seed.id);
        for (let i = 0; i < viz.length; i++) {{
          const v = viz[i];
          if (_refrat[v] && agoraMs - _refrat[v] < _REF) continue;
          // excitacao decai com a distancia mas so passa se sigma critico
          if (Math.random() < _sigma) {{
            _memb[v] = (_memb[v] || 0) + seed.energia;
            _avalanche.size++;
            if (_avalanche.size > _avalanche.maior) _avalanche.maior = _avalanche.size;
            if (_memb[v] >= _LIMIAR) {{
              _disparo({{ id: v }});
              _memb[v] = 0; _refrat[v] = agoraMs;
              _avalanche.fila.push({{ id: v, energia: 1 - 0.1 * (1 + Math.floor(Math.random() * 3)) }});
            }}
          }}
        }}
      }});
      // se a fila esvaziou, a avalanche acabou
      if (!_avalanche.fila.length) _avalanche.ativo = false;
    }}
    // 3) varredura final: nos acima do limiar disparam e iniciam ramificacao
    nodes.get().forEach(function(n) {{
      const id = n.id;
      if (_refrat[id] && agoraMs - _refrat[id] < _REF) return;
      if (_memb[id] >= _LIMIAR) {{
        _disparo({{ id: id }});
        _memb[id] = 0; _refrat[id] = agoraMs;
        _avalanche.ativo = true;
        _avalanche.fila.push({{ id: id, energia: 1 - 0.1 * (1 + Math.floor(Math.random() * 3)) }});
        _avalanche.size++;
      }}
    }});
  }}

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

  const _fontLimpo = (function() {{
    // respeita o padrao de labels ocultas (so 'false' mostra)
    var oc = (typeof localStorage !== 'undefined' && localStorage.getItem('labelsOcultos') !== 'false');
    return oc ? 0 : 11;
  }})();
  function limpar() {{
    _destacado = false; // libera de volta a decoracao viva (cerebro vivo)
    // reseta o estado do motor de avalanches: pausa correntes/residual
    _avalanche = {{ ativo: false, fila: [], maior: 0, size: 0 }};
    _memb = {{}}; _refrat = {{}};
    nodes.get().forEach(function(n) {{ _memb[n.id] = Math.random() * _LIMIAR * 0.7; }});
    _sinapsePorNo = null; // forca reconstrucao do cache de vizinhos
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const atualizacoes = nodes.get().map(n => ({{
      id: n.id, color: original[n.id].color, size: original[n.id].size,
      opacity: 1, borderWidth: 0, borderWidthSelected: 0, shadow: false,
      font: {{ size: _fontLimpo, color: '#cdd6f4', face: 'Segoe UI', bold: false }}
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
    _destacado = true; // congela decoracao viva: preserva o efeito do clique
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
    _destacado = true; // congela decoracao viva: preserva o destaque do grupo
    document.querySelectorAll('.lg').forEach(b => b.classList.remove('active'));
    const alvo = document.querySelector(`.lg[data-filter="${{filtro}}"][data-value="${{valor}}"]`);
    if (alvo) alvo.classList.add('active');

    // conjunto de nos do grupo
    const grupo = new Set();
    nodes.get().forEach(n => {{
      if (filtro === 'cat' && n.cat === valor) grupo.add(n.id);
      else if (filtro === 'cl' && n.cl === valor) grupo.add(n.id);
      else if (filtro === 'st' && n.st === valor) grupo.add(n.id);
      else if (filtro === 'dom') {{
        const ehMCP = (n.tags || []).some(t => String(t).toLowerCase().indexOf('mcp') !== -1);
        const ehHub = n.cat === 'hub' || n.cat === 'geral';
        // 'mcp' -> notas com tag mcp; 'conhecimento' -> notas sem tag mcp
        // (hubs/categorias genericas nao entram no filtro de dominio)
        if (!ehHub && (valor === 'mcp' ? ehMCP : !ehMCP)) grupo.add(n.id);
      }}
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
