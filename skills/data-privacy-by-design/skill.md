---
name: data-privacy-by-design
description: |
  Privacidade por design para LGPD/GDPR: minimização, base legal, retenção e governança de dados.
  Trigger phrases: "LGPD", "GDPR", "privacy by design", "PII", "data retention"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Data Privacy by Design — Compliance Embutido no Produto

## Objetivo
Proteger dados pessoais desde a arquitetura, não como etapa final de auditoria.

## Princípios
- Minimização de dados
- Finalidade explícita de uso
- Retenção limitada e descarte seguro
- Transparência e controle do titular

## Decisões arquiteturais
- Classificação de dados (PII/sensível/anônimo)
- Separação de identificadores e payload
- Criptografia em trânsito e repouso
- Tokenização/pseudonimização quando aplicável

## Operação e governança
- Registro de base legal por fluxo
- Data lineage e inventário atualizado
- Processo de DSAR (acesso/correção/exclusão)
- Logs sem vazamento de PII

## Checklist
- Coletamos apenas o necessário?
- Consentimento e revogação estão auditáveis?
- Exportação e exclusão funcionam ponta a ponta?
- Terceiros têm DPA e controles adequados?

## Anti-patterns
- Guardar dados "para talvez usar depois"
- Replicar PII em múltiplas tabelas sem controle
- Backups sem política de expurgo
- Telemetria com dados sensíveis em claro

## Saída esperada do agente
- Mapa de dados pessoais por fluxo
- Riscos de privacidade priorizados
- Plano de mitigação técnico/processual
- Evidências de compliance operacional