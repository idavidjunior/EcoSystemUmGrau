---
tags: [deploy opencode, mapear, matrizes, opencode, opencodeopencodeopencodeopencodeopencodeopencodeopencodeopen, padrao]
aliases: [Aprendizado: Skill auditoria-de-codigo (auto-evolutiva)]
date: 2026-08-10
---

# Aprendizado: Skill auditoria-de-codigo (auto-evolutiva)

**Fonte:** opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode

## Resumo

Criada skill declarativa de auditoria de código com auto-evolução, espelhada no
deploy do opencode.

## Padrões consolidados

1. **Bugs são encontrados pelo fluxo, não pela leitura** — mapear matrizes
   `chave → grava → lê → status` (localStorage), `gatilho → handler → efeito`
   (eventos), `origem → destino` (funções).
2. **Ferramentas autoritativas** — `py_compile`, `node --check` por bloco
   isolado, contagens regex e bytes hex; nunca confiar no display de arquivos.
3. **Corrigir no fonte** — editar o gerador, rebuild, revalidar; artefato gerado
   é sombra.
4. **Dado vs código** — sintoma persistente pode ser dado ruim de fonte externa
   (vault/notas), não bug do gerador; separar e reportar.
5. **Efeitos colaterais** — cada correção contra o resto (restore vs init,
   reset vs defaults, toggle vs layout, `!important` vs inline, timing de
   animações).

## Mecanismo de auto-evolução

- Ao fim de cada auditoria: `memory_engine.py add`, arquivo em
  `conhecimento/aprend
## Conexoes

- [[2026-08-03-adb-remoto-via-tailscale-script-automatico-de-rot]]
- [[cluster-hub-ecossistema]]
- [[compreensao-de-pedidos-refino-com-a-llm-do-opencode-primaria]]
- [[config-2026-07-28-formato-correto-do-mcp-no-opencode-1187]]
- [[eco-agente-e-comando-global]]
- [[padrao-hub-padroes]]