---
tipo: padrao
tags: [auditoria, auto-evolucao, qualidade, dedup, gates, skill, manifesto, memory]
data: 2026-08-10
contexto: "Skill auditoria-de-codigo criada como documento não era viva: não estava no manifesto_geral.json e não tinha mecanismo para auto-evoluir sem acumular lixo, redundância e falsos positivos. Usuário exigiu que a skill seja harmonizada com o ecossistema, alimente e se auto-alimente dele."
decisao: "Implementado cérebro evolucao.py (mcp/desenvolvimento/habilidades/auditoria-de-codigo/) com gates determinísticos: (1) evidência obrigatória existente em disco → sem ela rejeita em rejeitados.json com motivo; (2) dedup por similaridade Jaccard ≥0.80 → incrementa recorrencias do padrão existente em vez de duplicar; (3) acionabilidade → observação não vira regra até recorrer; (4) anti-overfitting → padrão único só vira checklist se impacto alto. review absorve no checklist quando ≥3 elegíveis (acionável + ≥2 ocorrências OU impacto alto), com backup skill.md.bak e registro em revisoes.json + evolucao.md. prune --dias remove rejeitados antigos e padrões mortos. add aceito fecha o loop via memory_engine (ecossistema aprende da skill). Registrada no manifesto via generate-manifesto.py (101 habilidades). Seed inicial = 8 padrões já no checklist."
impacto: "Skill viva e com evolução controlada. Gates validados por testes em dir isolado (dedup, review absorvendo checklist, rejeição sem evidência, prune). Preflight 100% após sanear bug pré-existente: memória #236 continha hardcoded path C:\Users\David Jr\Documents\EcoSystemUmGrauBACKUP que falhava test_json_sanitization.py; sanitizado para 'EcoSystemUmGrauBACKUP (clone antigo, 03/ago)' e reindexado (774 docs)."
---

# Aprendizado: Skill auditoria-de-codigo viva com evolução gated

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

- Usar `evolucao.py add` ao fim de cada auditoria real (gate obrigatório).
- Rodar `review` conforme padrões elegíveis acumulam; re-espelhar após revisão.
