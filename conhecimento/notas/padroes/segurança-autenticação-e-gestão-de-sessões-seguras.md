---
tags: [crypto, csrf, equals, lax, padrao, seguranca]
aliases: [Segurança: autenticação e gestão de sessões seguras]
date: 2026-08-15
---

# Segurança: autenticação e gestão de sessões seguras

**Fonte:** seguranca

Autenticação prova quem você é; autorização define o que você pode fazer; a sessão mantém o estado entre requests. A gestão segura de sessão é onde 80% dos ataques de identidade moram.

**Senhas:** nunca armazene plaintext nem hash não-saltado. Use argon2id (recomendado, com `m=64MB, t=3, p=1` ou parâmetros OWASP atuais) ou bcrypt (custo 10-12). Hash é para login, não para recuperação: implemente reset com token efêmero e expiração, nunca reenvie a senha. Rate-limit no endpoint de login (falhas por IP e por conta), lockout com backoff, e evite timing attacks com comparação em tempo constante (`hash_equals`, `crypto.timingSafeEqual`).

**MFA:** o mínimo aceitável hoje é TOTP (RFC 6238) ou WebAuthn/passkeys. TOTP exige segredo por usuário, exposição no setup (QR) e mecanismo de recovery (backup codes). WebAuthn elimina phishing de senha mas exige fallback de UX.

**Sessão server-side:** token aleatório de alta entropia, armazenado com hash no servidor (não plaintext no cookie), com `HttpOnly`, `Secure`, `SameSite=Strict` (ou Lax com CSRF token). Defina: expiração absoluta (re-login) + expiração de inatividade; rotação de session id a cada login/privilege escalation; revogação no logout (não apenas apagar cookie); mecanismo de invalidar todas as sessões de um usuário (violação, troca de senha).

**JWT / session tokens:** prefira sessão server-side; se usar JWT, use tokens curtos de acesso (5-15min) + refresh token armazenado em cookie httpOnly com rotação e reuse detection. JWT sem estado: impossível revogar individualmente — joker, evite. Sempre valide `iss`, `aud`, `exp`, `alg` (nunca `none`), e assine com HS256 (segredo forte) ou RS256/ES256.

**Defesas transversais:** logue logins (quem, quando, de onde — IP/UA) e alerte padrões anômalos; cheque vazamentos de credenciais (haveibeenpwned) na criação de senha; nunca exponha diferenças de timing entre \"usuário existe\" e \"senha errada\" em mensagens; considere OAuth2/OIDC (Authorization Code + PKCE) como federação padrão para delegar identidade.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]