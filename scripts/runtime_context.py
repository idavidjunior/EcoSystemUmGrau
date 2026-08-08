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


def _carregar_pendencias_runtime():
    try:
        from runtime_state import load_state
        state = load_state()
        pends = [p for p in state.get('pending', []) if not p.get('done')]
        return [f"#{p['id']} {p['text']}" for p in pends]
    except Exception:
        return []


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

    contexto = {
        'assunto': assunto,
        'tags_detectadas': tags,
        'projeto_ativo': projeto_ativo,
        'criticidade': criticidade,
        'memorias': _carregar_memorias(assunto, tags, limite, projeto_ativo),
        'conhecimento': _carregar_conhecimento(assunto, tags, limite),
        'decisoes': _carregar_decisoes(assunto, tags, max(2, limite // 2)),
        'docs_projeto': _carregar_docs_projeto(projeto_ativo),
        'agentes_sugeridos': _sugerir_agentes(criticidade),
        'pendencias': _carregar_pendencias_runtime() if incluir_pendencias else [],
    }

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
