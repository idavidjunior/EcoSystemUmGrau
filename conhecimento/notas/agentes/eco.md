---
tags: [agente, comando, ativacao, bootstrap]
aliases: [Eco]
date: 2026-09-12
---

# eco — Ativação do EcoSystemUmGrau

**Categoria:** agentes
**Fonte:** config/agents/eco.md

## Papel

Ativa e verifica o EcoSystemUmGrau. Confirma operacionalidade, executa boot do runtime e ativa todas as regras.

## Gatilho

`@eco`, `eco`, `ative o ecosystemumgrau`, `ativar ecossistema`

## Responsabilidades

- Executar `python scripts/runtime_boot.py --check`
- Confirmar integridade (boot OK, kernel ativo, memória carregada)
- Diagnosticar e corrigir se não operante
- Ativar modo voz se "Eco" palavra única

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[runtime-boot]] — script de boot
- [[clausula-ativacao-voz]] — cláusula de ativação
- [[auto-apresentacao]] — saudação espontânea
- [[00-system-rules]] — Constituição carregada