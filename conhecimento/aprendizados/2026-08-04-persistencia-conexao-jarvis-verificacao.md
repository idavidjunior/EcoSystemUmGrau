---
tipo: padrao
tags: [jarvis, bridge, persistencia, conexao, watchdog, tailscale, voxumgrau, verificacao]
data: 2026-08-04
contexto: Usuario pediu para verificar a conexao com o Jarvis. Constatado que a bridge havia morrido e o watchdog estava travado desde 07:29 (7h sem reescrever o log). A dificuldade real identificada pelo usuario e a PERSISTENCIA da conexao.
decisao: Para garantir que o Jarvis fique sempre disponivel mesmo apos longos periodos sem conversa: (1) o watchdog.ps1 deve permanecer rodando para reiniciar a bridge (8765) e o serve (8767); (2) ao verificar a conexao, conferir Bridge escutando + Celular conectado via Tailscale + estado persistido em scripts/bridge_estado.json; (3) o app VoxUmGrau conecta via WebSocket sobre Tailscale, independente de ADB.
impacto: Bridge reiniciada (PID 7736) e watchdog reiniciado (PID 7848), ambos Responding. Celular (100.64.71.9) reconectou sozinho ao trazer o app para o primeiro plano (2 conexoes established na porta 8765, log 'conectado de 100.64.71.9 hist=53'). Verificacao 100% OK.
---

# 2026-08-04: Persistencia da conexao do Jarvis

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
Get-NetTCPConnection -LocalPort 8765 -State Established
# 3. Estado persistido da ultima conexao
Get-Content scripts\bridge_estado.json
# 4. Watchdog vivo?
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'watchdog' }
```

## Observacoes / pendencias
- Se o watchdog travar de novo, matar o processo (Stop-Process) e reiniciar via:
  `Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',"`$PSScriptRoot\watchdog.ps1`" `
- O app Android desconecta ao ir para background — reconexao automatica e responsabilidade do app (abrindo o app, ele reconecta sozinho).
- O usuario enfatizou: NAO duplicar aprendizados curtos/irrelevantes no log da bridge; registrar apenas o essencial.
