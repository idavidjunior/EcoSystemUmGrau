---
name: security-review
description: |
  Revisão de segurança pragmática: identificação de riscos, priorização por impacto e plano de mitigação verificável.
  Trigger phrases: "security review", "threat model", "vulnerability", "secure coding"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Security Review — Risco Real, Mitigação Real

## Objetivo
Detectar vulnerabilidades relevantes ao negócio e propor correções priorizadas e testáveis.

## Escopo mínimo
- Entradas não confiáveis e validação
- Autenticação/autorização
- Gestão de segredos e credenciais
- Dependências e supply chain
- Superfície de ataque externa

## Método de revisão
1. Mapear ativos e dados sensíveis
2. Identificar fronteiras de confiança
3. Levantar ameaças prováveis
4. Classificar risco (impacto x probabilidade)
5. Definir mitigação + evidência de correção

## Checklist técnico
- Input sanitizado e validado por schema?
- Controles de acesso por recurso, não só por rota?
- Segredos fora de código e logs?
- Proteção contra SSRF, IDOR, SQLi, XSS, CSRF (quando aplicável)?
- Dependências com CVEs críticas tratadas?

## Anti-patterns
- "Segurança por obscuridade"
- Tratar achado crítico como dívida baixa
- Corrigir sem teste de regressão
- Ignorar telemetria de abuso

## Saída esperada do agente
- Lista de achados por severidade
- Evidência técnica de cada risco
- Mitigação proposta e esforço estimado
- Plano de validação pós-correção