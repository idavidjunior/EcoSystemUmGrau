"""Context Loader inteligente do Ecossistema.

NUNCA carrega toda a memória. Antes de cada tarefa, identifica o assunto
tratado pelo usuário e carrega apenas os documentos, memórias e conhecimentos
relevantes para aquela execução — reduzindo consumo de contexto e aumentando
precisão.

Melhorias v1.1:
- Fusão de relevância por tokens (não substring exata da frase inteira).
- Projeto ativo do Runtime usado automaticamente como filtro/prioridade.
- Bônus de relevância para memórias do projeto ativo.
- Carrega documentos/arquivos-chave do projeto relevante.
- Sugestão de agentes/Conselho conforme a criticidade da tarefa.
- Registro do que foi carregado no estado do Runtime (rastreabilidade).

Uso CLI:
  python scripts/runtime_context.py "<objetivo/assunto>"
  python scripts/runtime_context.py --projeto <nome> "<assunto>"
  python scripts/runtime_context.py --limite <N> "<assunto>"
  python scripts/runtime_context.py --json "<assunto>"
"""

import argparse
import json
import os
import re
import sys

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

try:
    from knowledge_graph import kg, NodeType, EdgeType
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_BOM = '\ufeff'
_STOP = set("""a o os as um uma uns umas e mas nem ou que se no na nos nas de do da dos
das em ao aos perante por para com contra entre sem sob sobre apos antes depois
daquele esta esse isto isso aquele este estes essas aqui ali ser esta estava para
como uma das seu sua seus suas com sem quer fazer feito vai vou ir no na nos nos""".split())

_PROJETOS = ['EcoSystemUmGrau', 'Mp3Player', 'CellCleaner', 'BibliaEstudoCompleta',
             'SupermarketCalculator', 'VoxUmGrau', 'WindowsMaintenanceSuite_v3',
             'OrquestradorAPK-FLUTTER', 'compiladorAPK', 'roboumgrau', 'Rob-Trader',
             'claude-code-extra-agents']


def _clean(s):
    return (s or '').replace(_BOM, '')


# --- Digest passes para modelos pequenos (padrão isair/jarvis) -------------
# Modelos pequenos (≤7B) degradam quando o prompt cresce. O digest condensa o
# contexto de memória/ferramentas antes de injetar: cabeçalho + corpo enxuto +
# fecho, sem descartar o começo (quase sempre o mais relevante). Nunca lança.
def _modelo_pequeno(modelo=None):
    if not modelo:
        modelo = os.environ.get('LLM_CHAT_MODEL', '')
    nome = (modelo or '').lower()
    return any(x in nome for x in ('0.8b', '1b', '1.5b', '2b', '3b', '4b', '7b')) or nome in ('', 'auto')


