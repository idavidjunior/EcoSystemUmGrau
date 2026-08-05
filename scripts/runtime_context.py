"""Context Loader inteligente do Ecossistema.

NUNCA carrega toda a memória. Antes de cada tarefa, identifica o assunto
tratado pelo usuário e carrega apenas os documentos, memórias e conhecimentos
relevantes para aquela execução — reduzindo consumo de contexto e aumentando
precisão.

Uso CLI:
  python scripts/runtime_context.py "<objetivo/assunto>"   # carrega contexto relevante
  python scripts/runtime_context.py --projeto <nome> "<assunto>"
  python scripts/runtime_context.py --limite <N> "<assunto>"
"""

import argparse
import json
import os
import re
import sys

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

_BOM = '\ufeff'

def _clean(s):
    return (s or '').replace(_BOM, '')


def _extrair_tags(texto, max_tags=6):
    """Extrai tags semânticas do assunto (RAKE leve)."""
    try:
        from semantic_tags import extrair_tags
        return extrair_tags(texto, max_tags=max_tags) or []
    except Exception:
        return []


def _carregar_memorias(assunto, tags, limite):
    """Carrega memórias relevantes (reforço de relevância do memory_engine)."""
    try:
        import memory_engine
        mems = memory_engine.query(text=assunto, tags=tags[:4], limit=limite)
        result = []
        for m in mems:
            result.append({
                'tipo': m['kind'],
                'titulo': _clean(m['task']),
                'resumo': _clean(m['summary'])[:160],
                'projeto': _clean(m.get('project', '')),
            })
        return result
    except Exception:
        return []


def _carregar_conhecimento(assunto, limite):
    """Carrega entradas relevantes do conhecimento (BM25 fusion)."""
    try:
        ksearch = os.path.join(BASE, 'mcp', 'memoria', 'habilidades',
                               'busca-conhecimento', 'search_knowledge.py')
        if os.path.exists(ksearch):
            sys.path.insert(0, os.path.dirname(ksearch))
            import search_knowledge as sk
            docs = sk.load_corpus()
            results = sk.bm25(assunto, docs)
            out = []
            for score, doc_id, text in results[:limite]:
                if score < 0.1:
                    break
                kind = doc_id.split(':')[0]
                title = doc_id.split(':', 1)[1] if ':' in doc_id else doc_id
                out.append({
                    'fonte': kind,
                    'titulo': title[:80],
                    'score': round(score, 3),
                })
            return out
    except Exception:
        pass
    return []


def _carregar_decisoes(assunto, limite):
    """Carrega decisões consolidadas relacionadas (nunca contrariar sem justificativa)."""
    try:
        import memory_engine
        mems = memory_engine.query(kind='decisao', text=assunto, limit=limite)
        return [{'titulo': m['task'][:80], 'resumo': m['summary'][:120]}
                for m in mems]
    except Exception:
        return []


def _carregar_pendencias_runtime():
    """Carrega pendências abertas do estado do Runtime."""
    try:
        from runtime_state import load_state
        state = load_state()
        pends = [p for p in state.get('pending', []) if not p.get('done')]
        return [f"#{p['id']} {p['text']}" for p in pends]
    except Exception:
        return []


def carregar_contexto(assunto, projeto='', limite=5, incluir_pendencias=True):
    """Monta o contexto relevante para a tarefa. Nunca carrega tudo."""
    tags = _extrair_tags(assunto)
    contexto = {
        'assunto': assunto,
        'tags_detectadas': tags,
        'memorias': _carregar_memorias(assunto, tags, limite),
        'conhecimento': _carregar_conhecimento(assunto, limite),
        'decisoes': _carregar_decisoes(assunto, max(2, limite // 2)),
        'pendencias': _carregar_pendencias_runtime() if incluir_pendencias else [],
        'projeto_filtro': projeto,
    }
    return contexto


def render(contexto):
    lines = []
    lines.append('=== CONTEXT LOADER (relevante apenas) ===')
    lines.append(f"Assunto: {_clean(contexto['assunto'])}")
    if contexto['tags_detectadas']:
        lines.append(f"Tags:    {', '.join(_clean(t) for t in contexto['tags_detectadas'])}")
    if contexto['projeto_filtro']:
        lines.append(f"Projeto: {_clean(contexto['projeto_filtro'])}")
    if contexto['memorias']:
        lines.append('')
        lines.append('Memórias relevantes:')
        for m in contexto['memorias']:
            proj = f" [{m['projeto']}]" if m['projeto'] else ''
            lines.append(f"  - [{m['tipo']}]{proj} {m['titulo'][:70]}")
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
    if contexto['pendencias']:
        lines.append('')
        lines.append('Pendências abertas no Runtime:')
        for p in contexto['pendencias']:
            lines.append(f"  - {p}")
    lines.append('')
    lines.append(f"Carregado: {len(contexto['memorias'])} memórias, "
                 f"{len(contexto['conhecimento'])} conhecimentos, "
                 f"{len(contexto['decisoes'])} decisões. "
                 f"(não carregou a memória inteira)")
    return '\n'.join(_clean(l) for l in lines)


def main():
    parser = argparse.ArgumentParser(description='Context Loader inteligente')
    parser.add_argument('assunto', nargs='*', default=[])
    parser.add_argument('--projeto', default='')
    parser.add_argument('--limite', type=int, default=5)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    assunto = ' '.join(args.assunto) or '(sem assunto — contexto geral)'
    contexto = carregar_contexto(assunto, projeto=args.projeto, limite=args.limite)
    if args.json:
        print(json.dumps(contexto, ensure_ascii=False, indent=2))
    else:
        print(render(contexto))
    return 0


if __name__ == '__main__':
    sys.exit(main())
