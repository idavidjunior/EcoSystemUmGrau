---
tags: [dizia, estiver, força, opencode, padrao, true]
aliases: [Otimização do reindex semântico do Memory Engine]
date: 2026-08-08
---

# Otimização do reindex semântico do Memory Engine

**Fonte:** opencode

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
    → nunca baixa; falha rápido (`ok=False`) se o modelo não está
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]