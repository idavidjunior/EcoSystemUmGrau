---
name: semantic-release-automation
description: |
  Automação de versionamento e changelog com conventional commits e pipeline de release confiável.
  Trigger phrases: "semantic release", "conventional commits", "changelog", "versioning"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Semantic Release Automation — Release sem Surpresas

## Objetivo
Automatizar versionamento, changelog e publicação com regras previsíveis.

## Fluxo de release
1. Validar conventional commits no CI
2. Calcular versão (major/minor/patch)
3. Gerar changelog por categoria
4. Criar tag e publicar artefatos
5. Notificar canais de entrega

## Regras recomendadas
- `feat` -> minor
- `fix` -> patch
- `BREAKING CHANGE` -> major
- Commits de docs/chore com impacto controlado

## Checklist de pipeline
- Branch de release definida?
- Token/permissões de publish corretos?
- Dry-run disponível?
- Artefatos assinados/validados?
- Rollback de versão documentado?

## Governança
- Política de suporte por versão
- Pre-release para canais beta
- Notas de release orientadas a impacto
- Rastreabilidade commit -> versão

## Anti-patterns
- Publicar manual sem trilha
- Commits sem convenção
- Changelog genérico sem contexto
- Quebrar sem sinalizar `BREAKING CHANGE`

## Saída esperada do agente
- Config de semantic release
- Política de commit/versionamento
- Pipeline de release com validações
- Plano de rollback de publicação