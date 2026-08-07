"""Indexacao semantica do Memory Engine via TF-IDF + cosine similarity.

Resolve o gargalo de 84+ memorias sem recuperacao por significado: so tinhamos
index por tags exatas. Agora search(query) retorna as memorias mais semanticamente
proximas, nao as que compartilham palavras-chave identicas.

Desde 2026-08-07 o indice tambem inclui as notas Obsidian (conhecimento/notas/ e
conhecimento/aprendizados/), com source='nota' — o Jarvis recupera conhecimento
das notas por significado, nao so memorias.

Arquivos gerados em conhecimento/memoria/:
  - tfidf_matrix.npz   (matriz esparsa TF-IDF das memorias + notas)
  - tfidf_meta.json    (ids, kinds, textos indexados, vocab, notas)
  - tfidf_vectorizer.pkl (vectorizer serializado)
"""
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

BASE = str(Path(__file__).resolve().parent.parent)
MEM_DIR = os.path.join(BASE, 'conhecimento', 'memoria')
MEMORIES_FILE = os.path.join(MEM_DIR, 'memories.json')
MATRIX_FILE = os.path.join(MEM_DIR, 'tfidf_matrix.npz')
META_FILE = os.path.join(MEM_DIR, 'tfidf_meta.json')
VECTORIZER_FILE = os.path.join(MEM_DIR, 'tfidf_vectorizer.pkl')

# Diretorios de notas Obsidian que entram no indice semantico.
NOTAS_DIRS = [
    os.path.join(BASE, 'conhecimento', 'notas'),
    os.path.join(BASE, 'conhecimento', 'aprendizados'),
]

# Cache estatico (carregado uma vez por processo; cold ~10s, quente <50ms).
_CACHE = None


def _corpus_text(memory: dict) -> str:
    """Concatena titulo + resumo + tags em um unico documento indexavel."""
    parts = [
        memory.get('title', ''),
        memory.get('summary', memory.get('resumo', '')),
        ' '.join(memory.get('tags', []) or []),
        memory.get('kind', ''),
    ]
    return ' '.join(p for p in parts if p).strip().lower()


def _frontmatter_tags(text: str) -> list:
    """Extrai as tags do frontmatter YAML (linhas 'tags: [...]')."""
    m = re.search(r'^---\s*\n(.*?)\n---', text, re.S | re.M)
    if not m:
        return []
    fm = m.group(1)
    tm = re.search(r'^\s*tags\s*:\s*\[(.*?)\]', fm, re.M)
    if tm:
        return [t.strip().strip('"\'') for t in tm.group(1).split(',') if t.strip()]
    return []


def _nota_texto(path: str) -> tuple:
    """Extrai (titulo, texto_indexavel) de uma nota Obsidian.

    Indexa: titulo + tags do frontmatter + corpo (ate 2500 chars).
    """
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return '', ''
    base = os.path.splitext(os.path.basename(path))[0]
    title = base.replace('\ufeff', '').strip()
    # Titulo do primeiro heading '#' se existir e for legivel.
    hm = re.search(r'^#\s+(.+)$', content, re.M)
    if hm:
        t = hm.group(1).strip().replace('\ufeff', '')
        if len(t) < 200:
            title = t
    tags = ' '.join(_frontmatter_tags(content))
    corpo = re.sub(r'^---.*?---', '', content, flags=re.S | re.M)
    corpo = re.sub(r'[#*`\[\]]', ' ', corpo)
    return title, f'{title} {tags} {corpo[:2500]}'.strip().lower()


def _carregar_notas() -> list:
    """Lista de dicts {id, titulo, texto} para todas as notas Obsidian."""
    notas = []
    seen = set()
    for d in NOTAS_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for fname in sorted(files):
                if not fname.endswith('.md'):
                    continue
                path = os.path.join(root, fname)
                rel = os.path.relpath(path, BASE).replace('\\', '/')
                if rel in seen:
                    continue
                seen.add(rel)
                titulo, texto = _nota_texto(path)
                if texto:
                    notas.append({'id': f'nota:{rel}', 'titulo': titulo, 'texto': texto})
    return notas


