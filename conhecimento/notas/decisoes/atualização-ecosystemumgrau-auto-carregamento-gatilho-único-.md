---
tags: [boota, decisao, isolada, nele, opencode, tenha]
aliases: [Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Úni]
date: 2026-08-17
---

# Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Único "Eco"

**Fonte:** opencode

---
tipo: decisao
tags: [voz, eco, clausula-petrea, bridge, config, regras, autoload, runtime]
data: 2026-08-07
contexto: O usuário pediu que (1) a cada nova sessão, o EcoSystemUmGrau seja carregado automaticamente sem precisar pedir, operando estritamente dentro dele; e (2) a palavra-gatilho para ativar/desativar o sistema de voz seja apenas "Eco" (em vez de "Ativar Eco"/"Desativar Eco").
decisao: Atualizada a CLÁUSULA PÉTREA — ATIVAÇÃO DE VOZ — ECO SYSTEM na Constituição (config/agents/00-system-rules.md): (1) adicionada a seção "CARREGAMENTO AUTOMÁTICO TOTAL — ECO SYSTEM" garantindo que toda nova sessão boota via runtime_boot.py, restaura estado persistente, carrega memória episódica, kernel, context loader e auditor — nenhuma sessão é isolada; (2) simplificado o gatilho de "Ativar Eco" para apenas "Eco" (palavra única, case-insensitive). "Desativar Eco" mantido. Sincronizado via sync_rules.py update (9 regras nas 3 camadas: Constituição, AGENTS.md, deployed). Preflight: TODOS OS TESTES PASSARAM.
impacto: O EcoSystemUmGrau agora carrega automaticamente em toda nova sessão, operando como Runtime persistente. O gatilho "Eco" ativa o sistema de voz (TTS/STT via jarvis_bridge.py porta 8765). Reduzido atrito: o usuário não precisa digitar "Ativar Eco", apenas "Eco". O carregamento automático elimina a necessidade de pedidos explícitos para usar o ecossistema completo.
---

# Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Único "Eco"

## Pedido do usuário

1. **Auto-carregamento total:** "A cada nova sessão que eu abrir, você pode carregar sozinho, automaticamente e imediatamente o EcoSystemUmGrau e operar nele sem que eu tenha que pedir?"
2. **Gatilho simplificado:** "A cada nova sessão que eu falar ou digitar Eco, imediatamente o protocolo de operação será ativado."

## Implementação

### 1. Carregamento automático total (nova sessão)

Adicionada à Constituição a seção **"CARREGAMENTO AUTOMÁTICO TOTAL — ECO SYSTEM"** dentro da cláusula pétrea. Todo agente, ao iniciar qualquer sessão, deve:

1. **Boot via `runtime_boot.py`** — verifica integridade, restaura estado, carrega memória
2. **Estado persistente** de `runtime/state.json` (projeto ativo, objetivo, última tarefa, pendências)
3. **Memória episódica** via `memory_engine` (memórias consolidadas relevantes)
4. **Kernel permanente** (7 regras absolutas, pipeline 9 etapas)
5. **Context Loader** (`runtime_context.py`) — BM25 semântico, carrega apenas o relevante
6. **Auditoria** (`runtime_auditor.py`) — classifica criticidade, reprova e devolve ao ciclo

### 2. Gatilho "Eco" (palavra única)

Simplificado de "Ativar Eco" para apenas **"Eco"**:
- **Entrada:** usuário digita/fala "Eco" → confirma "Eco ativado. Sistema de voz online."
- **Saída:** TTS via `jarvis_bridge.py` (porta 8765, `pt-BR-AntonioNeural`)
- **Modo diálogo PC:** `python scripts/dialogo.py --modo vad` (background)
- **Desativar:** "Desativar Eco" → confirma e volta ao modo texto

## Sincronização (3 camadas)

`python scripts/sync_rules.py update`:
1. `config/agents/00-system-rules.md` (fonte única) — seção atualizada como CLÁUSULA PÉTREA
2. `AGENTS.md` — bloco RULES regenerado (9 regras)
3. `~/.config/opencode/agents/00-system-rules.md` — deploy sincronizado

## Validação

- `python scripts/sync_rules.py check` → **RESULTADO: 3 camadas consistentes**
- `python scripts/preflight_check.py` → **TODOS OS TESTES PASSARAM** (7/7: template, deployed, rollback, agents, regras, secrets, ético)
- `memory_engine.py add` → Memory #181 registrada

## Conexões

- [[2026-08-02-ativacao-eco-voz]]
- [[2026-08-07-runtime-boot-operacional]]

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]