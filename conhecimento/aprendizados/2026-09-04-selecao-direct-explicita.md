---
tipo: padrao
tags: [kernel, direct, ferramentas, seguranca]
data: 2026-09-04
contexto: A rota DIRECT delegava a seleção de ferramentas ao planner e ao cognitive_core.
decisão: Usar uma seleção explícita para operações locais conhecidas e recusar pedidos fora do catálogo.
impacto: Leitura, escrita, listagem, glob, exclusão, Python e shell têm contratos previsíveis; APIs externas não são executadas por inferência.
---

O executor DIRECT agora identifica operações por verbos e objetos explícitos. A seleção não cria ferramentas novas e continua usando o servidor mcp-dev-tools e o Tool Orchestrator existentes.

Validação: dez testes focados e execução real de listagem de arquivos passaram.

## Conexoes

- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]