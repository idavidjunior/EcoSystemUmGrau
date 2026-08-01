# opencode-desktop-renderer-crash-gpu-antiga-memoria-critica

**Sintoma:** OpenCode Desktop abre a janela e fecha logo em seguida, ou abre uma janela branca/vazia.
**Ambiente:** Windows 10, Intel HD Graphics 5500 (driver 10.18.15.4248 / 2015), 3,9 GB RAM.
**Versão:** OpenCode Desktop 1.18.10 (Electron 42.3.3).

## Causa raiz (dupla)

1. **Crash do processo GPU** (driver Intel antigo incompatível com Chromium novo)
   → derruba o processo **renderer** (`oc://renderer/index.html` reason: crashed, exitCode: -1)
   → a janela fica branca/vazia ou some.
2. **Pressão de memória** (RAM física 3,9 GB, ~0,6 GB livre)
   → Windows encerra processos para liberar RAM
   → o app fecha "limpo" (sem `utility.log`/`window.log` de crash).

## Como diagnosticar (ordem)

1. Abrir `%APPDATA%\ai.opencode.desktop\logs\<ultima-sessao>\`:
   - `window.log` presente + `renderer process gone { reason: 'crashed' }` → **renderer crash** (via GPU).
   - `utility.log` com `child process gone { type: 'GPU', reason: 'crashed' }` → **GPU crash** (causa raiz #1).
   - Sessão sem `window.log` e sem `utility.log`, mas `main.log` termina em `server ready` → **encerramento externo** (causa raiz #2 = memória, ou kill manual).
2. Confirmar memória: `Get-CimInstance Win32_OperatingSystem | FreePhysicalMemory` — se < ~1 GB, é pressão.
3. Confirmar GPU antiga: `Get-CimInstance Win32_VideoController | DriverDate` — driver de anos atrás = gatilho.

## Correção (definitiva, aplicada 2026-08-01)

1. **Atalhos com flags de GPU desabilitadas** (todos os `.lnk` do OpenCode):
   ```
   --disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox
   ```
   Elimina o crash do processo GPU e, em cascata, do renderer.
2. **Pagefile 8192 MB fixo** (`Win32_PageFileSetting`, `AutomaticManagedPagefile=$false`).
3. **Guardião** `scripts/opencode_desktop_guardian.ps1` (monitor + auto-heal).

## Resolução de longo prazo

- Atualizar o driverIntel HD Graphics (ou instalar GPU dedicada).
- Considerar RAM física extra (o limite de 3,9 GB é crônico neste hardware).

## Não faça

- Não reinstalar o app sem antes aplicar as flags de GPU (o crash é do Chromium, não do app).
- Não confundir crash de `adb.exe` (Android platform-tools) com o problema do OpenCode — são independentes.
- Não concluir "fechou limpo = bug do app" sem checar `FreePhysicalMemory`; pode ser o Windows matando por OOM.
