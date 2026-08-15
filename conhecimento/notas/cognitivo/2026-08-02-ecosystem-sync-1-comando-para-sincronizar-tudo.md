---
tags: [cognitivo, ecossistema, ficar, general, inteiro, nico]
aliases: [# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tu]
date: 2026-08-14
---

# # 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

**Dominio:** general

# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

## Contexto
O usuÃ¡rio queria sincronizar o ecossistema inteiro com um Ãºnico comando, para ficar
sempre atualizado e nada se perder ao trocar de PC.

## O que foi feito
- Corrigido `scripts/ecosystem.ps1`:
  - `$ecoDir` agora Ã© auto-detectado via `Split-Path $PSScriptRoot -Parent` (antes
    hardcoded `Desktop\Codigos\EcoSystemUmGrau`, que nÃ£o existe mais â€” o repo vive em
    `Documents\Default Project\EcoSystemUmGrau`).
  - `
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]