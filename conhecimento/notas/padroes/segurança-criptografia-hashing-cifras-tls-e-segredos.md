---
tags: [criptografada, dek, encryption, kek, padrao, seguranca]
aliases: [Segurança: criptografia — hashing, cifras, TLS e segredos]
date: 2026-08-11
---

# Segurança: criptografia — hashing, cifras, TLS e segredos

**Fonte:** seguranca

Criptografia se divide em três problemas distintos que as pessoas misturam: hash (verificação irreversível), cifra (confidencialidade reversível) e TLS (confidencialidade em trânsito). Usar a ferramenta errada para o problema é a falha mais comum.

**Hashing (senhas):** deve ser lento, com salt único por senha e resistente a GPU. argon2id (prêmio PHC, escolha padrão) ou bcrypt (libsodium `crypto_pwhash`). NUNCA SHA-256/MD5 para senhas — são rápidos por design. Para checksums/verificação de integridade (não senhas), SHA-256/384 é ok; para detectar colisões maliciosas use SHA-3 ou SHA-256 com comprimento adequado.

**Cifras (dados em repouso):** use AEAD: AES-256-GCM ou ChaCha20-Poly1305 (XChaCha20-Poly1305 melhor para nonce aleatório). GCM fornece confidencialidade + integridade. Não use ECB (vaza padrões), CBC sem MAC, ou cifras sem autenticação. Gerenciamento de chaves: rotação, armazenamento em HSM/KMS (AWS KMS, Azure Key Vault, Vault), envelope encryption (DEK criptografada por KEK). Nunca hardcode chave no código ou config.

**TLS (em trânsito):** TLS 1.2+ com curvas elípticas (ECDHE) para forward secrecy — nada de RSA handshake estático nem SSL 3.0/TLS 1.0/1.1. Cadeia de confiança válida, `HSTS` (`Strict-Transport-Security`) para forçar HTTPS, revocation via CRL/OCSP. Ferramenta: `ssllabs`/`testssl.sh` para auditar. Certificados: certbot (Let's Encrypt), rotação automática.

**Segredos (API keys, tokens, credenciais):** 1) nunca em código, git, logs, imagens de contêiner, env hardcoded ou README; 2) use gerenciador de segredos: Vault, AWS Secrets Manager, SOPS, age, ou env injetado pelo orquestrador no runtime; 3) rotacione proativamente e invalide vazados (git scan com gitleaks/trufflehog); 4) escaneie containers em build (trivy).

**Regra final:** peça padrão é NIST SP 800-63B para senhas, NIST SP 800-52 para TLS, NIST SP 800-57 para gestão de chaves. Criptografia própria (roll your own) é proibida — use bibliotecas mantidas (libsodium, OpenSSL, Tink).
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]