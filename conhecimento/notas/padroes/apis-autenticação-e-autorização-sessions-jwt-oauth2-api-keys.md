---
tags: [apis-web, deprecado, device, duração, implicit, padrao]
aliases: [APIs: autenticação e autorização (sessions, JWT, OAuth2, API]
date: 2026-08-14
---

# APIs: autenticação e autorização (sessions, JWT, OAuth2, API keys)

**Fonte:** apis-web

**Autenticação** (quem é você) ≠ **Autorização** (o que você pode fazer). **Sessions/cookies:** servidor guarda o estado da sessão (em memória ou store) e envia cookie `HttpOnly; Secure; SameSite`; o cliente envia o cookie em toda request. Simples e revogável instantaneamente; custo de state no servidor; vulnerável a CSRF se mal configurado (use SameSite + token anti-CSRF). Bom para apps web tradicionais. **JWT (JSON Web Token):** token stateless assinado (HMAC com secret ou RSA/ECDSA) com claims (`sub`, `exp`, `scope`). O servidor só valida a assinatura — não consulta store. Vantagens: escalabilidade horizontal, perfeito para APIs/mobile/SPA. Cuidados: nunca guarde segredos no payload (é apenas base64, não criptografado); `exp` obrigatório e curto; **revogação é difícil** (token válido até expirar) — use blacklist ou token de curta duração + refresh; sempre valide assinatura, issuer (`iss`) e audience (`aud`); use `jwt` sobre HTTPS sempre. **OAuth2:** framework de **delegação de autorização** — o cliente (app) obtém acesso em nome do usuário sem ver a senha. Fluxos: Authorization Code + PKCE (padrão para SPAs/mobile), Client Credentials (server-to-server), Device Code, Implicit (deprecado). Emitido via Authorization Server com scope e refresh token. Use uma lib madura (Expo/OpenID Connect para identidade). **API keys:** segredo opaco simples para autenticar máquinas/integrações (cliente server-to-server). Não identifica usuário humano; guarde com rotação, escopo por origem/IP e rate limiting. **Decisão prática:** web app com UI → session cookie; SPA/mobile consumindo API própria → JWT (access curto + refresh rotativo) ou OAuth2 PKCE; integrações server-to-server → API key ou OAuth2 client credentials. Autorização sempre no servidor: nunca confie em claims do cliente — valide permissões (RBAC/ABAC) por request.
## Conexoes

- [[apis-http-na-prática-métodos-status-cabeçalhos-cache]]
- [[apis-rest-recursos-coleções-versionamento-e-hipermidia]]
- [[apis-serialização-contratos-e-graphql-vs-rest]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]