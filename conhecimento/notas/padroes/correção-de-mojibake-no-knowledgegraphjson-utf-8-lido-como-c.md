---
tags: [ativa, generate, notes, opencodeopencodeopencodeopencode, padrao, u00c7]
aliases: [Correção de mojibake no knowledge_graph.json (UTF-8 lido com]
date: 2026-08-20
---

# Correção de mojibake no knowledge_graph.json (UTF-8 lido como CP1252)

**Fonte:** opencode+opencode+opencode+opencode

## Contexto
O vault Obsidian (`conhecimento/notas/_hubs/`) gerado por `generate-obsidian-notes.py`
exibia dezenas de nomes corrompidos (ex.: "Cl\\u00e1usula P\\u00e9trea",
"Comunica\\u00e7\\u00e3o cont\\u00ednua em \\u00e1udio", "ATIVA\\u00c7\\u00c3O",
"N\\u00c3O", "autom\\u00e1tico", "Evolu\\u00e7\\u00e3o"). A origem não era o script,
mas sim o `ler-runtime/knowledge/knowledge_graph.json`, cujas strings foram gravadas
com mojibake de UTF-8 interpretado como CP1252/Latin-1.

## Decisão
Corrigir a fonte única (knowledge_graph.json) em passes progressivos:

1. Tabela de substituição direta dos pares mais comuns (ex.: pares "Ã"+"vogal" -> vogal
   acentuada, "ç"->ç, sequência 3-bytes -> em-dash etc.)
2. Round-trip genérico `encode('latin-1').decode('utf-8')` para strings 100% mojibake
3. Round-trip `encode('cp1252').decode('utf-8')` (encoding real usado na corrupção)
4. Tabela de pares residuais (ex.: "Ã"->Ã, "Ç"->Ç) para strings mistas que
   continham caracteres legítimos (—) e não pass
## Conexoes

- [[cluster-hub-ecossistema]]
- [[padrao-hub-padroes]]