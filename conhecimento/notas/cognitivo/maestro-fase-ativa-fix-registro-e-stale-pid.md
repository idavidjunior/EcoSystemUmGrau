---
tags: [clientes, cognitivo, general, intervenção, manual, recuperam]
aliases: [Maestro Fase Ativa - Fix Registro e Stale PID]
date: 2026-08-31
---

# Maestro Fase Ativa - Fix Registro e Stale PID

**Dominio:** general

﻿---
tipo: decisao
tags: [maestro, runtime, guardian, fase-ativa, stale-pid]
data: 2026-08-31
contexto: |
  Maestro de Runtime em fase ativa. Guardians consultam antes de iniciar servicos.
  Bug: Maestro nao verificava se PID registrado ainda estava vivo (confiava cego no campo vivo).
  Bug: Guardian nao registrava PID no Maestro apos iniciar servico.
decisao: |
  1. Adicionar verificacao de vida (psutil.pid_exists) no pode_iniciar() do Maestro.
     Se PID registrado morto, limpar registro stal

---
tipo: erro
tags: [maestro, runtime, resiliencia, pid, heartbeat]
data: 2026-09-04
contexto: O livro do Maestro mantinha serviços mortos e o PID persistido do daemon apontava para processo inexistente.
decisão: Reconciliar por PID e heartbeat, iniciar o daemon automaticamente com lock único e executar a autocura no boot completo.
impacto: Registros órfãos deixam de bloquear reinícios, o status informa a vida real do processo e clientes recuperam o Maestro sem intervenção manual.
---

O livro 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]