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
import time
from pathlib import Path

import numpy as np

# Silencia logs verbosos do huggingface/sentence-transformers (httpx, download)
# no processo da bridge — mantem o log limpo para diagnósticos reais.
for _mod in ('httpx', 'huggingface_hub', 'sentence_transformers', 'urllib3'):
    try:
        import logging
        logging.getLogger(_mod).setLevel(logging.ERROR)
    except Exception:
        pass

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
    os.path.join(BASE, 'docs'),
    os.path.join(BASE, 'documentos'),
]

# Bônus de domínio aplicado ao score final (relevância de contexto).
# Notas recentes/aprendizados pesam mais que memoria genérica.
DOMAIN_BOOST = {
    'aprendizados': 0.12,
    'docs': 0.10,
    'padroes': 0.08,
    'decisoes': 0.05,
    'notas': 0.03,
    'mem': 0.0,
}

# Contador de acesso por doc (frequência de uso -> boost). Persistido entre execuções.
ACCESS_FILE = os.path.join(MEM_DIR, 'tfidf_acesso.json')

# Modelo de embeddings densos (camada de SIGNIFICADO). Lidera a busca quando
# disponível; TF-IDF atua como complemento. Nunca força download de centenas de MB.
DENSE_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
DENSE_MATRIX_FILE = os.path.join(MEM_DIR, 'dense_matrix.npy')

# Léxico de expansão de query (pt-br, domínio do ecossistema). Transforma a
# consulta em variantes de intenção: "quebrou" -> "quebrou caiu parou falhou".
# Permite recuperar por significado mesmo sem TF-IDF denso.
SINONIMOS = {
    # conectividade / rede
    'ponte': ['bridge', 'conexao', 'ligacao'],
    'caiu': ['quebrou', 'parou', 'falhou', 'cai', 'queda'],
    'reconexao': ['reconectar', 'reconecta', 'voltar', 'retomar'],
    'rede': ['network', 'internet', 'wifi', 'tailscale'],
    'dispositivo': ['celular', 'telefone', 'android', 'phone', 'device'],
    'wifi': ['rede', 'internet', 'conexao', 'sem fio'],
    'tailscale': ['vpn', 'rede', 'malha', 'mesh'],
    # resiliencia
    'resiliencia': ['robustez', 'recuperacao', 'falha', 'failover', 'tolerancia'],
    'watchdog': ['guardiao', 'vigia', 'monitor', 'zelador', 'sentinel'],
    'daemon': ['servico', 'processo', 'background', 'servico'],
    'monitorar': ['observar', 'acompanhar', 'checar', 'verificar', 'monitor'],
    # audio / voz
    'audio': ['voz', 'som', 'tts', 'falado'],
    'voz': ['audio', 'som', 'voz ativa', 'tts'],
    'ouvir': ['escuta', 'audio', 'vad', 'microfone', 'stt'],
    # memoria / conhecimento
    'memoria': ['memorias', 'lembrar', 'relembrar', 'registro', 'historico'],
    'conhecimento': ['notas', 'obsidian', 'saber', 'base', 'aprendizado'],
    'semantica': ['significado', 'sentido', 'busca por significado', 'dense'],
    # etica
    'etica': ['moral', 'conformidade', 'lgpd', 'conformidade', 'privacidade'],
    'preflight': ['checagem', 'verificacao', 'gate', 'check'],
    # dispositivo / adb
    'adb': ['android', 'dispositivo', 'celular', 'conectividade'],
    'tela': ['display', 'screen', 'monitor'],
    'bateria': ['baterias', 'energia', 'carregamento'],
    # app / interface
    'widget': ['grafo', 'interface', 'componente', 'painel'],
    'bug': ['erro', 'falha', 'defeito', 'crash', 'problema'],
    'jarvis': ['jarvis', 'assistente', 'assistente de voz', 'eco'],
    'opencode': ['opencode', 'cli', 'terminal', 'ide'],
}


