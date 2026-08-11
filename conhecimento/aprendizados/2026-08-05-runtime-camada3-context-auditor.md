---
tipo: padrao
tags: [runtime, context-loader, auditor, pipeline, arquitetura]
data: 2026-08-05
contexto: Transformar o Ecossistema Jarvis em Runtime de IA persistente. Camada 3: Context Loader inteligente + Auditor adaptativo.
decisao: Criar scripts/runtime_context.py (BM25, carrega so o relevante) e scripts/runtime_auditor.py (classifica criticidade, audita com profundidade proporcional).
impacto: Menor consumo de contexto, maior precisao. Respostas criticas passam por auditoria completa antes de entregar.
---

# Runtime Persistente — Camada 3: Context Loader + Auditor (2026-08-05)

## Contexto
Camadas 1 (estado+boot) e 2 (Kernel+Constituição) prontas. Agora o Context
Loader (nunca carregar tudo) e o Auditor adaptativo (profundidade por
criticidade).

## Decisão de Arquitetura
- **`scripts/runtime_context.py`** — Context Loader inteligente:
  - Extrai tags do assunto (RAKE leve via `semantic_tags`).
  - `_carregar_memorias`: `memory_engine.query(text=assunto, tags=...)`.
  - `_carregar_conhecimento`: BM25 fusion via `search_knowledge.load_corpus()`
    + `bm25()` (usa as funções reais do módulo — NÃO existe função `search()`).
  - `_carregar_decisoes`: decisões consolidadas relacionadas (para a regra
    "nunca contrariar decisão sem justificativa").
  - `_carregar_pendencias_runtime`: pendências abertas do estado.
  - Nunca carrega a memória inteira — só o relevante. Flags: `--projeto`,
    `--limite`, `--json`.
- **`scripts/runtime_auditor.py`** — Auditor adaptativo:
  - `classificar_criticidade(objetivo)`: baixa/media/alta por marcadores
    (arquitetura, segurança, deploy, produção, migração → alta; explicar,
    pergunta, dúvida → baixa).
  - `auditar(resposta, objetivo, criticidade, kernel_rules, decisoes)`:
    resposta presente, aderência ao objetivo (tolerante a flexões via
    prefixo/substring), regras do Kernel, auditoria completa (próximos passos +
    verificações) só em criticidade média/alta.
  - Retorna (aprovado, relatório, falhas). Reprovação = ciclo deve repetir
    (Executar → Validar → Corrigir → Validar → Responder).
- **Bootloader** — checklist de integridade agora valida os 5 módulos do
  runtime (state, kernel, context, auditor, memory). Relatório exibe módulos
  disponíveis.
- **Maestro** — pipeline completo: Kernel → Context Loader → Auditor antes de
  entregar.

## Validação
- Context Loader: `"aplicativo Android Kotlin com SQLite"` → 5 conhecimentos
  relevantes (BM25), 0 memórias irrelevantes, pendências carregadas. Não
  carregou a memória inteira.
- Auditor: "explicar lista em python" → baixa; "refatorar arquitetura com
  migração + deploy" → alta. Resposta fraca em criticidade alta → REPROVADO
  (exit 1). Resposta com validação+justificativa+próximos passos → APROVADO.
- `preflight_check.py`: TODOS TESTES PASSARAM.

## Lições
- **BOM `\ufeff` em conteúdo vindo de memories.json quebra o console cp1252**
  (UnicodeEncodeError). Sanitizar com `_clean()` (remover BOM) e forçar
  `PYTHONIOENCODING=utf-8`.
- **`search_knowledge.py` não tem `search()`** — expõe só `load_corpus()` e
  `bm25(query, docs)` retornando `(score, doc_id, text)`. Usar essas funções.
- Heurística de aderência ao objetivo precisa ser **tolerante a flexões**
  (refatorar vs Refatoracao) — usar prefixo de 5 chars ou substring.

## Próximos passos (camada 4)
- Camada de adaptação multi-LLM (provider-agnostic) — LLM como motor
  substituível.
- Validador formal de saída + orquestração unificada (boot completo de uma vez).

## Conexoes

- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[cluster-hub-programacao]]