---
tags: [filtro, opencodeopencode, outer, padrao, query, tradução]
aliases: [Como adicionar uma nova versão da Bíblia ao BibliaEstudoComp]
date: 2026-08-20
---

# Como adicionar uma nova versão da Bíblia ao BibliaEstudoCompleta

**Fonte:** opencode+opencode

Pipeline completo validado na adição da ALM1911 (domínio público) junto à ARC (SBB licenciada).

## 1. Origem dos dados

- Formato aceito: JSON com lista de livros contendo `abbrev` e `chapters` (arrays de versículos).
- Fontes: repositório damarals/biblias no GitHub releases (ALM1911.json, 4MB, 66 livros canônicos).
- Regra de licença: versões licenciadas (ARC/SBB) NÃO podem ser redistribuídas; versões de domínio público (ALM1911) podem.

## 2. Schema do banco (assets/databases/biblia_estudo.db)

- Tabela `verses`: coluna `translation_id TEXT NOT NULL DEFAULT 'arc'`.
- Constraint UNIQUE: `(book_id, chapter, verse_number, translation_id)` — permite a mesma referência em várias traduções.
- Tabela `translations`: `code (UNIQUE), name, language, license, is_default`.
- Índice: `idx_verses_translation (translation_id)`.
- FTS4: `verses_fts (text, book_id, chapter, verse_number)` — texto normalizado (sem acentos), filtro por tradução no outer query via `v.translation_id = ?`.

## 3. Script
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]