def expandir_query(query: str) -> str:
    """Expande a query com sinônimos de intenção do ecossistema.

    Ex.: 'a ponte caiu' -> 'a ponte bridge conexao ligacao caiu quebrou parou falhou'.
    """
    palavras = re.findall(r'\w+', query.lower())
    expandidas = set(palavras)
    for p in palavras:
        variantes = SINONIMOS.get(p)
        if variantes:
            expandidas.update(variantes)
    return ' '.join(expandidas)

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


def _nota_data(path: str) -> str:
    """Extrai data da nota no formato YYYY-MM-DD (do filename ou frontmatter).

    Filename de aprendizados: '2026-08-06-saudacoes-...md'. Fallback: mtime.
    """
    base = os.path.basename(path).replace('\ufeff', '')
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', base)
    if m:
        return m.group(1)
    try:
        fm = re.search(r'^---\s*\n(.*?)\n---', open(path, encoding='utf-8', errors='replace').read(), re.S | re.M)
        if fm:
            dm = re.search(r'^\s*data\s*:\s*["\']?(\d{4}-\d{2}-\d{2})', fm.group(1), re.M)
            if dm:
                return dm.group(1)
    except Exception:
        pass
    try:
        import time as _time
        return _time.strftime('%Y-%m-%d', _time.localtime(os.path.getmtime(path)))
    except Exception:
        return ''


def _nota_dominio(rel: str) -> str:
    """Segmento de dominio da nota (aprendizados/docs/padroes/decisoes/notas)."""
    low = rel.lower()
    for key in ('aprendizados', 'docs', 'padroes', 'decisoes'):
        if f'/{key}/' in low or low.startswith(key + '/'):
            return key
    return 'notas'


def _carregar_notas() -> list:
    """Lista de dicts {id, titulo, texto, data, dominio} para todas as notas Obsidian."""
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
                    notas.append({
                        'id': f'nota:{rel}',
                        'titulo': titulo,
                        'texto': texto,
                        'data': _nota_data(path),
                        'dominio': _nota_dominio(rel),
                    })
    return notas


# Idade maxima da camada densa (embeddings) antes de ser reconstruida.
# Reindexar denso a cada add era caro (MiniLM sobre todo o corpus); agora
# so reconstroi apos esse intervalo ou quando a matriz nao existe.
DENSE_MAX_AGE = 600  # 10 min
# Lock anti-concorrencia: impede dois rebuilds densos simultaneos.
DENSE_LOCK_FILE = os.path.join(MEM_DIR, '.dense_rebuild.lock')


def _dense_lock_held() -> bool:
    """True se um rebuild denso esta em andamento (lock recente)."""
    try:
        return os.path.exists(DENSE_LOCK_FILE) and \
            (time.time() - os.path.getmtime(DENSE_LOCK_FILE)) < DENSE_MAX_AGE
    except Exception:
        return os.path.exists(DENSE_LOCK_FILE)


def _index_fingerprint(mem_count: int | None = None):
    """Fingerprint leve do corpus (count memorias + mtimes das notas).

    Usado para detectar se o indice TF-IDF esta desatualizado sem reindexar
    tudo. Barato: so conta memorias e faz stat de arquivos .md.
    """
    if mem_count is None:
        mem_count = 0
        if os.path.exists(MEMORIES_FILE):
            try:
                with open(MEMORIES_FILE, encoding='utf-8') as f:
                    mem_count = len(json.load(f))
            except Exception:
                mem_count = 0
    notas_fp = []
    for d in NOTAS_DIRS:
        newest = 0.0
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for fn in files:
                    if fn.endswith('.md'):
                        try:
                            newest = max(newest, os.path.getmtime(os.path.join(root, fn)))
                        except Exception:
                            pass
        notas_fp.append(round(newest, 1))
    # Retorna lista (nao tupla): JSON serializa tupla como lista, e a comparacao
    # em index_stale() falharia sempre (list != tuple), forçando rebuild a cada add.
    return [mem_count, notas_fp]


def index_stale() -> bool:
    """True se o indice TF-IDF nao reflete o corpus atual (memorias + notas)."""
    try:
        with open(META_FILE, encoding='utf-8') as f:
            meta = json.load(f)
        return meta.get('fingerprint') != _index_fingerprint()
    except Exception:
        return True


