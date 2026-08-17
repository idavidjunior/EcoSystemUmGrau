---
tags: [cognitivo, deploy, expande, general, list, renderizacao]
aliases: [integracao completa mcps offline placeholder]
date: 2026-08-17
---

# integracao completa mcps offline placeholder

**Dominio:** general

---
tipo: erro
tags: [integracao, mcp, opencode, config, placeholder, renderizacao, deploy]
data: 2026-08-13
contexto: Diagnóstico de integração completa do EcoSystemUmGrau. Todos os 13 MCPs
apareciam como "failed / Connection closed" no `opencode mcp list`, mesmo com o
preflight passando e o opencode.jsonc definindo todos os servidores.
decisao: A causa raiz era que o opencode.jsonc deployado em ~/.config/opencode
continha `{{USERPROFILE}}` literal nos caminhos (o opencode não expande esse
plac
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]