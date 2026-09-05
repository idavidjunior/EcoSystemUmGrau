---
tags: [instância opencode, opencode, opencode está, opencode não, opencodeopencodeopencodeopencodeopencodeopencodeopencodeopen, padrao]
aliases: [retencao opencode db vigilante]
date: 2026-08-27
---

# retencao opencode db vigilante

**Fonte:** opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode

Tipo: padrao

Tags: [opencode, retencao, vacuum, vigilante, limpeza-db]

Data: 2026-08-27

Contexto: Verificação de espaço no C: revelou opencode.db com 5,9 GB. O opencode não tem retenção nativa e o banco cresce sem limite (eventos repetem o payload da sessão).

Decisão: Integrar a retenção do opencode.db no vigilante.ps1 (estrutura existente) chamando limpeza_disco.py --opencode-db --dias 7, com gate de 24h via marcador runtime. A poda roda sempre; o VACUUM só roda quando nenhuma instância do OpenCode está ativa, pois exige lock exclusivo.; ---
tipo: padrao
tags: [opencode, retencao, vacuum, vigilante, limpeza-db]
data: 2026-08-27
contexto: Verificação de espaço no C: revelou opencode.db com 5,9 GB. O opencode não tem retenção nativa e o banco cresce sem limite (eventos repetem o payload da sessão).
decisao: Integrar a retenção do open
## Conexoes

- [[2026-08-03-adb-remoto-via-tailscale-script-automatico-de-rot]]
- [[cluster-hub-ecossistema]]
- [[compreensao-de-pedidos-refino-com-a-llm-do-opencode-primaria]]
- [[config-2026-07-28-formato-correto-do-mcp-no-opencode-1187]]
- [[eco-agente-e-comando-global]]
- [[padrao-hub-padroes]]