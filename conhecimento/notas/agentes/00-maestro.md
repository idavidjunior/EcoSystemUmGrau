---
tags: [agente, nucleo, maestro, runtime]
aliases: [Maestro do Runtime]
date: 2026-09-12
---

# 00-maestro — Maestro do Runtime

**Categoria:** agentes
**Fonte:** config/agents/00-maestro.md

## Papel

Coordenador único de processos críticos do ecossistema. Mantém livro único de processos vivos (`runtime/maestro_estado.json`), cooldown global (15s), anti-órfão automático. Comunicação via arquivos de comando `runtime/maestro_cmd_<id>.json`.

## Responsabilidades

- Singleton central: evita duplicatas de serviços
- Cooldown central: reinícios respeitam 15s global
- Anti-órfão: detecta e mata duplicatas automaticamente
- Fallback seguro: modo degraded se cair, sistema nunca trava
- Fase 1 (observador): registra e compara, não bloqueia

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[ponto-unico-de-persistencia-gate]] — gate de persistência que o Maestro respeita
- [[maestro-fase-ativa-fix-registro-e-stale-pid]] — aprendizado sobre ativação do Maestro
- [[00-system-rules]] — Constituição que o Maestro faz cumprir
- [[11-ler-executor]] — executor LER que consulta o Maestro

## Ver também

- [[01-estrategista]] — define direção, o Maestro executa
- [[09-executor]] — executores sob coordenação do Maestro