def build_index(verbose: bool = False) -> dict:
    """Constroi (ou reconstrroi) o indice TF-IDF a partir de memories.json."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import pickle

    if not os.path.exists(MEMORIES_FILE):
        return {'ok': False, 'erro': 'memories.json ausente', 'count': 0}

    with open(MEMORIES_FILE, encoding='utf-8') as f:
        memories = json.load(f)

    notas = _carregar_notas()

    if not memories and not notas:
        return {'ok': False, 'erro': 'sem memorias nem notas para indexar', 'count': 0}

    corresp_ids = [m['id'] for m in memories]
    corresp_kinds = [m.get('kind', 'episodio') for m in memories]
    corpus = [_corpus_text(m) for m in memories]

    nota_meta = {}
    for n in notas:
        corresp_ids.append(n['id'])
        corresp_kinds.append('nota')
        corpus.append(n['texto'])
        nota_meta[n['id']] = {'titulo': n['titulo']}

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.9,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(corpus)

    # matiz esparsa persistida
    from scipy.sparse import save_npz
    save_npz(MATRIX_FILE, matrix)

    with open(VECTORIZER_FILE, 'wb') as f:
        pickle.dump(vectorizer, f)

    meta = {
        'ids': corresp_ids,
        'kinds': corresp_kinds,
        'texts': corpus,
        'notas': nota_meta,
        'vocab_size': len(vectorizer.vocabulary_),
        'count': len(corresp_ids),
        'count_mem': len(memories),
        'count_notas': len(notas),
    }
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f'[semantic] {len(memories)} memorias + {len(notas)} notas indexadas | '
              f'vocab={len(vectorizer.vocabulary_)}')
    return {'ok': True, 'count': len(corresp_ids),
            'vocab_size': len(vectorizer.vocabulary_)}


def search(query: str, k: int = 5, min_score: float = 0.05) -> list:
    """Retorna as top-k memorias mais similares a query (por cosseno).

    Usa cache estatico (_CACHE) para carregar vectorizer/matrix/memories uma
    unica vez por processo (essencial: o cold-load leva ~10s, quente <50ms).

    Returns:
        [{'id', 'kind', 'score', 'title'}, ...] decrescente por score.
    """
    global _CACHE
    if _CACHE is None:
        from sklearn.metrics.pairwise import cosine_similarity
        import pickle
        if not os.path.exists(MATRIX_FILE) or not os.path.exists(META_FILE) \
                or not os.path.exists(VECTORIZER_FILE):
            build_index(verbose=False)
        if not all(os.path.exists(p) for p in [MATRIX_FILE, META_FILE, VECTORIZER_FILE]):
            return []
        from scipy.sparse import load_npz
        with open(META_FILE, encoding='utf-8') as f:
            meta = json.load(f)
        with open(VECTORIZER_FILE, 'rb') as f:
            vectorizer = pickle.load(f)
        with open(MEMORIES_FILE, encoding='utf-8') as f:
            memories = json.load(f)
        _CACHE = {
            'matrix': load_npz(MATRIX_FILE),
            'meta': meta,
            'vectorizer': vectorizer,
            'mem_by_id': {m['id']: m for m in memories},
            'cosine': cosine_similarity,
        }

    c = _CACHE
    q_vec = c['vectorizer'].transform([query.lower()])
    sims = c['cosine'](q_vec, c['matrix']).flatten()

    idx_sorted = np.argsort(sims)[::-1]
    results = []
    for idx in idx_sorted[:k * 3]:
        score = float(sims[idx])
        if score < min_score:
            break
        doc_id = c['meta']['ids'][idx]
        kind = c['meta']['kinds'][idx]
        if kind == 'nota':
            info = c['meta'].get('notas', {}).get(doc_id, {})
            results.append({
                'id': doc_id,
                'kind': 'nota',
                'source': 'nota',
                'score': round(score, 4),
                'title': info.get('titulo', doc_id)[:120],
                'summary': '',
            })
        else:
            mem = c['mem_by_id'].get(doc_id)
            if mem:
                titulo = mem.get('title', '') or mem.get('summary', mem.get('resumo', ''))
                results.append({
                    'id': doc_id,
                    'kind': kind,
                    'source': 'mem',
                    'score': round(score, 4),
                    'title': titulo[:120],
                    'summary': mem.get('summary', mem.get('resumo', '')),
                })
        if len(results) >= k:
            break
    return results


def cli_main(argv):
    if not argv:
        print('uso: memory_semantic.py [build|search <query>]')
        return 1
    cmd = argv[0]
    if cmd == 'build':
        r = build_index(verbose=True)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get('ok') else 1
    if cmd == 'search':
        if len(argv) < 2:
            print('uso: memory_semantic.py search <query>')
            return 1
        query = ' '.join(argv[1:])
        results = search(query, k=5)
        if not results:
            print('sem resultados (indice vazio ou nao construido)')
            return 0
        for r in results:
            print(f"  [{r['score']:.4f}] #{r['id']} ({r['kind']}) {r['title']}")
        return 0
    print(f'comando desconhecido: {cmd}')
    return 1


if __name__ == '__main__':
    sys.exit(cli_main(sys.argv[1:]))
