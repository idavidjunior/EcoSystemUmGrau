# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memória

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

Investigação exaustiva do ciclo de vida do `OpenCode.exe`:

1. **Logs do app** em `%APPDATA%\ai.opencode.desktop\logs\<sessao>\`:
   - `window.log` → `app render process gone { url: 'oc://renderer/index.html', details: { reason: 'crashed', exitCode: -1 } }`
   - `utility.log` → `child process gone { type: 'GPU', reason: 'crashed', exitCode: -1 }` (várias vezes)
   - `main.log` terminava em `server ready`, ou seja, o sidecar Node iniciava, mas o renderer caía.
2. **Event Log do Windows** — sem WER (Windows Error Reporting) do OpenCode; o adb.exe crashando era ruído (Android platform-tools).
3. **Diagnóstico raiz**: GPU Intel HD 5500 com driver de 2015 é incompatível com Chromium/Electron moderno → o **processo GPU crasha** → derruba o **processo renderer** → a janela some/janela branca.
4. **Segunda causa**: RAM física de 3,9 GB com só ~0,6 GB livre (OpenCode CLI ~700 MB + VS Code ~500 MB + desktop ~650 MB + Defender) → pressão de memória → Windows encerra processos → app fecha "limpo" (sem crash logs: ausência de `utility.log`/`window.log`).

## Correções aplicadas

1. **Flags de GPU desabilitadas** em TODOS os atalhos do OpenCode:
   `--disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox`
   - Atalhos corrigidos: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\OpenCode.lnk`, `%USERPROFILE%\Desktop\OpenCode.lnk`, `%USERPROFILE%\Desktop\OpenCode (2).lnk`.
   - Resultado: eliminou o crash de GPU/renderer. App abriu e permaneceu aberto (11+ min de teste, 914 cores distintas na captura = UI renderizada).
2. **Pagefile aumentado** de ~5,9 GB (auto) para **8192 MB fixo** (`Win32_PageFileSetting` + `AutomaticManagedPagefile=$false`):
   - Commit total (RAM+pagefile) subiu para ~9,7 GB → aliviou a pressão de memória que fechava o app "limpo".
   - Expansão total entra em vigor após reboot; parte já vale em runtime.
3. **Guardião preventivo** `scripts/opencode_desktop_guardian.ps1`: monitora a janela/renderer do desktop, detecta crash ou memória crítica e reinicia com as flags corretas (auto-heal).

## Resultados

- App abriu, renderizou a UI e permaneceu estável por 11+ minutos (sem `utility.log`, sem `window.log`).
- Janela "OpenCode" respondendo (`MainWindowHandle` válido, `Responding=True`).
- Renderer ativo (`renderer.log` crescendo, só `ResizeObserver loop` benigno).
- Commit de memória saiu de 0,6 GB livre (RAM física) p/ 1,9 GB livre (virtual) com pagefile maior.

## Próximos passos

- **Reboot necessário** para o pagefile chegar aos 8192 MB completos.
- **Atualizar o driverIntel** (ou considerar GPU dedicada) como solução de longo prazo — driver de 2015 é o gatilho do crash de GPU.
- Consiglio anterior a nível de maestro: sempre que um app Electron/Chromium fechar "sem motivo" em GPU antiga, **primeira ação = rodar com `--disable-gpu`**; se persistir, checar pressão de RAM (pagefile + apps concorrentes).
- Guardião registrado no Agente de Sistema/Vigilante para previnir reincidência.

## Padrões/Heurísticas acionados

- `primeiro-scan-depois-intervencao` (logs antes de mexer)
- `metodo-dos-5-porques-5-why` (renderer crasha → GPU crasha → driver antigo)
- `projete-para-falha-nao-para-sucesso` (pagefile como folga)
- `log-de-fallback-para-diagnostico` (ausência de crash logs = encerramento externo, não crash)
