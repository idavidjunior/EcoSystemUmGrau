---
tags: [daemon, monitor, opencode, padrao, ruim, silent]
aliases: [Resiliência de logs: encoding detectado na leitura, não pres]
date: 2026-08-22
---

# Resiliência de logs: encoding detectado na leitura, não presumido

**Fonte:** opencode

## Contexto
O caso "ap��s" no guardian_log revelou que o elo fraco nunca foi a gravação
(todos os 18 gravadores Python já usam UTF-8 explícito) e sim a leitura:
Get-Content do PS 5.1 assume ANSI sem BOM, redirecionamento `>` do PS grava
UTF-16, e leitores programáticos sem errors=replace crasham com 1 byte ruim.

## Solução em três camadas
1. scripts/ver_log.py — leitor único: BOM UTF-8/UTF-16 → UTF-8 estrito →
   fallback cp1252 com replace; última linha sem newline marcada como
   "gravacao interrompida"; filtros -n e --grep; stdout reconfigurado UTF-8.
2. Blindagem errors="replace" nos 6 pontos de leitura de conteúdo que
   crashariam (audit_engine ×2, adb_monitor_daemon ×2, adb_monitor_silent,
   adherence_audit).
3. Exit code honesto: opencode_resilience.py saía 1 até em limpeza bem-sucedida,
   fazendo o guardian logar "resilience falhou:" vazio. Agora só órfão adiado
   = exit 1; e o guardian inclui stdout/stderr na mensagem de erro.

## Regra prática
Nunca ler log do ecossistem
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]