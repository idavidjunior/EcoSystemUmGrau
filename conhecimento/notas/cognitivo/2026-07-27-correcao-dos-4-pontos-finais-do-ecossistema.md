---
tags: [agentes, cognitivo, general, graph, python, tem]
aliases: [# 2026-07-27 - Correcao dos 4 pontos finais do ecossistema]
date: 2026-08-10
---

# # 2026-07-27 - Correcao dos 4 pontos finais do ecossistema

**Dominio:** general

# 2026-07-27 - Correcao dos 4 pontos finais do ecossistema

## Problemas resolvidos
1. **Paths fixos**: vigilante.ps1, ecosystem.ps1, SKILL.md agora usam env:USERPROFILE
2. **LER vs OpenCode**: documentado que LER tem engine MODULES (Python), OpenCode tem AGENTES (LLM). Sao complementares, nao duplicados.
3. **ecosystem learn**: varredura proativa que escaneia projetos Android + registra no knowledge graph
4. **Vigilante aprende sozinho**: timer diario executa ecosystem learn automaticamente
5.

# 2026-08-02 - Regras do ecossistema: garantia de obediÃªncia pelo LLM

## Contexto
O usuÃ¡rio perguntou se as regras estavam no local correto. InvestigaÃ§Ã£o honesta
revelou que NÃƒO estavam: `config/agents/00-system-rules.md` era um "agente fantasma"
(sem frontmatter, sem referÃªncias de outros agents) e nÃ£o existia AGENTS.md â€” ou seja,
as ClÃ¡usulas PÃ©treas dependiam do LLM "lembrar" de invocar o agente. Na prÃ¡tica nÃ£o
eram aplicadas.

## Problema raiz
- `00-system-rules.md` nÃ£o tinha
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]