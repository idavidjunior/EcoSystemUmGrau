---
tipo: decisao
tags: [jarvis, widget, pywebview, ui, voz, microfone, controle-flutuante, ipc]
data: 2026-08-10
contexto: "Precisava de uma janela flutuante (always-on-top, sem bordas, arrastável) para controle visual da narração do Jarvis no PC, com interrupção de fala, toggle de voz e toggle de microfone, integrada globalmente ao opencode e online em tempo real."
decisao: "Criado scripts/widget_controle_jarvis.py: janela flutuante pywebview (mesmo padrao de widget_grafo.py) com Bridge js_api bidirecional. Reaproveita jarvis_audio.py (on/off/stop) e runtime/narracao_estado.json para voz; cria runtime/mic_estado.json + runtime/mic.pid + dialogo.py --modo vad para microfone. Polling de 1s do estado real via setInterval JS → bridge.ler_estado(). Registrado comando '$ controle' no opencode.jsonc (template + deployed) usando {{USERPROFILE}} path variables. pywebview usa 'on_top=True' (nao 'topmost') e 'frameless=True' + 'easy_drag=False' (drag customizado pela barra superior em JS, igual ao widget_grafo)."
impacto: "Usuario tem controle visual flutuante e em tempo real sobre voz (ON/OFF), parada de fala (STOP) e microfone (ON/OFF), integrado ao ecossistema via arquivos de estado compartilhados. Estado refletido instantaneamente por polling. Preflight aprovado (TODOS TESTES PASSARAM). py_compile OK. Janela abriu e manteve-se estável 6s no teste."
---
# Aprendizado: Widget flutuante de controle Jarvis (pywebview)

## Problema
O Jarvis narra em áudio (via `narrador_desktop.py` + `vox_audio.py`) e escuta via
`dialogo.py --modo vad`, mas o controle era feito apenas por atalho (Pause/Break)
ou comandos de voz (`AT ECO`/`DT ECO`/...). Faltaava um controle visual sempre
visível e em tempo real.

## Solução
Janela flutuante pywebview (`scripts/widget_controle_jarvis.py`) com:
- Barra superior draggable (`<div class="drag">`) com fechamento (✕)
- 3 botões: **Voz** (toggle via `jarvis_audio.py`), **Parar Fala** (STOP via
  `matar_tts_ativo`), **Mic** (toggle inicia/para `dialogo.py --modo vad`)
- Polling de 1s: JS → `bridge.ler_estado()` → atualiza UI com o estado REAL
  (`narracao_estado.json` + `mic_estado.json` + alive check de PIDs)
- Posição persistida em `runtime/widget_controle_geometria.json`

## Decisões-chave reaproveitadas do ecossistema
| Recurso | Padrão herdado |
|---|---|
| Janela flutuante | `widget_grafo.py`: `pywebview.create_window(frameless, easy_drag, bg)` |
| js_api Bridge | `widget_grafo.py Bridge`: métodos async chamados via `window.pywebview.api.x()` |
| Drag customizado | JS `mousemove` → `bridge.mover(x,y)` (screenX/Y) |
| Atomic write | `tmp + replace` (igual `jarvis_audio.gravar`) |
| Detached process | `DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP` (igual `jarvis_audio.iniciar_narrador`) |
| Estado de voz | REUSADO `runtime/narracao_estado.json` + `jarvis_audio.py` CLI (fonte única) |
| Estado de microfone | NOVO `runtime/mic_estado.json` + `runtime/mic.pid` (mesma convenção `runtime/*.json`) |
| Always-on-top | `on_top=True` (a API do pywebview local usa `on_top`, NÃO `topmost`) |
| Comando global | `$ controle` no `opencode.jsonc` (template `!\`python …\`` igual aos demais) |

## Controle de microfone (novo)
- `mic_on()`: `Popen(dialogo.py --modo vad, DETACHED)`, salva PID em `runtime/mic.pid`
- `mic_off()`: `taskkill /PID /F /T` pelo PID, limpa arquivo
- `mic_ativo()`: lê `mic_estado.json` + verifica PID vivo via `tasklist /FI PID eq`
  (mesmo algoritmo de `jarvis_audio.narrador_rodando`)

## Integração global / tempo real
- Estado compartilhado por arquivos JSON → mudanças feitas via CLI (`jarvis_audio.py`)
  ou atalho (`hotkey_pause_win32.py`) refletem no widget em ≤1s.
- Comando `controle` disponível no opencode (CLI/desktop).
- Não abre outra sessão: o widget é apenas uma VISÃO do estado real.
