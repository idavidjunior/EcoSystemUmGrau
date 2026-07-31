"""Semantic search: BM25 lexical + tag graph fusion over knowledge graph."""
import json, os, re, sys, math
from collections import Counter
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
LER_DIR = os.path.join(BASE, 'ler-runtime')
NOTAS_DIR = os.path.join(BASE, 'conhecimento', 'notas')
MEM_DIR = os.path.join(BASE, 'conhecimento', 'memoria')

def tokenize(text):
    return re.findall(r'[a-zA-Z\u00C0-\u024F]+|\d+', text.lower())

def bm25(query, docs, k1=1.5, b=0.75):
    """BM25 scoring. docs = [(id, text), ...]"""
    q_tokens = tokenize(query)
    if not q_tokens:
        return []
    N = len(docs)
    avgdl = sum(len(tokenize(d)) for _, d in docs) / max(N, 1)
    idf = {}
    for qt in set(q_tokens):
        n = sum(1 for _, d in docs if qt in tokenize(d))
        idf[qt] = math.log((N - n + 0.5) / (n + 0.5) + 1)

    scored = []
    for doc_id, text in docs:
        tokens = tokenize(text)
        dl = len(tokens)
        tf = Counter(tokens)
        score = 0
        for qt in q_tokens:
            if qt in tf:
                score += idf.get(qt, 0) * (tf[qt] * (k1 + 1)) / (tf[qt] + k1 * (1 - b + b * dl / avgdl))
        scored.append((score, doc_id, text))
    scored.sort(key=lambda x: -x[0])
    return scored[:20]

def load_corpus():
    """Build search corpus from knowledge graph + memory + notes."""
    docs = []
    # Knowledge graph
    kg_path = os.path.join(LER_DIR, 'knowledge', 'knowledge_graph.json')
    if os.path.exists(kg_path):
        with open(kg_path, encoding='utf-8') as f:
            g = json.load(f)
        for cat in ['patterns', 'decisions', 'bug_fixes', 'cognitive_patterns', 'heuristics', 'frameworks']:
            for item in g.get(cat, []):
                text = json.dumps(item, ensure_ascii=False)
                title = item.get('title', item.get('decision', item.get('name', '')))
                docs.append((f'kg:{cat}/{title[:40]}', text[:2000]))

    # Memories
    mem_path = os.path.join(MEM_DIR, 'memories.json')
    if os.path.exists(mem_path):
        with open(mem_path, encoding='utf-8') as f:
            for m in json.load(f):
                text = f"{m.get('task','')} {m.get('summary','')} {m.get('project','')} {' '.join(m.get('tags',[]))}"
                docs.append((f'mem:{m["id"]}', text))

    # Notas Obsidian
    if os.path.exists(NOTAS_DIR):
        for root, _, files in os.walk(NOTAS_DIR):
            for fname in files:
                if fname.endswith('.md'):
                    path = os.path.join(root, fname)
                    with open(path, encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    title = os.path.splitext(fname)[0]
                    docs.append((f'nota:{title}', content[:2000]))

    return docs

if __name__ == '__main__':
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
    if not query:
        print('Uso: python scripts/search_knowledge.py <termo>')
        sys.exit(1)

    docs = load_corpus()
    results = bm25(query, docs)

    if not results:
        print(f'Sem resultados para: {query}')
        sys.exit(0)

    print(f'--- Resultados para: {query} ---')
    for score, doc_id, text in results[:10]:
        if score < 0.1: break
        kind = doc_id.split(':')[0]
        title = doc_id.split(':', 1)[1] if ':' in doc_id else doc_id
        preview = text[:150].replace('\n', ' ')
        print(f'  [{score:.2f}] ({kind}) {title[:60]}')
        print(f'           {preview}...')
