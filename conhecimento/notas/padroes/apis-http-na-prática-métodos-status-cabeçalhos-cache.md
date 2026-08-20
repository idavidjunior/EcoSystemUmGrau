---
tags: [429, apis-web, header, limit, padrao, rate]
aliases: [APIs: HTTP na prática (métodos, status, cabeçalhos, cache)]
date: 2026-08-20
---

# APIs: HTTP na prática (métodos, status, cabeçalhos, cache)

**Fonte:** apis-web

**HTTP/1.1** é o transporte das APIs web. **Métodos:** `GET` (ler, sem efeitos colaterais, idempotente e cacheável), `POST` (criar ou 'ação' genérica, não idempotente), `PUT` (substituir recurso completo, idempotente), `PATCH` (atualização parcial), `DELETE` (remover, idempotente), mais `HEAD`, `OPTIONS`, `TRACE`, `CONNECT`. Idempotência: repetir a mesma request não muda o estado além da primeira — GET/PUT/DELETE devem ser idempotentes; POST não (use um Idempotency-Key para pagamentos/orders). **Status codes:** 1xx informativo (100 Continue, 101 Switching); 2xx sucesso (200 OK, 201 Created + Location, 202 Accepted para async, 204 No Content); 3xx redireção (301 moved permanently, 304 Not Modified p/ cache condicional, 307/308 preservam método); 4xx erro do cliente (400 malformado, 401 não autenticado, 403 não autorizado, 404 não encontrado, 405 método não permitido, 409 conflito, 422 entidade não processável — validação de domínio, 429 rate limit + header Retry-After); 5xx erro do servidor (500, 502 bad gateway, 503 indisponível, 504 timeout). **Cabeçalhos essenciais:** `Content-Type`/`Accept` (negociação), `Authorization`, `Cache-Control`, `ETag`, `If-None-Match`/`If-Modified-Since`, `Idempotency-Key`, `Retry-After`, `CORS` (`Access-Control-Allow-Origin`). **Cache na prática:** `Cache-Control: max-age=3600` (também `public/private`, `no-store`, `no-cache`, `must-revalidate`); validação com ETag (válido para revalidar com `If-None-Match` → 304). Caches: browser, CDN (edge), reverse proxy, cache de aplicação. **Boas práticas:** nunca cachear payloads autenticados/privados sem `private`/`no-store`; usar `Vary: Accept`; mensagens de erro com corpo estruturado (`{error: {code, message, details}}`); timeouts e retry com backoff exponencial no cliente. Sempre retorne o status code correto — a semântica do HTTP é parte do contrato da API.
## Conexoes

- [[apis-autenticação-e-autorização-sessions-jwt-oauth2-api-keys]]
- [[apis-rest-recursos-coleções-versionamento-e-hipermidia]]
- [[apis-serialização-contratos-e-graphql-vs-rest]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]