---
tags: [bug, sessaolimpezaauth]
aliases: [auth.json com entradas de chave NVIDIA disfarcadas de outros]
date: 2026-08-01
---

# Bug: auth.json com entradas de chave NVIDIA disfarcadas de outros provedores

**Projeto:** sessao_limpeza_auth

## Causa Raiz
auth.json continha 5 entradas, 2 com chaves nvapi-... mascaradas como deepseek-ai e outra

## Correcao
Removidas entradas invalidas mantendo apenas github-copilot (oauth), nvidia (api key), deepseek (api key legitimo)
