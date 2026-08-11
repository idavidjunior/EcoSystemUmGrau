---
tipo: padrao
tags: [opencode, @mention, comando, agente, eco, clausula-petrea, config, ativacao]
data: 2026-08-08
contexto: Em nova sessão com outra LLM, o usuário digitou "@eco" e recebeu "I don't see an agent or skill named 'eco'". O mesmo ocorreu com "@ecosystemumgrau". A LLM não via "eco" em sua lista de agentes/skills.
decisao: Diagnóstico pela documentação do opencode: no opencode, comandos são invocados com "/" (slash), e a menção "@" resolve apenas agentes, skills, arquivos e referências — NÃO comandos. Portanto "@eco" chegava como texto cru à LLM, que não encontrava nenhum agente/skill chamado "eco". Correção: (1) criado o agente subagent "eco" (config/agents/eco.md, deploy em ~/.config/opencode/agents/eco.md) com o protocolo de ativação do EcoSystemUmGrau — agora "@eco" resolve deterministicamente em qualquer LLM; (2) reforçado o comando "/eco" no config/opencode.jsonc (deployado globalmente) com caminhos absolutos via {{USERPROFILE}} e roteamento agent: "eco" — funciona de qualquer diretório. Ambos ficam globais.
impacto: "@eco" e "/eco" agora funcionam globalmente em qualquer sessão e qualquer LLM. O comando "/" não era a causa do problema; a ausência do agente "eco" era. Mesmo padrão se aplica a "@sync" e "@compreender" (menções em cláusulas) — se falharem em outra LLM, criar agentes de mesmo nome resolve.
---

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[cluster-hub-programacao]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]