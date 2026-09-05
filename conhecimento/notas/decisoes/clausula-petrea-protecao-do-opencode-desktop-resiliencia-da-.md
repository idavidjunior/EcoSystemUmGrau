---
tags: [adqu, automatico, decisao, fechar, opencode, restrito]
aliases: [Clausula Petrea: protecao do OpenCode desktop + resiliencia ]
date: 2026-08-06
---

# Clausula Petrea: protecao do OpenCode desktop + resiliencia da bridge

**Fonte:** opencode

## Regra imutavel (clausula petrea)
**Em hipotese alguma, o Windows ou qualquer outro processo automatico pode fechar o
OpenCode desktop. Somente o usuario pode, manualmente.**

- O desktop roda como `OpenCode.exe` em `@opencode-aidesktop`.
- O CLI roda como `opencode.exe` (serve na porta 8767, run em sessoes).

## Bug critico encontrado
O filtro antigo de orfaos do watchdog matava qualquer `opencode.exe` cujo comando
NAO contivesse " serve":
```powershell
$cmd -match "opencode\.exe run" -or ($cmd -match "opencode\.exe" -and $cmd -notmatch " serve")
```
O desktop (`OpenCode.exe`) casa no segundo criterio (nao tem " serve" no comando),
entao o proprio watchdog poderia derrubar o desktop. **Corrigido** com protecao
explicita por caminho (`opencode-aidesktop`) e filtro restrito a `opencode run`.

## Melhorias no watchdog.ps1
1. **Instancia unica via lock de PID** (`watchdog.lock`): substitui o Mutex nomeado,
   que no Windows fica "abandoned" quando o processo dono e morto e NAO e re-adqu
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]