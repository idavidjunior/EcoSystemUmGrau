"""Gera o vault Obsidian vivo: notas + hubs + links bidirecionais a partir do knowledge_graph.json.

Transforma o conhecimento do ecossistema em uma teia (grafo) navegavel no Obsidian:

  1. Gera notas por categoria (padroes, decisoes, bugs, cognitivo, heuristicas, frameworks, missoes)
  2. Gera notas-hub por categoria e por cluster de projeto (navegacao, ler, android, ...)
  3. Conecta tudo com links bidirecionais [[...]] (arestas reais do grafo)
  4. Injeta a secao "## Conexoes" nos aprendizados (conhecimento/aprendizados/*.md)

Uso:
  python scripts/generate-obsidian-notes.py            # gera tudo
  python scripts/generate-obsidian-notes.py --no-links # apenas notas+hubs, sem injetar aprendizados
  python scripts/generate-obsidian-notes.py --dry-run  # reporta o que faria, sem escrever

Exit: 0 = sucesso.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
LER_DIR = os.path.join(BASE, 'ler-runtime')
GRAPH_FILE = os.path.join(LER_DIR, 'knowledge', 'knowledge_graph.json')
OUTPUT_DIR = os.path.join(BASE, 'conhecimento', 'notas')
APRENDIZADOS_DIR = os.path.join(BASE, 'conhecimento', 'aprendizados')
sys.path.insert(0, os.path.join(BASE, 'scripts'))
try:
    from semantic_tags import extrair_tags
except ImportError:
    extrair_tags = None
try:
    from cluster_mapper import ClusterMapper
except ImportError:
    ClusterMapper = None

CATEGORIAS = ['padroes', 'decisoes', 'bugs', 'cognitivo', 'heuristicas', 'frameworks', 'missoes']

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
    'programacao': ['python', 'javascript', 'typescript', 'node', 'bash', 'java', 'kotlin',
                    'c', 'cpp', 'rust', 'csharp', 'golang', 'php', 'ruby', 'sql',
                    'fundamentos', 'engenharia', 'arquitetura', 'designpatterns',
                    'testes', 'git', 'apis-web', 'bancos-dados', 'seguranca',
                    'devops', 'linux', 'performance'],
}

CATEGORIA_EMOJI = {
    'padroes': 'padrao', 'decisoes': 'decisao', 'bugs': 'bug', 'cognitivo': 'cognitivo',
    'heuristicas': 'heuristica', 'frameworks': 'framework', 'missoes': 'missao',
}
CATEGORIA_LABEL = {
    'padroes': 'Padroes Tecnicos', 'decisoes': 'Decisoes', 'bugs': 'Bugs e Correcoes',
    'cognitivo': 'Padroes Cognitivos', 'heuristicas': 'Heuristicas',
    'frameworks': 'Frameworks', 'missoes': 'Missoes',
}


def slugify(text, maxlen=60):
    text = re.sub(r'[^a-zA-Z0-9\u00C0-\u024F\u00E0-\u024F\s-]', '', str(text))
    text = re.sub(r'[-\s]+', '-', text.strip().lower()).strip('-')
    return text[:maxlen] if text else None


def cluster_of(source):
    src = (source or '').split('+')[0].strip()
    for cluster, sources in CLUSTERS.items():
        if src in sources:
            return cluster
    return 'geral'


def cluster_da_nota(tags, categoria='', slug='', mapper=None, fonte=''):
    """Resolve o cluster de uma nota: o mapeamento explícito por fonte tem
    precedência; o ClusterMapper (aprendizado) só atua quando a fonte é
    'geral' (sem mapeamento estático)."""
    estatico = cluster_of(fonte or slug or '') if (fonte or slug) else cluster_of('')
    if estatico != 'geral':
        return estatico
    if mapper is not None:
        return mapper.resolver(tags or [], '', categoria, slug)
    return estatico


def read_graph():
    with open(GRAPH_FILE, encoding='utf-8') as f:
        return json.load(f)


def extract_items(g):
    """Extrai notas planas de todas as categorias do graph."""
    items = []  # (categoria, slug, title, tags, body, sources)
    updated = g.get('last_updated', datetime.now().isoformat())[:10]

    for p in g.get('patterns', []):
        title = (p.get('title', '') or '').strip()
        if not title:
            continue
        slug = slugify(title)
        if not slug:
            continue
        src = p.get('source', '')
        body = f'**Fonte:** {src}\n\n{p.get("description", p.get("action", ""))}'
        items.append(('padroes', slug, title, ['padrao', slugify(src) or 'geral'], body, [src], updated))

    for d in g.get('decisions', []):
        title = (d.get('decision', '') or '').strip()
        if not title:
            continue
        slug = slugify(title[:80])
        if not slug:
            continue
        src = d.get('source', '')
        body = f'**Fonte:** {src}\n\n{p.get("rationale", d.get("rationale", ""))}'
        items.append(('decisoes', slug, title, ['decisao', slugify(src) or 'geral'], body, [src], updated))

    for b in g.get('bug_fixes', []):
        title = (b.get('issue', '') or '').strip()
        if not title or title.strip(' -\n\t\r') == '-----------':
            continue
        slug = slugify(title[:80])
        if not slug:
            continue
        src = b.get('source', '')
        body = f'**Projeto:** {src}\n\n## Causa Raiz\n{b.get("root_cause", "")}\n\n## Correcao\n{b.get("fix", "")}'
        items.append(('bugs', slug, title, ['bug', slugify(src) or 'geral'], body, [src], updated))

    for c in g.get('cognitive_patterns', []):
        title = c.get('title', 'Cognitive pattern')
        slug = slugify(title)
        if not slug:
            continue
        dom = slugify(c.get('domain', 'general')) or 'general'
        src = c.get('source', '')
        body = f'**Dominio:** {c.get("domain", "")}\n\n{c.get("body", "")}'
        items.append(('cognitivo', slug, title, ['cognitivo', dom], body, [src], updated))

    for h in g.get('heuristics', []):
        title = h.get('title', 'Heuristic')
        slug = slugify(title)
        if not slug:
            continue
        dom = slugify(h.get('domain', '')) or 'geral'
        src = h.get('source', '')
        body = f'**Dominio:** {h.get("domain", "")} | **Fonte:** {src}\n\n{h.get("description", "")}'
        items.append(('heuristicas', slug, title, ['heuristica', dom], body, [src], updated))

    for f in g.get('frameworks', []):
        name = f.get('name', 'Framework')
        slug = slugify(name)
        if not slug:
            continue
        src = f.get('source', '')
        body = f'{f.get("description", "")}\n\n{f.get("body", "")}'
        items.append(('frameworks', slug, name, ['framework'], body, [src], updated))

    for m in g.get('mission_learnings', []):
        goal = (m.get('goal_objective', 'Mission') or '')[:80]
        slug = slugify(goal)
        if not slug:
            continue
        ts = m.get('timestamp', '')[:10]
        tags = ['missao'] + [slugify(t) for t in (m.get('tags', []) or [])[:3] if slugify(t)]
        files = m.get('files_modified', [])
        files_str = ', '.join(files[:10]) if isinstance(files, list) else str(files or '')
        body = f'**Status:** {m.get("status", "")}\n\n**Objetivo:** {goal}'
        if files_str:
            body += f'\n\n**Arquivos:** {files_str}'
        items.append(('missoes', slug, goal, tags, body, [], ts or updated))

    return items


def _enriquecer_tags(tags_base, texto):
    """Adiciona tags semanticas (RAKE leve) extraidas do corpo da nota."""
    if not texto or not extrair_tags:
        return tags_base
    novas = []
    for t in extrair_tags(texto, max_tags=4):
        if t and t not in tags_base:
            novas.append(t)
    return tags_base + novas


def frontmatter(tags, aliases=None, date=None):
    fm = ['---']
    if tags:
        fm.append(f'tags: [{", ".join(sorted(set(t for t in tags if t)))}]')
    if aliases:
        fm.append(f'aliases: [{", ".join(aliases)}]')
    if date:
        fm.append(f'date: {date}')
    fm.append('---')
    return '\n'.join(fm)


def write_note(subdir, filename, content):
    d = os.path.join(OUTPUT_DIR, subdir)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, filename), 'w', encoding='utf-8') as f:
        f.write(content)
    return os.path.join(d, filename)


def limpar_orfãos(escritos):
    """Remove notas .md em pastas gerenciadas que nao existem mais no grafo.
    Preserva conhecimento/aprendizados (fontes) e arquivos nao-.md."""
    pastas = CATEGORIAS + ['_hubs']
    removidos = 0
    for sub in pastas:
        d = os.path.join(OUTPUT_DIR, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith('.md'):
                continue
            full = os.path.join(d, f)
            if full not in escritos:
                try:
                    os.remove(full)
                    removidos += 1
                except OSError:
                    pass
    if removidos:
        print(f'{removidos} notas orfas removidas (nao estao mais no knowledge graph)')
    return removidos


def seccao_conexoes(links):
    if not links:
        return ''
    body = ['\n## Conexoes\n']
    for name in sorted(set(links)):
        body.append(f'- [[{name}]]')
    return '\n'.join(body)


def generate(dry_run=False, inject_links=True):
    print(f'Lendo {GRAPH_FILE}...')
    g = read_graph()
    items = extract_items(g)
    print(f'{len(items)} notas de conhecimento extraidas')
    escritos = set()

    # indice: slug -> (categoria, title, tags, sources)
    index = {}
    for cat, slug, title, tags, body, sources, updated in items:
        index[slug] = {'categoria': cat, 'title': title, 'tags': tags, 'sources': sources}

    # TREINO do ClusterMapper com as notas do graph (aprendizado + ousadia)
    _mapper = None
    if ClusterMapper is not None:
        try:
            _mapper = ClusterMapper()
            _dados = [{'tags': m['tags'], 'fonte': m['sources'][0] if m['sources'] else '',
                       'slug': slug, 'categoria': m['categoria'], 'cl_bruto': ''}
                      for slug, m in index.items()]
            _mapper.treinar(_dados)
        except Exception as e:
            print(f'  [aviso] ClusterMapper indisponivel: {e}')
            _mapper = None

    # por categoria e por cluster -> lista de slugs
    por_categoria = defaultdict(list)
    por_cluster = defaultdict(list)
    por_tag = defaultdict(list)
    for slug, meta in index.items():
        por_categoria[meta['categoria']].append(slug)
        cl = cluster_da_nota(meta['tags'], meta['categoria'], slug, _mapper,
                             meta['sources'][0] if meta['sources'] else '')
        por_cluster[cl].append(slug)
        for t in meta['tags']:
            if t and t not in ('geral', 'general'):
                por_tag[t].append(slug)

    written = 0
    # ---------- notas individuais ----------
    for cat, slug, title, tags, body, sources, updated in items:
        cl = cluster_da_nota(tags, cat, slug, _mapper, sources[0] if sources else '')
        links = []
        links.append(f'{CATEGORIA_EMOJI[cat]}-hub-{cat}')
        if cl != 'geral':
            links.append(f'cluster-hub-{cl}')
        # liga a uma nota mesma-categoria que compartilha fonte ou tag
        vizinhos = 0
        for t in tags:
            if t in ('geral', 'general') or t == CATEGORIA_EMOJI[cat]:
                continue
            for v in por_tag.get(t, []):
                if v != slug and v not in links:
                    links.append(v)
                    vizinhos += 1
                    if vizinhos >= 4:
                        break
            if vizinhos >= 4:
                break
        if not dry_run:
            # enriquece tags com conceitos do corpo (sinapses via tags semanticas)
            tags_finais = _enriquecer_tags(list(tags), f'{title} {body}')
            escritos.add(write_note(cat, f'{slug}.md',
                       f'{frontmatter(tags_finais, [title[:60]], updated)}\n\n# {title}\n\n{body}{seccao_conexoes(links)}'))
        written += 1

    # ---------- hubs de categoria ----------
    hub_links = {'Home': f'[[home]]'}
    for cat in CATEGORIAS:
        items_cat = sorted(set(por_categoria.get(cat, [])))
        label = CATEGORIA_LABEL[cat]
        emoji = CATEGORIA_EMOJI[cat]
        body = [f'# {label}\n', f'**{len(items_cat)} notas** conectadas a este hub.\n']
        body.append('\n## Notas')
        for slug in items_cat:
            body.append(f'- [[{slug}]]')
        if not dry_run:
            escritos.add(write_note('_hubs', f'{emoji}-hub-{cat}.md', '\n'.join(body)))
        written += 1
        hub_links[cat] = f'[[{emoji}-hub-{cat}]]'

    # ---------- hubs de cluster (projeto) ----------
    cluster_labels = {
        'android': 'Android (SDK puro)', 'mp3player': 'MP3 Player', 'ler': 'LER (Loop de Execucao)',
        'navegacao': 'Navegacao (web/PC/mobile)', 'ecossistema': 'Ecossistema OpenCode', 'cognicao': 'Cognicao',
        'geral': 'Geral',
        'programacao': 'Programacao (linguagens e engenharia)',
    }
    for cl, slugs in por_cluster.items():
        items_cl = sorted(set(slugs))
        label = cluster_labels.get(cl, cl)
        body = [f'# Cluster: {label}\n', f'**{len(items_cl)} notas** do cluster {cl}.\n']
        body.append('\n## Notas')
        for slug in items_cl:
            body.append(f'- [[{slug}]]')
        if not dry_run:
            escritos.add(write_note('_hubs', f'cluster-hub-{cl}.md', '\n'.join(body)))
        written += 1

    # ---------- Home ----------
    home = ['# Cerebro Vivo — Ecossistema UmGrau\n',
            '> Vault gerado automaticamente por `python scripts/generate-obsidian-notes.py`.\n',
            '> Edite os aprendizados ou o knowledge_graph.json e regenere.\n',
            '\n## Mapa do conhecimento\n']
    for cat in CATEGORIAS:
        home.append(f'- {CATEGORIA_LABEL[cat]}: [[{CATEGORIA_EMOJI[cat]}-hub-{cat}]]')
    home.append('\n## Clusters de projeto\n')
    for cl in sorted(por_cluster):
        home.append(f'- {cluster_labels.get(cl, cl)}: [[cluster-hub-{cl}]]')
    home.append('\n## Aprendizados (vault: conhecimento/)\n')
    home.append('- Os aprendizados vivem em `conhecimento/aprendizados/*.md` (vault raiz `conhecimento/`)')
    if not dry_run:
        escritos.add(write_note('_hubs', 'home.md', '\n'.join(home)))
    written += 1

    if not dry_run:
        limpar_orfãos(escritos)

    print(f'{written} notas + hubs escritos em {OUTPUT_DIR}')

    # ---------- injeta links nos aprendizados ----------
    injetados = 0
    if inject_links:
        if not os.path.isdir(APRENDIZADOS_DIR):
            print('AVISO: pasta de aprendizados nao encontrada, pulando injecao')
        else:
            for ap in sorted(Path(APRENDIZADOS_DIR).glob('*.md')):
                content = ap.read_text(encoding='utf-8')
                # remove secao "## Conexoes" existente para regenerar (idempotente)
                content = re.sub(r'\n## Conexoes\n+?(?:- \[\[[^\]]+\]\]\n?)+', '', content).rstrip() + '\n'
                tags = re.findall(r'tags:\s*\[?([^\]]+)\]?', content)
                tag_list = []
                for tblock in tags:
                    tag_list += [t.strip().strip('"\'') for t in re.split(r'[,\[\]]', tblock) if t.strip()]
                tag_list = [t for t in tag_list if t and not t.startswith('-')]
                if not tag_list:
                    m = re.search(r'\*\*Tags?:\*\*\s*(.+)', content)
                    if m:
                        tag_list = [t.strip() for t in m.group(1).split(',') if t.strip()]
                tag_list = [t.lower() for t in tag_list]
                # acha hubs de categoria/cluster por tags
                links = []
                for t in tag_list:
                    if t in por_tag:
                        hub_cat = None
                        for cand, metas in index.items():
                            if t in metas['tags']:
                                hub_cat = cand
                                break
                        if hub_cat and len(por_tag[t]) >= 2:
                            links.append(hub_cat)
                # cluster por nome de arquivo (ex: scan-Mp3Player -> mp3player)
                fname = ap.stem.lower()
                for cl, sources in CLUSTERS.items():
                    if any(s.split('_')[0] in fname or s.replace('_', '').replace('-', '') in fname.replace('-', '').replace('_', '')
                           for s in sources):
                        links.append(f'cluster-hub-{cl}')
                        break
                links = [l for l in set(links) if l in index or l.startswith('cluster-hub-')]
                if links:
                    novo = content + seccao_conexoes(links)
                    if novo != content:
                        if not dry_run:
                            ap.write_text(novo, encoding='utf-8')
                        injetados += 1

    print(f'{injetados} aprendizados receberam conexoes')
    print('OK — abra o vault no Obsidian: abrir pasta como vault -> conhecimento/')
    return 0


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    inject = '--no-links' not in sys.argv
    sys.exit(generate(dry_run=dry, inject_links=inject))
