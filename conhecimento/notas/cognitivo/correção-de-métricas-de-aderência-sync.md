---
tags: [cognitivo, data, general, hora, retornando, yyyy]
aliases: [Correção de métricas de aderência (@sync)]
date: 2026-09-02
---

# Correção de métricas de aderência (@sync)

**Dominio:** general

## 1. Bug na métrica preflight_entregas (erro crítico)

Em `scripts/adherence_audit.py`, o `parse_git_log` usava `--date=short` no git log, retornando apenas a data do commit (YYYY-MM-DD) sem hora. O parse `datetime.strptime(c['date'], '%Y-%m-%d')` criava meia-noite do dia. A comparação `p < e['date']` então exigia preflight ANTES da meia-noite do dia do commit, excluindo todos os preflights do mesmo dia.

Resultado: de 4 entregas, só 1 contava como "com preflight" (25%) mesmo com 415+ execuções reais de preflight.

Correção: usar `--date=iso` no git log e `datetime.fromisoformat` (removendo tzinfo) para capturar o timestamp completo do commit. Métrica subiu de 25% para 100% (7d) e 92.3% (30d).

## 2. Métrica de inventário (15.8% -> 100%)

O `config/inventario_estruturas.json` não refletia 82 estruturas novas no disco. Rodar `scripts/inventory_manager.py sync` detectou e registrou automaticamente (scripts core, habilidades MCP, agentes). O item `test_widget_live.py` estava listado mas 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]