---
tipo: decisao
tags: [jarvis, widget, pywebview, ui, voz, microfone, controle-flutuante, ipc, python-driven]
data: 2026-08-10
contexto: "Precisava de uma janela flutuante (always-on-top, sem bordas, arrastável) para controle visual da narração do Jarvis no PC, com interrupção de fala, toggle de voz e toggle de microfone, integrada globalmente ao opencode e online em tempo real."
decisao: "Arquitetura Python-Driven (robusta, backend-independente): janela flutuante pywebview SEM js_api. Python->JS: poller thread (250ms) chama win.evaluate_js('applyState(JSON)') para atualizar DOM. JS->Python: onclick escreve localStorage['jarvis_click']; poller lê via win.evaluate_js. Drag: JS escreve screenX/Y no localStorage; Python chama win.move. Refatorado em 10/08 — mesmo padrão de widget_grafo.py (frameless, easy_drag=False, on_top=True, bg). _dispatch rotas: fala->interromper (jarvis_audio stop), voz->toggle (jarvis_audio on/off), mic->toggle (dialogo vad), close->destroy. py_compile OK. Launch via controle.bat + pythonw."
impacto: "TESTE E2E 100% PASSOU (in-proc, mesma janela+poller): (1) applyState existe e atualiza lblVoz/btnVoz/info (inclui emoji) em tempo real; (2) clique JS escreve localStorage['jarvis_click']; (3) poller Python detecta a cada 250ms e chama _dispatch; (4) _dispatch('fala') roda cmd_interromfer_fala -> jarvis_audio stop -> narracao_estado.json ativo=False (verificado). Janela visível em (26,26) 204x245, WebView2 filho ativo, log vazio. PID 6712. Aprendido: pywebview isola localStorage POR PROCESSO (teste cross-process NAO compartilha localStorage; so funciona in-proc onde a janela e o poller saom o mesmo processo). Bug do emoji U+1F50A no console cp1252 e falso negativo no teste (applyState funciona; o print que falha). Typo 'ler_estado_vou' corrigido para 'ler_estado_voz'."
---
# Aprendizado: Widget flutuante de controle Jarvis (pywebview) — Arquitetura Python-Driven

## Problema
O Jarvis narra em áudio (via `narrador_desktop.py` + `vox_audio.py`) e escuta via
`dialogo.py --modo vad`, mas o controle era feito apenas por atalho (Pause/Break)
ou comandos de voz (`AT ECO`/`DT ECO`/...). Faltaava um controle visual sempre
visível e em tempo real.

## Solução
Janela flutuante pywebview (`scripts/widget_controle_jarvis.py`) com:
- Barra superior draggable (`<div class="drag">`) com fechamento (✕)
- 3 botões: **Voz** (toggle via `jarvis_audio.py`), **Parar Fala** (STOP via
  `interromper_fala`), **Mic** (toggle inicia/para `dialogo.py --modo vad`)
- Arquitetura Python-Driven: poller Python (250ms) empurra estado via
  `win.evaluate_js("applyState(JSON)")`; cliques JS vão para `localStorage`
  e o poller Python detecta via `win.evaluate_js("localStorage.getItem(...)")`
- Posição persistida em `runtime/widget_controle_geometria.json`

## Arquitetura Python-Driven (decisão 10/08)
Motivo: pywebview 6.2.1 + WebView2 — `js_api=Bridge()` é unreliable; `shadow=False`
quebra a bridge. Solução: **`evaluate_js` (Python→JS) + `localStorage` (JS→Python)**
são confiáveis. O poller roda em thread daemon dentro do mesmo processo da janela,
compartilhando o mesmo localStorage do WebView2.

| Direção | Mecanismo | Exemplo |
|---|---|---|
| Python→JS | `win.evaluate_js("applyState(JSON)")` | Atualiza btnVoz, lblVoz, info, swVoz/swMic |
| JS→Python | `localStorage['jarvis_click'] = 'fala'` | onclick → poller detecta a cada 250ms → `_dispatch` |
| JS→Python | `localStorage['jarvis_move'] = JSON` | drag → poller lê → `win.move(x,y)` |

### _dispatch (roteamento de cliques)
- `voz` → `cmd_voz(not (ativo and not pausado))` → `jarvis_audio.py on/off`
- `fala` → `cmd_interromper_fala()` → `jarvis_audio.py stop` → `cmd_stop` → `gravar(ativo=False, pausado=True)`
- `mic` → `cmd_mic(not mic_ativo())` → inicia/para `dialogo.py --modo vad`
- `close` → `win.destroy()`

## Decisões-chave reaproveitadas do ecossistema
| Recurso | Padrão herdado |
|---|---|
| Janela flutuante | `widget_grafo.py`: `create_window(frameless, easy_drag, bg, on_top)` |
| Drag customizado | JS `mousemove` → `localStorage.jarvis_move` → `win.move` |
| Atomic write | `tmp + replace` (igual `jarvis_audio.gravar`) |
| Detached process | `DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP` |
| Estado de voz | REUSADO `runtime/narracao_estado.json` + `jarvis_audio.py` CLI |
| Estado de microfone | NOVO `runtime/mic_estado.json` + `runtime/mic.pid` |

## Controle de microfone
- `mic_on()`: `Popen(dialogo.py --modo vad, DETACHED)`, salva PID em `runtime/mic.pid`
- `mic_off()`: `taskkill /PID /F /T`, limpa arquivo
- `mic_ativo()`: lê `mic_estado.json` + verifica PID vivo via `tasklist /FI PID eq`

## TESTE E2E (in-proc) — 100% PASSOU
Teste in-proc (mesma janela + poller no mesmo processo):
1. **applyState existe** → `typeof window.applyState == 'function'` ✓
2. **applyState voz ON** → `lblVoz.textContent == 'ON'`, `btnVoz.className` contém 'btn on' ✓
3. **applyState tts_ativo** → `info.textContent == '🔊 FALANDO'`, `className == 'info falando'` ✓
4. **Clique btnFala** → `localStorage['jarvis_click'] == 'fala'` ✓
5. **Poller detecta** → localStorage limpo em ~250ms ✓
6. **cmd_executed** → `narracao_estado.json` mudou para `{ativo: false, pausado: true}` ✓

## Aprendizos críticos
1. **pywebview isola localStorage POR PROCESSO** — não há compartilhamento entre
   janelas de processos diferentes (mesmo file:// origin). Teste cross-process
   (janela separada → ler localStorage do widget real) FALHA. Apenas funciona
   in-proc: a janela de teste DEVE ser criada pelo mesmo processo que roda o poller.
2. **Emoji U+1F50A no console cp1252** — `evaluate_js` retorna corretamente `🔊 FALANDO`
   (UTF-8 no WebView2), mas `print()` no console Windows cp1252 lança
   `UnicodeEncodeError`. Fix: `sys.stdout.reconfigure(encoding='utf-8')` no script
   de teste. Não afeta o widget real (a UI renderiza o emoji perfeitamente).
3. **`evaluate_js` não permite `return` no top-level** — usar IIFE `(function(){...})()`.

## Estado atual
- PID 6712 (pythonw widget), janela visível em (26,26) 204x245
- WebView2 child PID 10964 (msedgewebview2)
- `widget_err.log` vazio (sem erros)
- Launch via `scripts/controle.bat` → `pythonw widget_controle_jarvis.py`
