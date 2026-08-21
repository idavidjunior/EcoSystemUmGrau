---
tags: [401, 403, 404, inválido, padrao, testes]
aliases: [Testes: testes de contrato e testes de API]
date: 2026-08-21
---

# Testes: testes de contrato e testes de API

**Fonte:** testes

**Testes de contrato** validam que dois lados de uma integração concordam sobre o contrato (forma, tipos, campos obrigatórios, status, headers) sem rodar a suíte completa. O padrão de referência é **consumer-driven contracts (CDC)** com ferramentas como Pact: o consumidor declara as interações que espera (request que fará + resposta esperada), o contrato é publicado e o provedor roda a validação (provider verification) contra esse contrato. Benefício central: detectar quebra de API **antes** do deploy, em CI, em vez de só em produção. **Testes de API** (integração) exercitam a API HTTP real: chamam o endpoint, validam status code, headers (Content-Type, CORS), corpo (schema, valores), idempotência e erros (400 para payload inválido, 404, 401/403). Use contratos de schema (OpenAPI, JSON Schema) para validar o corpo, não asserts manuais campo a campo. **Boa prática de stack:** (1) testes de contrato para cada par consumidor/provedor; (2) testes de API com a aplicação subida em teste (Testcontainers, supertest, pytest + httpx); (3) verificação de contrato com a spec OpenAPI como fonte de verdade. **Quando usar:** microservices e times diferentes no contrato; bibliotecas de clientes públicas; SDKs. **Quando não usar:** monólito com chamadas internas diretas — o custo do Pact não paga; prefira testes de integração. **Cuidados:** contratos demasiado detalhados congelam implementação (use 'matchers' para campos variáveis); esquecer de atualizar versão de contrato ao evoluir; asserção apenas de status sem validar o corpo deixa bugs passarem. Pipeline ideal: contrato aprovado → verificação no provedor em CI → publish de resultado → consumidor pode seguir com deploy.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[testes-cobertura-de-código-como-métrica-o-que-ela-mostra-e-o]]
- [[testes-mocks-fakes-e-stubs-e-quando-evitar-mockar]]
- [[testes-pirâmide-de-testes-e-o-que-testar-em-cada-camada]]
- [[testes-tdd-e-quando-ele-compensa]]