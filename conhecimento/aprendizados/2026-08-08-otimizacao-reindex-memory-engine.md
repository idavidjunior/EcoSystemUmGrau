---
tipo: padrao
tags: [memory-engine, reindex, semantico, huggingface, desempenho, tfidf, dense, sentencetransformers]
data: 2026-08-08
contexto: memory_engine.py add travava >120s (timeout) baixando modelo do HuggingFace a cada reindexação
decisao: TF-IDF no add (rápido) + camada densa (MiniLM) em subprocesso background com lock e local_files_only
impacto: add caiu de 120s+ para ~6-9s; sem downloads silenciosos; dense atualizado a cada ~10min em background
---

# Otimização do reindex semântico do Memory Engine

## Sintoma
`python scripts/memory_engine.py add ...` travava (>120s) exibindo barra de
download de pesos do HuggingFace ("Loading weights"). A cada `add`, o
`reindexar_semantico` reconstruía TF-IDF **e** a camada densa
(`build_dense`) — que instancia `SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')`
e **baixava ~470MB** do Hub na primeira execução. Mesmo com modelo em cache,
re-embedding de 681 docs (MiniLM) no CPU leva >2min — bloqueando o add.

## Causa raiz
1. `build_dense` não tinha `local_files_only` — o comentário dizia "nunca força
   download", mas `SentenceTransformer(DENSE_MODEL)` baixa do HF Hub se não estiver no cache.
2. `add_memory` chamava `reindexar_semantico` que reconstruía TUDO (TF-IDF + denso)
   a cada adição, sem checagem de desatualização nem debounce.

## Correção aplicada
- **`memory_semantic.py`:**
  - `build_dense` agora usa `SentenceTransformer(DENSE_MODEL, local_files_only=True)`
    → nunca baixa; falha rápido (`ok=False`) se o modelo não está em cache local.
  - `local_files_only=True` também na carga do modelo em `search()`.
  - Novo `index_stale()` baseado em **fingerprint** (count de memórias + mtimes
    das notas) → pula rebuild se o índice já reflete o corpus.
  - Lock anti-concorrência (`.dense_rebuild.lock`) impede rebuilds densos simultâneos.
  - `DENSE_MAX_AGE = 600` (10min) — denso só reconstrói se velho/ausente.
  - Novo comando CLI: `memory_semantic.py build-dense` (para rebuild manual/agendado).
- **`memory_engine.py`:**
  - `reindexar_semantico`: TF-IDF (rápido, ~1-2s) quando stale; camada densa
    disparada em **subprocesso destacado** (`subprocess.Popen` + `DETACHED_PROCESS`)
    que roda `memory_semantic.py build-dense` em background — o `add` não espera.

## Resultados medidos
- Antes: `add` >120s (timeout, download HF).
- Depois: `add` ~6-9s (exit 0), índice atualizado, sem download, sem lock residual.
- Busca semântica funcionando (TF-IDF + denso + expansão de sinônimos).

## Lições
- Sempre validar comentários de código contra o comportamento real (o "nunca força
  download" era falso).
- Operações de ML pesadas (embedding de corpus inteiro) nunca devem bloquear o
  caminho crítico — subprocesso background + lock é o padrão.
- `TOKENIZERS_PARALLELISM=false` evita warnings/hang de tokenizers no Windows.
- Fingerprint (count + mtime) é barato e suficiente para detectar índice stale.