def digest_contexto(texto, max_chars=4000):
    """Condensa texto de contexto para caber em modelos pequenos.

    Se o texto já cabe no teto, devolve intacto. Caso contrário, mantém o
    início (cabeçalho/contexto imediato), reduz o miolo a linhas essenciais
    e preserva o fecho. Retorna string nunca vazia se a entrada não era vazia.
    """
    if not texto:
        return ""
    if max_chars <= 0:
        return texto
    if len(texto) <= max_chars:
        return texto
    inicio = texto[: max_chars // 2]
    fim = texto[-max(200, max_chars // 4):]
    return inicio.rstrip() + f"\n...[contexto condensado: {len(texto) - (max_chars // 2 + max(200, max_chars // 4))} chars suprimidos]...\n" + fim.lstrip()


def _tokenizar(texto):
    return [t for t in re.findall(r'[a-zA-Z0-9]{3,}', (texto or '').lower())
            if t not in _STOP]


def _extrair_tags(texto, max_tags=6):
    try:
        from semantic_tags import extrair_tags
        return extrair_tags(texto, max_tags=max_tags) or []
    except Exception:
        return []


def _projeto_ativo():
    try:
        from runtime_state import load_state
        return load_state().get('active_project', '') or ''
    except Exception:
        return ''


def _sugerir_agentes(criticidade):
    """Sugere agentes/Conselho conforme a criticidade da tarefa."""
    base = ['01-Estrategista', '06-Recursos', '08-Revisor']
    if criticidade == 'alta':
        return base + ['02-Cetico', '03-Realista', '04-Etica', '05-Futuro',
                       '07-Criativo', '11-LER-Executor']
    if criticidade == 'media':
        return base + ['02-Cetico', '07-Criativo']
    return ['06-Recursos', '08-Revisor']


def _carregar_memorias(assunto, tags, limite, projeto_ativo=''):
    """Fusão de relevância: tokens + tags + bônus de projeto."""
    try:
        import memory_engine
        todas = memory_engine.query(limit=100)
        tokens = set(_tokenizar(assunto)) | set(t.lower() for t in tags)
        scored = []
        for m in todas:
            score = 0.0
            texto = (m.get('task', '') + ' ' + m.get('summary', '') + ' ' +
                     ' '.join(m.get('tags', [])) + ' ' + m.get('project', '')).lower()
            for t in tokens:
                if len(t) < 3:
                    continue
                if t in texto:
                    score += 1.0
                    # reforço se é tag semântica
                    if t in [x.lower() for x in tags]:
                        score += 0.5
            # bônus do projeto ativo
            if projeto_ativo and m.get('project', '') == projeto_ativo:
                score += 0.5
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: -x[0])
        result = []
        for score, m in scored[:limite]:
            result.append({
                'id': m.get('id'),
                'tipo': m['kind'],
                'titulo': _clean(m['task']),
                'resumo': _clean(m['summary'])[:160],
                'projeto': _clean(m.get('project', '')),
                'score': round(score, 2),
            })
        return result
    except Exception:
        return []


def _carregar_conhecimento(assunto, tags, limite):
    """BM25 fusion, com reforço das tags na query."""
    try:
        ksearch = os.path.join(BASE, 'mcp', 'memoria', 'habilidades',
                               'busca-conhecimento', 'search_knowledge.py')
        if os.path.exists(ksearch):
            sys.path.insert(0, os.path.dirname(ksearch))
            import search_knowledge as sk
            docs = sk.load_corpus()
            query = assunto
            if tags:
                query += ' ' + ' '.join(tags)
            results = sk.bm25(query, docs)
            out = []
            for score, doc_id, text in results[:limite]:
                if score < 0.1:
                    break
                kind = doc_id.split(':')[0]
                title = doc_id.split(':', 1)[1] if ':' in doc_id else doc_id
                out.append({
                    'fonte': kind,
                    'titulo': _clean(title)[:80],
                    'score': round(score, 3),
                })
            return out
    except Exception:
        pass
    return []


def _carregar_decisoes(assunto, tags, limite):
    """Decisões consolidadas relacionadas (nunca contrariar sem justificativa)."""
    try:
        import memory_engine
        todas = memory_engine.query(kind='decisao', limit=100)
        tokens = set(_tokenizar(assunto)) | set(t.lower() for t in tags)
        scored = []
        for m in todas:
            texto = (m.get('task', '') + ' ' + m.get('summary', '')).lower()
            score = sum(1 for t in tokens if len(t) >= 3 and t in texto)
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: -x[0])
        return [{'titulo': _clean(m['task'])[:80], 'resumo': _clean(m['summary'])[:120]}
                for _, m in scored[:limite]]
    except Exception:
        return []


_RX_LINK = re.compile(r'\[\[([^\]\|#]+)')
_DIRS_NOTAS = [os.path.join(BASE, 'conhecimento', 'notas'),
               os.path.join(BASE, 'conhecimento', 'aprendizados')]


def _carregar_sinapses(conhecimento, max_notas=4, max_links=4):
    """Expande resultados do vault com a vizinhanca do grafo vivo.

    Para cada nota recuperada pelo BM25, extrai os links [[...]] do corpo
    e devolve as conexoes (sinapses) como contexto estruturado.
    Hubs e Home sao ignorados (navegacao, nao conhecimento).
    """
    alvos = [c['titulo'] for c in conhecimento if c.get('fonte') == 'nota']
    if not alvos:
        return []
    restantes = set(alvos[:max_notas])
    achados = {}
    for notas_dir in _DIRS_NOTAS:
        if not restantes or not os.path.isdir(notas_dir):
            continue
        for root, _, files in os.walk(notas_dir):
            if not restantes:
                break
            for fname in files:
                stem = fname[:-3] if fname.endswith('.md') else ''
                if stem in restantes:
                    achados[stem] = os.path.join(root, fname)
                    restantes.discard(stem)
                    if not restantes:
                        break
    out = []
    for slug in alvos:
        if len(out) >= max_notas or slug not in achados:
            continue
        try:
            with open(achados[slug], encoding='utf-8', errors='replace') as f:
                conteudo = f.read(8000)
        except OSError:
            continue
        links = []
        for m in _RX_LINK.findall(conteudo):
            destino = _clean(m).strip()
            if not destino or 'hub-' in destino.lower() or \
                    destino.lower() in ('home',):
                continue
            if destino not in links:
                links.append(destino)
            if len(links) >= max_links:
                break
        if links:
            out.append({'nota': slug[:60], 'conecta': links})
    return out


def _carregar_docs_projeto(projeto_ativo, limite=5):
    """Carrega documentos-chave do projeto ativo (sem varrer tudo)."""
    if not projeto_ativo:
        return []
    candidatos = []
    # Projeto no diretório Projetos/ ou raiz
    for base_dir in (os.path.join(BASE, 'Projetos', projeto_ativo), os.path.join(BASE, projeto_ativo)):
        if not os.path.isdir(base_dir):
            continue
        for fname in ('README.md', 'PROJECTS_STRUCTURE.md', 'estado_atual.md', 'docs'):
            p = os.path.join(base_dir, fname)
            if os.path.isfile(p):
                candidatos.append(p)
        docs_dir = os.path.join(base_dir, 'docs')
        if os.path.isdir(docs_dir):
            for f in sorted(os.listdir(docs_dir))[:limite]:
                candidatos.append(os.path.join(docs_dir, f))
        break
    out = []
    for p in candidatos[:limite]:
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                head = f.read(2000)
            out.append({'arquivo': os.path.relpath(p, BASE),
                        'resumo': _clean(head).strip().replace('\n', ' ')[:160]})
        except Exception:
            pass
    return out


def _carregar_knowledge_graph(assunto, tags, limite, projeto_ativo=''):
    """Carrega nodes e edges relevantes do Knowledge Graph."""
    if not KG_AVAILABLE:
        return {'nodes': [], 'edges': [], 'query_used': ''}
    try:
        # Buscar no KG usando busca semântica
        result = kg.search(assunto, limit=limite)
        nodes_out = []
        for n in result.nodes:
            nodes_out.append({
                'id': n.id,
                'tipo': n.type.value if hasattr(n.type, 'value') else n.type,
                'nome': n.name,
                'tags': n.tags,
                'resumo': n.properties.get('summary', '')[:160],
            })
        edges_out = []
        for e in result.edges:
            edges_out.append({
                'origem': e.source_id,
                'destino': e.target_id,
                'tipo': e.type.value if hasattr(e.type, 'value') else e.type,
                'peso': e.weight,
            })
        return {
            'nodes': nodes_out,
            'edges': edges_out,
            'query_used': assunto,
        }
    except Exception:
        return {'nodes': [], 'edges': [], 'query_used': assunto}


def _carregar_pendencias_runtime():
    try:
        from runtime_state import load_state
        state = load_state()
        pends = [p for p in state.get('pending', []) if not p.get('done')]
        return [f"#{p['id']} {p['text']}" for p in pends]
    except Exception:
        return []


def _carregar_sinapses_dinamicas(memorias_servidas, maximo=4):
    """Sinapses Vivas fase 2: vizinhos das arestas de co-uso real.
    Fail-soft; nunca inventa memória inexistente."""
    try:
        from pathlib import Path
        import json as _json
        f = Path(__file__).resolve().parent.parent / 'runtime' / 'sinapses' / 'arestas.json'
        arestas = _json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        return []
    ids_servidos = {m.get('id') for m in memorias_servidas
                    if isinstance(m.get('id'), int)}
    if not ids_servidos:
        return []
    vizinhos = {}
    for chave, peso in arestas.items():
        try:
            a, b = (int(x) for x in chave.split('-'))
        except (ValueError, AttributeError):
            continue
        if a in ids_servidos and b not in ids_servidos:
            vizinhos[b] = vizinhos.get(b, 0) + peso
        elif b in ids_servidos and a not in ids_servidos:
            vizinhos[a] = vizinhos.get(a, 0) + peso
    if not vizinhos:
        return []
    try:
        import memory_engine as me
        saida = []
        for mid, peso in sorted(vizinhos.items(), key=lambda kv: -kv[1])[:maximo]:
            m = me.buscar_por_id(mid)
            if m:
                saida.append({
                    'id': mid,
                    'titulo': _clean(m.get('task', ''))[:70],
                    'peso': peso,
                })
        return saida
    except Exception:
        return []


def _telemetria_sinapses(contexto):
    """Fase 0 Sinapses Vivas: registra o que foi servido a cada tarefa.
    Fail-soft absoluto: telemetria nunca quebra o contexto."""
    try:
        from pathlib import Path
        from datetime import datetime
        import json as _json
        d = Path(__file__).resolve().parent.parent / 'runtime' / 'sinapses'
        d.mkdir(parents=True, exist_ok=True)
        registro = {
            'ts': datetime.now().isoformat(timespec='seconds'),
            'assunto': (contexto.get('assunto') or '')[:120],
            'projeto': contexto.get('projeto_ativo', ''),
            'criticidade': contexto.get('criticidade', ''),
            'memorias_servidas': [
                {'id': m.get('id'), 'score': m.get('score')}
                for m in contexto.get('memorias', [])
            ],
            'conhecimento_titulos': [c['titulo'][:60] for c in
                                     contexto.get('conhecimento', [])][:4],
            'decisoes_titulos': [d['titulo'][:60] for d in
                                 contexto.get('decisoes', [])][:3],
        }
        with open(d / 'telemetria.jsonl', 'a', encoding='utf-8') as f:
            f.write(_json.dumps(registro, ensure_ascii=False) + '\n')
    except Exception:
        pass


def carregar_contexto(assunto, projeto='', limite=5, incluir_pendencias=True,
                      criticidade=None, registrar=False):
    """Monta o contexto relevante para a tarefa. Nunca carrega tudo."""
    tags = _extrair_tags(assunto)
    projeto_ativo = projeto or _projeto_ativo()

    # Criticidade (usa o Auditor se não for passada)
    if criticidade is None:
        try:
            from runtime_auditor import classificar_criticidade
            criticidade = classificar_criticidade(assunto)
        except Exception:
            criticidade = 'baixa'

    conhecimento_rel = _carregar_conhecimento(assunto, tags, limite)
    memorias_rel = _carregar_memorias(assunto, tags, limite, projeto_ativo)
    contexto = {
        'assunto': assunto,
        'tags_detectadas': tags,
        'projeto_ativo': projeto_ativo,
        'criticidade': criticidade,
        'memorias': memorias_rel,
        'conhecimento': conhecimento_rel,
        'sinapses': _carregar_sinapses(conhecimento_rel),
        'sinapses_dinamicas': _carregar_sinapses_dinamicas(memorias_rel),
        'decisoes': _carregar_decisoes(assunto, tags, max(2, limite // 2)),
        'docs_projeto': _carregar_docs_projeto(projeto_ativo),
        'knowledge_graph': _carregar_knowledge_graph(assunto, tags, limite, projeto_ativo),
        'agentes_sugeridos': _sugerir_agentes(criticidade),
        'pendencias': _carregar_pendencias_runtime() if incluir_pendencias else [],
    }

    _telemetria_sinapses(contexto)

    if registrar:
        try:
            from runtime_state import load_state, save_state
            state = load_state()
            state['loaded_memory'] = (
                [m['titulo'][:60] for m in contexto['memorias'][:4]] +
                [c['titulo'][:60] for c in contexto['conhecimento'][:4]]
            )
            save_state(state)
        except Exception:
            pass
    return contexto


def render(contexto):
    lines = []
    lines.append('=== CONTEXT LOADER (relevante apenas) ===')
    lines.append(f"Assunto: {_clean(contexto['assunto'])}")
    if contexto['tags_detectadas']:
        lines.append(f"Tags:    {', '.join(_clean(t) for t in contexto['tags_detectadas'])}")
    if contexto['projeto_ativo']:
        lines.append(f"Projeto: {_clean(contexto['projeto_ativo'])}")
    lines.append(f"Criticidade: {contexto['criticidade']}")
    if contexto['memorias']:
        lines.append('')
        lines.append('Memórias relevantes:')
        for m in contexto['memorias']:
            proj = f" [{m['projeto']}]" if m['projeto'] else ''
            lines.append(f"  - [{m['tipo']}]{proj} {m['titulo'][:70]} (score {m['score']})")
            lines.append(f"    {m['resumo']}")
    if contexto['conhecimento']:
        lines.append('')
        lines.append('Conhecimento relevante:')
        for c in contexto['conhecimento']:
            lines.append(f"  - {c['titulo'][:80]} (score {c['score']}, {c['fonte']})")
    if contexto.get('sinapses'):
        lines.append('')
        lines.append('Sinapses do grafo (vizinhança das notas):')
        lines.append("")
        for s in contexto['sinapses']:
            lines.append(f"  - {s['nota']} -> conecta: {', '.join(s['conecta'])}")
    if contexto.get('sinapses_dinamicas'):
        lines.append('')
        lines.append('Sinapses vivas (co-uso real, peso):')
        for s in contexto['sinapses_dinamicas']:
            lines.append(f"  - [{s['id']}] {s['titulo']} (peso {s['peso']})")
    if contexto['decisoes']:
        lines.append('')
        lines.append('Decisões consolidadas relacionadas:')
        for d in contexto['decisoes']:
            lines.append(f"  - {d['titulo']}")
    if contexto['docs_projeto']:
        lines.append('')
        lines.append('Documentos do projeto:')
        for d in contexto['docs_projeto']:
            lines.append(f"  - {d['arquivo']}: {d['resumo'][:90]}")
    if contexto.get('knowledge_graph', {}).get('nodes'):
        lines.append('')
        lines.append('Knowledge Graph relevante:')
        for n in contexto['knowledge_graph']['nodes'][:5]:
            lines.append(f"  - [{n['tipo']}] {n['nome']} (tags: {', '.join(n['tags'][:3])})")
            if n['resumo']:
                lines.append(f"    {n['resumo']}")
        if contexto['knowledge_graph']['edges']:
            lines.append('')
            lines.append('  Relações:')
            for e in contexto['knowledge_graph']['edges'][:5]:
                lines.append(f"    {e['origem']} -[{e['tipo']}]-> {e['destino']}")
    if contexto['agentes_sugeridos']:
        lines.append('')
        lines.append(f"Agentes sugeridos ({contexto['criticidade']}): "
                     f"{', '.join(contexto['agentes_sugeridos'])}")
    if contexto['pendencias']:
        lines.append('')
        lines.append('Pendências abertas no Runtime:')
        for p in contexto['pendencias']:
            lines.append(f"  - {p}")
    lines.append('')
    lines.append(f"Carregado: {len(contexto['memorias'])} memórias, "
                 f"{len(contexto['conhecimento'])} conhecimentos, "
                 f"{len(contexto.get('sinapses', []))} sinapses, "
                 f"{len(contexto['decisoes'])} decisões, "
                 f"{len(contexto['docs_projeto'])} documentos. "
                 f"(não carregou a memória inteira)")
    return '\n'.join(_clean(l) for l in lines)


def main():
    parser = argparse.ArgumentParser(description='Context Loader inteligente')
    parser.add_argument('assunto', nargs='*', default=[])
    parser.add_argument('--projeto', default='')
    parser.add_argument('--limite', type=int, default=5)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--registrar', action='store_true',
                        help='registra o que foi carregado no estado do Runtime')
    args = parser.parse_args()

    assunto = ' '.join(args.assunto) or '(sem assunto — contexto geral)'
    contexto = carregar_contexto(assunto, projeto=args.projeto, limite=args.limite,
                                 registrar=args.registrar)
    if args.json:
        print(json.dumps(contexto, ensure_ascii=False, indent=2))
    else:
        print(render(contexto))
    return 0


if __name__ == '__main__':
    sys.exit(main())
