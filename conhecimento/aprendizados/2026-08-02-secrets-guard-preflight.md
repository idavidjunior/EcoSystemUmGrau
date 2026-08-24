---
tipo: padrao
tags: [seguranca, preflight, auth, resiliencia, env]
data: 2026-08-02
---

# Secrets Guard no preflight_check

## Contexto
O bug historico "sessao_limpeza_auth" (chaves nvapi camufladas como outros
providers no auth.json) mostrou que chaves de provider podem vazar para o
auth.json sem deteccao no fluxo de resiliencia.

## Decisao

Adicionada a secao [6] Secrets Guard ao `scripts/preflight_check.py`:

- `guard_auth_json()`: auth.json so deve conter login OAuth oficial do
  OpenCode; bloqueia chave crua (prefixos nvapi-, sk-, ghp_, etc.) e chave
  mascarada (nvapi em provider != nvidia). Leitura com encoding utf-8-sig.
- `guard_env_vars()`: toda referencia `{env:VAR}` citada na config deve estar
  definida no ambiente.
- `guard_literal_keys()`: rejeita apiKey/token/secret literal; exige `{env:VAR}`.

## Impacto

- auth.json `{}` (vazio/neutro) passa como seguro.
- chave nvapi mascarada como "deepseek" e BLOQUEADA (1 ERRO).
- Preflight completo: TODOS TESTES PASSARAM.
- Sincronizado em a81af50 + memoria #53.

## Conexoes

- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]