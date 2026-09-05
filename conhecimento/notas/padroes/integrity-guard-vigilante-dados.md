---
tags: [falsos, opencodeopencodeopencodeopencodeopencode, padrao, positivos, proteção, vários]
aliases: [integrity guard vigilante dados]
date: 2026-08-20
---

# integrity guard vigilante dados

**Fonte:** opencode+opencode+opencode+opencode+opencode

Tipo: padrao

Tags: [integracao, vigilancia, mojibake, integridade, dados]

Data: 2026-08-18

Contexto: O ecossistema sofreu corrupção de dados por mojibake (texto UTF-8 lido como CP1252) em vários JSONs de conhecimento. A correção do knowledge_graph foi manual e não se repetia. Decidiu-se criar um vigilante permanente de integridade de dados.

Decisão: Criar scripts/integrity_guard.py, um detector/corretor de mojibake e truncamento em 13 JSONs de conhecimento, com backup, escrita atômica e proteção contra falsos positivos. Integrado aos gatilhos naturais: runtime_boot --check, preflight_check seção [10] e vigilante.ps1 (timer 1h com --fix + comunicação via Write-Log e memory_engine log).
## Conexoes

- [[2026-08-04-persistencia-da-conexao-do-jarvis]]
- [[cluster-hub-ecossistema]]
- [[padrao-hub-padroes]]