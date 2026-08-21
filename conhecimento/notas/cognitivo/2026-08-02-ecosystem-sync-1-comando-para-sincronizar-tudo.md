---
tags: [cognitivo, ficar, general, parent, vive, único]
aliases: [# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tu]
date: 2026-08-21
---

# # 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

**Dominio:** general

# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

## Contexto
O usuário queria sincronizar o ecossistema inteiro com um único comando, para ficar
sempre atualizado e nada se perder ao trocar de PC.

## O que foi feito
- Corrigido `scripts/ecosystem.ps1`:
  - `$ecoDir` agora é auto-detectado via `Split-Path $PSScriptRoot -Parent` (antes
    hardcoded `Desktop\Codigos\EcoSystemUmGrau`, que não existe mais — o repo vive em
    `Documents\Default Project\EcoSystemUmGrau`).
  - `
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]