---
name: authz-authn-matrix
description: |
  Estratégias de autenticação e autorização: OAuth2/OIDC, passkeys, sessões, RBAC/ABAC e controles por recurso.
  Trigger phrases: "auth", "oauth", "oidc", "rbac", "abac", "zanzibar"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Authn/Authz Matrix — Identidade e Permissão sem Ambiguidade

## Objetivo
Definir quem é o usuário (authn) e o que ele pode fazer (authz) com regras auditáveis.

## Matriz de decisão
- B2C web/mobile: OIDC + PKCE + refresh token rotativo
- B2B/API: OAuth2 client credentials + escopos finos
- Interno/admin: SSO corporativo + MFA obrigatório
- Alta segurança: passkeys/WebAuthn + step-up auth

## Modelo de autorização
- RBAC para papéis estáveis
- ABAC para contexto dinâmico (tenant, região, horário)
- ReBAC/Zanzibar para relacionamentos complexos
- Policy engine central para evitar lógica dispersa

## Checklist de implementação
- Tokens curtos + revogação efetiva?
- Sessões protegidas contra fixation/replay?
- Permissão validada por recurso e ação?
- Auditoria de decisões de autorização?
- Segregação por tenant garantida?

## Testes essenciais
- Escopo insuficiente retorna 403 consistente
- Usuário autenticado sem permissão não acessa recurso
- Token expirado/revogado tratado corretamente
- Elevação de privilégio bloqueada

## Anti-patterns
- Confundir autenticação com autorização
- Validar permissão só na UI
- "Admin bypass" sem trilha de auditoria
- Escopos amplos demais por conveniência

## Saída esperada do agente
- Matriz `ator x recurso x ação`
- Estratégia de tokens/sessão
- Controles por severidade de risco
- Plano de testes de authn/authz