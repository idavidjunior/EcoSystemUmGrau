---
tags: [236, acionabilidade, entrada, nova, opencode, padrao]
aliases: [Aprendizado: Skill auditoria-de-codigo viva com evolução gat]
date: 2026-08-10
---

# Aprendizado: Skill auditoria-de-codigo viva com evolução gated

**Fonte:** opencode

## Resumo

Tornada a skill viva no ecossistema com auto-evolução sem lixo.

## O que foi feito

1. `mcp/desenvolvimento/habilidades/auditoria-de-codigo/evolucao.py` — cérebro
   com subcomandos `add`, `review`, `stats`, `prune`.
2. Dados: `aprendizados.json` (8 padrões seed, em_checklist), `rejeitados.json`,
   `revisoes.json`, `evolucao.md` (histórico).
3. skill.md canônico atualizado com o fluxo de auto-evolução gated + espelho em
   `~/.claude/skills/auditoria-de-codigo/`.
4. Registrada no `manifesto_geral.json` (entrypoint + script).
5. Preflight: corrigido bug pré-existente de hardcoded path na memória #236.

## Lições

- Auto-evolução precisa de portão de qualidade (evidência + dedup + acionabilidade
  + anti-overfitting), senão vira lixo organizado.
- Padrão repetido reforça (recorrencias), não infla (sem nova entrada).
- O ecossistema indexa `conhecimento/aprendizados/` e `memories.json` via BM25:
  o loop se fecha quando o aprendizado validado vira memória.

## Próximos passos
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]