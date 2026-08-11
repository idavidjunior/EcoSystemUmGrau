---
tipo: padrao
tags: [skills, manifesto, dominios-tecnicos, mcp, plano-lacunas]
data: 2026-08-04
contexto: Plano listava 53 dominios tecnicos sem skill. Usuario autorizou criar todos seguindo o padrao mcp/<dominio>/habilidades/.
decisao: Gerar skill.md declarativas em lote via script para os dominios IA/MLOps, DevOps, Seguranca, Arquitetura, Mobile, Frontend, Backend, Dados, Qualidade e Documentacao.
impacto: Catalogo de habilidades saltou para 96 (48 novas); manifesto regenerado; servers MCP expoem tudo automaticamente.
---

# 48 skills tecnicas do plano (96 no total)

## O que foi feito
- `context/lista_skills.py` — dados: (id, dominio_mcp, titulo, descricao_com_triggers).
- `context/gerar_skills.py` — gera `mcp/<dominio>/habilidades/<id>/skill.md` com frontmatter
  (name/description) + corpo declarativo, seguindo o padrao das skills existentes.
- 48 novas skills em `mcp/desenvolvimento/` (44) e `mcp/android/` (4: ios, flutter,
  react-native, expo).
- `manifesto_geral.json` regenerado: **96 habilidades**, 0 duplicados, entrypoints ok.
- Server `mcp/desenvolvimento` agora expoe 74 tools; `mcp/android` 8.

## Padrao de geracao (reutilizavel)
- Formato: tupla de 4 `(id, dominio, titulo, descricao)`. Os triggers ficam no FINAL da
  descricao como `Trigger keywords: ...`; `split_triggers()` separa para o frontmatter.
- Rodar: `python scripts/generate-manifesto.py` apos qualquer mudanca de skills.

## Validacao
- preflight_check.py: TODOS TESTES PASSARAM (MCP mcp-desenvolvimento e mcp-android PASS).
- tools/list: desenvolvimento 74, android 8; novas skills presentes.
- Memory #89.

## Lista das 48 novas
IA/MLOps: prompt-engineering, rag-implementation, fine-tuning, eval-testing,
agent-orchestration, mlops, vector-databases.
DevOps: kubernetes, terraform, ci-cd-pipeline, infrastructure-as-code,
monitoring-alerting, service-mesh.
Seguranca: threat-modeling, secure-coding, vulnerability-scanning, compliance-audit.
Arquitetura: domain-driven-design, event-sourcing, cqrs, microservices-patterns.
Mobile: ios, flutter, react-native, expo.
Frontend: react-vue-svelte-patterns, state-management, css-architecture, accessibility.
Backend: graphql, grpc, message-queues, event-driven-architecture.
Dados: data-pipeline, feature-engineering, model-training, database-design, nosql-patterns.
Qualidade: code-review, refactoring-patterns, legacy-modernization, technical-debt,
contract-testing, performance-testing.
Documentacao: technical-writing, api-documentation, adr, runbooks.

## Conexoes

- [[cluster-hub-programacao]]