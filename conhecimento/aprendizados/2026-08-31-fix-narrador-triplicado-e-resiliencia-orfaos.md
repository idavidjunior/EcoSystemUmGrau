---
tipo: decisao
tags: [narrador, thread-singleton, anti-orfao, watchdog, resiliencia]
data: 2026-08-31
contexto: |
  Narrador do widget_edge.py repetia cada evento 3x no log e potencialmente
  falava 2-3x (TTS dedup mitigava parcialmente). Bug afetava UX do narrador
  e gerava ruído operacional no diagnóstico.
decisao: |
  Causa raiz: main() e poller() do widget_edge.py criavam 2 threads narradoras
  independentes — variável `narrador_thread` do poller era local e nunca
  recebia a referência da thread iniciada pelo main, então o poller sempre
  achava "narrador_thread is None" e criava outra. Cada thread chamava
  `_flush()` para as mesmas partes do SQLite.

  Fix em 3 camadas:
  1. Singleton thread-safe por PID: `_NARRADOR_LOCK` + `_NARRADOR_INSTANCIA` +
     `iniciar_narrador_thread()` como porta única (substitui criação direta
     de Thread em main e poller).
  2. Dedup em memória: set `vistos` com (ts, texto[:80]) evita log triplo
     mesmo em race entre duas threads que escapem do singleton.
  3. Resiliência sistêmica: `cleanup_duplicate_scripts()` no system_guardian
     detecta PIDs duplicados de scripts críticos (widget_edge, jarvis_bridge,
     tts_service, dialogo, system_guardian) e mata o mais novo, exceto se for
     o dono registrado no pid_file.

  Heartbeat agora inclui `tid` para diagnóstico futuro.
impacto: |
  - Narrador loga 1x por evento (era 1-3x).
  - Narrador fala 1x por evento (já estava parcialmente coberto por dedup
    em disco, mas agora a fonte do problema some).
  - system_guardian mata processos órfãos do mesmo script automaticamente
    a cada check_and_act — qualquer regressão futura que duplique PIDs
    é auto-corrigida.
  - Detectou bug latente: PID 6548 (dono, ontem) + PID 10412 (órfão, hoje)
    coexistiam sem ninguém limpar.
testes: |
  - preflight_check.py: 76/76 passou
  - ast.parse em widget_edge.py e system_guardian.py: OK
  - iniciar_narrador_thread() chamado 3x: True, False, False
  - cleanup_duplicate_scripts() em ambiente real: detectou 2 widget_edge,
    manteve o dono do pid_file (6548), marcou 10412 como órfão
reversibilidade: |
  Toda alteração é interna. Não muda contratos externos (não alterei
  nenhum endpoint, schema JSON nem PID file). Rollback = git revert.
arquivos_alterados:
  - scripts/widget_edge.py (singleton narrador + dedup memoria + heartbeat tid)
  - scripts/system_guardian.py (cleanup_duplicate_scripts + hook em check_and_act)
