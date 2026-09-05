---
tags: [config, opencode, padrao, quebrados, race, secrets]
aliases: [Aprendizado: Debugging Expertise Skill]
date: 2026-08-09
---

# Aprendizado: Debugging Expertise Skill

**Fonte:** opencode

## Resumo

Implementada expertise completa de debugging no EcoSystemUmGrau através de:

### 1. Skill Declarativa (`mcp/desenvolvimento/habilidades/debugging-expertise/skill.md`)
- Metodologia científica obrigatória (Observar → Hipotetizar → Testar → Validar → Corrigir → Registrar)
- Classificação de criticidade P0-P3 com SLA
- Ferramentas por linguagem: debuggers, logging estruturado, análise estática, sanitizers, profilers, memory leak detectors, race detectors
- Padrões de falha catalogados: crashes, null refs, resource leaks, duplicação, 10 code smells, UI disfuncional, links quebrados, config/secrets
- Protocolo de auto-pesquisa/autocorreção com algoritmo que evita tentativas redundantes via cache persistente
- Base de conhecimento auto-expansível em `conhecimento/debug-patterns/`
- Checklists por categoria (crash, logic, perf, ui, dup, smell, link)
- Integração com outras skills (search-first, refactoring, code-review, tech-debt, observability, etc.)

### 2. Scripts de Debug Integ
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]