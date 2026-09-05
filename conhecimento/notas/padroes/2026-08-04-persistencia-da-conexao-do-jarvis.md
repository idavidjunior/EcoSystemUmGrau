---
tags: [cair, limpa, opencodeopencodeopencodeopencodeopencode, orfaos, padrao, reinicia]
aliases: [2026-08-04: Persistencia da conexao do Jarvis]
date: 2026-08-04
---

# 2026-08-04: Persistencia da conexao do Jarvis

**Fonte:** opencode+opencode+opencode+opencode+opencode

## Diagnostico
- Watchdog travado desde 07:29 (log parado ~7h), nao reiniciava nem a bridge nem o serve.
- Bridge morta na porta 8765; serve morto na 8767.
- App VoxUmGrau desconecta quando vai para background (WebSocket nao se mantem em 2o plano).

## Persistencia (garantia de disponibilidade)
- **Watchdog** (`scripts/watchdog.ps1`): a cada 20s testa bridge (porta 8765) e serve (porta 8767, health com auth Basic), reinicia se cair, limpa orfaos do OpenCode.
- **Atalho de inicializacao**: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EcoSystemUmGrau-Watchdog.lnk` aponta para `powershell.exe -WindowStyle Hidden -File watchdog.ps1` — inicia junto com o Windows.
- **Celular**: conecta por WebSocket via rede Tailscale (IP fixo 100.64.71.9 -> 100.91.141.101:8765), sem depender de ADB/USB, funciona em WiFi ou dados moveis.

## Procedimento de verificacao rapida
```powershell
# 1. Bridge escutando?
Get-NetTCPConnection -LocalPort 8765 -State Listen
# 2. Celular conectado agora?
Get
## Conexoes

- [[cluster-hub-ecossistema]]
- [[integrity-guard-vigilante-dados]]
- [[padrao-hub-padroes]]