def _dense_recente() -> bool:
    """True se a matriz densa existe e foi construida ha menos de DENSE_MAX_AGE."""
    if not os.path.exists(DENSE_MATRIX_FILE):
        return False
    try:
        return (time.time() - os.path.getmtime(DENSE_MATRIX_FILE)) < DENSE_MAX_AGE
    except Exception:
        return False


def build_index(verbose: bool = False) -> dict:
    """Constroi (ou reconstrroi) o indice TF-IDF a partir de memories.json."""
    global _CACHE
    _CACHE = None
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
        nota_meta[n['id']] = {'titulo': n['titulo'],
                              'data': n.get('data', ''),
                              'dominio': n.get('dominio', 'notas')}

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
        'fingerprint': _index_fingerprint(len(memories)),
    }
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Embeddings depend do mesmo corpus; a matriz antiga nao pode ser usada
    # enquanto o rebuild denso nao termina.
    try:
        os.remove(DENSE_MATRIX_FILE)
    except FileNotFoundError:
        pass

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
        dense = None
        dense_model = None
        if not os.path.exists(DENSE_MATRIX_FILE):
            # Tenta construir a camada densa uma vez (best-effort, nunca bloqueia
            # a busca se o modelo estiver indisponível). Tempo total de download
            # NUNCA é forçado: build_dense() só usa modelo em cache.
            build_dense(verbose=False)
        if os.path.exists(DENSE_MATRIX_FILE):
            try:
                dense = np.load(DENSE_MATRIX_FILE)
                from sentence_transformers import SentenceTransformer
                dense_model = SentenceTransformer(DENSE_MODEL, local_files_only=True)
            except Exception:
                dense = None
                dense_model = None
        _CACHE = {
            'matrix': load_npz(MATRIX_FILE),
            'meta': meta,
            'vectorizer': vectorizer,
            'mem_by_id': {m['id']: m for m in memories},
            'cosine': cosine_similarity,
            'acesso': _carregar_acesso(),
            'dense': dense,
            'dense_model': dense_model,
        }

    c = _CACHE
    q_expandida = expandir_query(query)
    q_vec = c['vectorizer'].transform([q_expandida])
    sims = c['cosine'](q_vec, c['matrix']).flatten()
    # Camada densa (embeddings de SIGNIFICADO) — lidera a busca quando disponível.
    denso = None
    if c.get('dense') is not None and c.get('dense_model') is not None \
            and len(c['dense']) == len(c['meta']['ids']):
        try:
            q_emb = c['dense_model'].encode([query], normalize_embeddings=True)
            dsims = np.dot(q_emb, c['dense'].T).flatten()
            # Cosine ja e uma medida absoluta; nao normalizar pelo maximo da
            # propria consulta, pois isso transforma falso positivo em top-1.
            dsims = np.clip(dsims, 0.0, 1.0)
            denso = dsims
        except Exception:
            denso = None

    if denso is not None:
        # Denso lidera (0.65) — captura significado; TF-IDF com expansão complementa
        # (0.35) para palavras-chave exatas. Peso denso domina quando há contexto.
        sims = 0.35 * sims + 0.65 * denso

    idx_sorted = np.argsort(sims)[::-1]
    results = []
    seen_ids = set()
    for idx in idx_sorted:
        score = float(sims[idx])
        if score < min_score:
            break
        doc_id = c['meta']['ids'][idx]
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)
        kind = c['meta']['kinds'][idx]
        # Bônus de recência + domínio + acesso sobre o score TF-IDF.
        bonus = 0.0
        if kind == 'nota':
            info = c['meta'].get('notas', {}).get(doc_id, {})
            bonus = _boost_recencia(info.get('data', '')) \
                + DOMAIN_BOOST.get(info.get('dominio', 'notas'), 0.03) \
                + _boost_acesso(doc_id, c['acesso'])
        else:
            bonus = DOMAIN_BOOST.get('mem', 0.0) + _boost_acesso(doc_id, c['acesso'])
        final_score = score + bonus
        if kind == 'nota':
            info = c['meta'].get('notas', {}).get(doc_id, {})
            results.append({
                'id': doc_id,
                'kind': 'nota',
                'source': 'nota',
                'score': round(final_score, 4),
                'base': round(score, 4),
                'title': info.get('titulo', doc_id)[:120],
                'summary': '',
            })
        else:
            mem = c['mem_by_id'].get(doc_id)
            if mem and not mem.get('archived', False):
                titulo = mem.get('title', '') or mem.get('summary', mem.get('resumo', ''))
                results.append({
                    'id': doc_id,
                    'kind': kind,
                    'source': 'mem',
                    'score': round(final_score, 4),
                    'base': round(score, 4),
                    'title': titulo[:120],
                    'summary': mem.get('summary', mem.get('resumo', '')),
                })

    # Ranking final pelo score ponderado.
    results.sort(key=lambda r: r['score'], reverse=True)

    # Registra acesso dos docs retornados (persistido para reforçar frequência).
    for r in results[:k]:
        c['acesso'][r['id']] = c['acesso'].get(r['id'], 0) + 1
    _salvar_acesso(c['acesso'])

    return results[:k]


