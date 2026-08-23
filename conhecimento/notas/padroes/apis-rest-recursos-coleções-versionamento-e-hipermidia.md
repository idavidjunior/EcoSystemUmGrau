---
tags: [apis-web, estados, estáveis, ids, padrao, sejam]
aliases: [APIs: REST, recursos, coleções, versionamento e hipermidia]
date: 2026-08-23
---

# APIs: REST, recursos, coleções, versionamento e hipermidia

**Fonte:** apis-web

**REST (Representational State Transfer)** é um estilo arquitetural, não um protocolo nem um formato. Princípios: recursos identificados por URI, representações (JSON/XML) trocadas por métodos HTTP padronizados, stateless (estado do cliente, não do servidor), cacheabilidade e hipermidia como motor do estado da aplicação (HATEOAS). **Recursos e coleções:** `/orders` (coleção), `/orders/{id}` (elemento), sub-recursos aninhados com moderação (`/orders/{id}/items`). Nomeie no plural, use substantivos (não verbos — ações viram sub-recursos ou endpoints de ação com POST), kebab-case ou snake_case consistente, e URLs que sejam IDs estáveis, não estados. **Mapeamento:** GET /orders → listar (com paginação `?page`/`limit` ou cursor `?cursor`), POST /orders → criar (201 + Location), GET /orders/123 → ler, PUT /orders/123 → substituir, PATCH → parcial, DELETE → 204. **Status de coleções:** 200 com payload de paginação (`{items, page, total, next}`), erros de validação em 400/422. **Versionamento:** compatibilidade é prioridade. Estratégias: na URL (`/v1/orders` — simples e explícito, mas não-hipermidia 'pura'), no header (`Accept: application/vnd.myapi.v1+json`), ou por data (`/2026-08/orders`). Na prática, **URL versioning `/v1`** é o mais comum e debuggável; compatível com HTTP semantics. Regra: versionamento só entra quando há contrato externo; evite minor version na URL (use extensões não quebradoras). **Hipermidia:** a resposta carrega links (`self`, `next`, `payment`) para o cliente descobrir ações sem conhecimento hard-coded das URLs. Reduz acoplamento, mas aumenta complexidade do cliente. **Boas práticas:** documentação com OpenAPI (single source of truth), depreciação com plano de retirada (nunca remova versão sem aviso), e paginação e filtragem consistentes.
## Conexoes

- [[apis-autenticação-e-autorização-sessions-jwt-oauth2-api-keys]]
- [[apis-http-na-prática-métodos-status-cabeçalhos-cache]]
- [[apis-serialização-contratos-e-graphql-vs-rest]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]