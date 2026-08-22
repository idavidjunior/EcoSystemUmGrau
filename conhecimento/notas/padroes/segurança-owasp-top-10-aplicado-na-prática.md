---
tags: [aplique, cabeçalho, método, padrao, seguranca, verbos]
aliases: [Segurança: OWASP Top 10 aplicado na prática]
date: 2026-08-22
---

# Segurança: OWASP Top 10 aplicado na prática

**Fonte:** seguranca

OWASP Top 10 não é checklist de compliance: é ranking das falhas mais exploradas. Aplicar na prática significa fixar cada classe com defesa em profundidade, assumindo que o input é hostil.

**1) Broken Access Control (hoje #1):** a falha mais comum e barata de explorar. Mitigue: nunca confie em cliente (IDs de objeto checados no servidor — IDOR), autorize por servidor em cada request, deny-by-default, valide método HTTP e verbos, aplique cabeçalho `Cache-Control: no-store` em dados sensíveis, limite por origem (CORS com allowlist).

**2) Cryptographic Failures (antes \"sensitive data exposure\"):** criptografe em trânsito (TLS 1.2+, HSTS) e em repouso; nunca armazene senha (só hash argon2/bcrypt com salt); evite algoritmos antigos (SHA1, MD5 para senha); dados sensíveis sem criptografia em cache, logs ou backup são falha.

**3) Injection:** SQL é a rainha. Use parametrização/prepared statements SEMPRE — não confie em \"escaping\"; sanitize por framework no ponto de saída (XSS); órgãos de linguagem: separe dados de instrução. Injection em command, LDAP, XPath e template seguem a mesma regra.

**4) Insecure Design:** faltam controle de limites de taxa, budget de consultas, validação de fluxo de negócio (ex.: limite de crédito). Segurança começa no design, não no código.

**5) Security Misconfiguration:** defaults inseguros, CORS aberto, debug ligado, headers ausentes (`X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`). Automatize hardening e scan.

**6) Vulnerable Components:** software com CVE conhecido. Gerencie SBOM e atualize com prioridade (ver card de supply chain).

**7) Identification & Authentication Failures:** MFA, senhas com policy razoável, rate-limit no login, logout real, proteja sessão.

**8) Software & Data Integrity Failures:** valide assinaturas, CI/CD assinado, desserialização segura, desatualização de dados (race conditions).

**9) Logging & Monitoring Failures:** logue eventos de segurança com dados acionáveis, alerte anomalias, nunca logue segredos.

**10) SSRF:** controle URLs de saída, bloqueie IPs privados/metadata (`169.254.169.254`), allowlist de destinos, DNS rebinding protection.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]