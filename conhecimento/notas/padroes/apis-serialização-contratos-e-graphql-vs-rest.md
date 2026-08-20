---
tags: [agregados, apis-web, fontes, frontends, padrao, várias]
aliases: [APIs: serialização, contratos e GraphQL vs REST]
date: 2026-08-20
---

# APIs: serialização, contratos e GraphQL vs REST

**Fonte:** apis-web

**Serialização** transforma objetos em representação de transporte. **JSON** é o padrão de fato: use nomes consistentes (snake_case vs camelCase — decida e documente), tipos corretos (número vs string de número), e trate datas em ISO 8601 UTC (`2026-08-10T14:30:00Z`). Boas práticas: **nunca serializar entidades de domínio diretamente** — use DTOs explícitos que controlam o que sai (evita vazar senha_hash, campos internos e acopla o contrato ao modelo); use null vs ausente de forma deliberada; número como string para bigint (IDs de 64 bits quebram em JS). Ferramentas: Jackson/Gson (Java), pydantic/serializers (Python), Serde (Rust), attributes-based (TS). **Contratos:** a spec OpenAPI/Swagger (ou JSON Schema) é o single source of truth: documenta endpoints, schemas, erros, auth. Gere clientes e servidores a partir dela (openapi-generator) e valide request/response em testes de contrato. **GraphQL vs REST:** GraphQL expõe um único endpoint (`POST /graphql`) com query language — o cliente pede exatamente os campos que quer (evita over/under-fetching), schema fortemente tipado e tipado self-documenting, boa para mobile e frontends com dados agregados de várias fontes. Custos: cache HTTP quase inexistente (mude para persistência/cache por query), complexidade de resolver/N+1, rate limiting e segurança mais difíceis (query depth/complexity), e dificuldade de versionar (evolução de schema, field deprecation). **REST** é melhor para simplicidade, cache por recurso, versionamento explícito, tools/curl/debug, e integrações machine-to-machine estáveis. **Regra prática:** REST para o núcleo da API pública e contratos estáveis; GraphQL quando o cliente consome dados de consumo variável e o time tem maturidade para custear o overhead. No meio: REST + campos de filtro/select + partial responses.
## Conexoes

- [[apis-autenticação-e-autorização-sessions-jwt-oauth2-api-keys]]
- [[apis-http-na-prática-métodos-status-cabeçalhos-cache]]
- [[apis-rest-recursos-coleções-versionamento-e-hipermidia]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]