def cli_main(argv):
    if not argv:
        print('uso: memory_semantic.py [build|search <query>]')
        return 1
    cmd = argv[0]
    if cmd == 'build':
        r = build_index(verbose=True)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get('ok') else 1
    if cmd == 'build-dense':
        r = build_dense(verbose=True)
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


def _carregar_acesso() -> dict:
    """Carrega o contador de acesso por doc (doc_id -> n)."""
    try:
        with open(ACCESS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_acesso(acesso: dict) -> None:
    try:
        with open(ACCESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(acesso, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _boost_acesso(doc_id: str, acesso: dict) -> float:
    """Boost por frequencia de uso: quanto mais consultado, maior (limitado a +0.1)."""
    return min(acesso.get(doc_id, 0), 10) * 0.01


def _boost_recencia(data: str, dias_meia_vida: float = 60.0) -> float:
    """Boost por recencia: notas recentes pesam mais (decai exponencialmente).

    Bônus max ~0.15 hoje, metade disso em ~60 dias, ~0 depois de ~6 meses.
    """
    if not data:
        return 0.0
    try:
        from datetime import date
        y, mo, d = map(int, data.split('-'))
        delta = (date.today() - date(y, mo, d)).days
        if delta < 0:
            delta = 0
        return 0.15 * (0.5 ** (delta / dias_meia_vida))
    except Exception:
        return 0.0


def _dense_disponivel() -> bool:
    """True se a camada densa ja foi construida (matriz em disco)."""
    return os.path.exists(DENSE_MATRIX_FILE)


def build_dense(verbose: bool = False) -> dict:
    """(Opcional) Constrói embeddings densos das memórias + notas.

    Só roda se o modelo de sentence-transformers já estiver em cache local —
    nunca força download (local_files_only=True). Se não estiver, retorna
    ok=False sem erro fatal. Lock impede rebuilds concorrentes.
    """
    if _dense_lock_held():
        if verbose:
            print('[semantic] dense: rebuild ja em andamento (lock)')
        return {'ok': False, 'erro': 'rebuild denso ja em andamento'}
    try:
        open(DENSE_LOCK_FILE, 'w', encoding="utf-8").close()
    except Exception:
        pass
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        with open(META_FILE, encoding='utf-8') as f:
            meta = json.load(f)
        # local_files_only: NUNCA faz download do HuggingFace. Se o modelo nao
        # estiver em cache local, falha rapido e retorna ok=False (best-effort).
        model = SentenceTransformer(DENSE_MODEL, local_files_only=True)
        emb = model.encode(meta['texts'], show_progress_bar=False, normalize_embeddings=True)
        np.save(DENSE_MATRIX_FILE, np.asarray(emb))
        if verbose:
            print(f'[semantic] dense: {len(meta["texts"])} docs | {DENSE_MODEL}')
        return {'ok': True, 'count': len(meta['texts'])}
    except Exception as e:
        if verbose:
            print(f'[semantic] dense indisponivel: {e}')
        return {'ok': False, 'erro': str(e)}
    finally:
        try:
            os.remove(DENSE_LOCK_FILE)
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(cli_main(sys.argv[1:]))
