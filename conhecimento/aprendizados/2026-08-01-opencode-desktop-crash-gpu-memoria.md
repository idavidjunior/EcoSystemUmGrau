# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memÃ³ria

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

InvestigaÃ§Ã£o exaustiva do ciclo de vida do `OpenCode.exe`:

1. **Logs do app** em `%APPDATA%\ai.opencode.desktop\logs\<sessao>\`:
   - `window.log` â†’ `app render process gone { url: 'oc://renderer/index.html', details: { reason: 'crashed', exitCode: -1 } }`
   - `utility.log` â†’ `child process gone { type: 'GPU', reason: 'crashed', exitCode: -1 }` (vÃ¡rias vezes)
   - `main.log` terminava em `server ready`, ou seja, o sidecar Node iniciava, mas o renderer caÃ­a.
2. **Event Log do Windows** â€” sem WER (Windows Error Reporting) do OpenCode; o adb.exe crashando era ruÃ­do (Android platform-tools).
3. **DiagnÃ³stico raiz**: GPU Intel HD 5500 com driver de 2015 Ã© incompatÃ­vel com Chromium/Electron moderno â†’ o **processo GPU crasha** â†’ derruba o **processo renderer** â†’ a janela some/janela branca.
4. **Segunda causa**: RAM fÃ­sica de 3,9 GB com sÃ³ ~0,6 GB livre (OpenCode CLI ~700 MB + VS Code ~500 MB + desktop ~650 MB + Defender) â†’ pressÃ£o de memÃ³ria â†’ Windows encerra processos â†’ app fecha "limpo" (sem crash logs: ausÃªncia de `utility.log`/`window.log`).

## CorreÃ§Ãµes aplicadas

1. **Flags de GPU desabilitadas** em TODOS os atalhos do OpenCode:
   `--disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox`
   - Atalhos corrigidos: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\OpenCode.lnk`, `%USERPROFILE%\Desktop\OpenCode.lnk`, `%USERPROFILE%\Desktop\OpenCode (2).lnk`.
   - Resultado: eliminou o crash de GPU/renderer. App abriu e permaneceu aberto (11+ min de teste, 914 cores distintas na captura = UI renderizada).
2. **Pagefile aumentado** de ~5,9 GB (auto) para **8192 MB fixo** (`Win32_PageFileSetting` + `AutomaticManagedPagefile=$false`):
   - Commit total (RAM+pagefile) subiu para ~9,7 GB â†’ aliviou a pressÃ£o de memÃ³ria que fechava o app "limpo".
   - ExpansÃ£o total entra em vigor apÃ³s reboot; parte jÃ¡ vale em runtime.
3. **GuardiÃ£o preventivo** `scripts/opencode_desktop_guardian.ps1`: monitora a janela/renderer do desktop, detecta crash ou memÃ³ria crÃ­tica e reinicia com as flags corretas (auto-heal).

## Resultados

- App abriu, renderizou a UI e permaneceu estÃ¡vel por 11+ minutos (sem `utility.log`, sem `window.log`).
- Janela "OpenCode" respondendo (`MainWindowHandle` vÃ¡lido, `Responding=True`).
- Renderer ativo (`renderer.log` crescendo, sÃ³ `ResizeObserver loop` benigno).
- Commit de memÃ³ria saiu de 0,6 GB livre (RAM fÃ­sica) p/ 1,9 GB livre (virtual) com pagefile maior.

## PrÃ³ximos passos

- **Reboot necessÃ¡rio** para o pagefile chegar aos 8192 MB completos.
- **Atualizar o driverIntel** (ou considerar GPU dedicada) como soluÃ§Ã£o de longo prazo â€” driver de 2015 Ã© o gatilho do crash de GPU.
- Consiglio anterior a nÃ­vel de maestro: sempre que um app Electron/Chromium fechar "sem motivo" em GPU antiga, **primeira aÃ§Ã£o = rodar com `--disable-gpu`**; se persistir, checar pressÃ£o de RAM (pagefile + apps concorrentes).
- GuardiÃ£o registrado no Agente de Sistema/Vigilante para previnir reincidÃªncia.

## PadrÃµes/HeurÃ­sticas acionados

- `primeiro-scan-depois-intervencao` (logs antes de mexer)
- `metodo-dos-5-porques-5-why` (renderer crasha â†’ GPU crasha â†’ driver antigo)
- `projete-para-falha-nao-para-sucesso` (pagefile como folga)
- `log-de-fallback-para-diagnostico` (ausÃªncia de crash logs = encerramento externo, nÃ£o crash)

## Conexoes

- [[cluster-hub-ecossistema]]