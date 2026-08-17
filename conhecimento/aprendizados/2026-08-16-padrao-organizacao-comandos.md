---
tipo: padrao
tags: [comandos, organizacao, padrao, eco-system, agentes]
data: 2026-08-16
contexto: >
  Auditoria revelou 9 comandos espalhados: 5 sem agent .md, 4 com paths absolutos,
  1 sem campo "agent" no config, protocolos @sync e /eco dessincronizados em 3 fontes.
  Limpeza total removeu ~70 arquivos scattered (duplicados, backups, logs, orphaned).
decisao: >
  Padrao obrigatorio para TODO novo comando no EcoSystemUmGrau:
  1. Criar config/agents/<nome>.md com frontmatter (description, mode: subagent)
  2. Adicionar entry "command" em config/opencode.jsonc com campo "agent"
  3. Registrar em config/inventario_estruturas.json
  4. Se regra permanente: adicionar CLAUSULA PETREA em 00-system-rules.md
  5. Executar sync_rules.py update + deploy agents + deploy config
  Templates devem usar paths relativos (scripts/...) nunca absolutos.
impacto: >
  Ecossistema ficou consistente: todos os 9 comandos seguem o padrao.
  ~70 arquivos scattered removidos. Config sync OK. Agents deployados.
aprendizado: >
  A desorganizacao acontece quando comandos sao criados sem seguir o pipeline completo.
  O inventario_estruturas.json e a CLAUSULA PETREA sao os gates que impedem drift.
  Paths relativos em templates eliminam acoplamento a USERPROFILE.
---

## Conexoes

- [[aapt-javac-d8-apksigner]]