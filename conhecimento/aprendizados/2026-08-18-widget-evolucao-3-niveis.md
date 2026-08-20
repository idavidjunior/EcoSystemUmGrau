---
tipo: decisao
tags: [widget, evolucao, microfone, narrador, dialogo, sistema, notificacoes]
data: 2026-08-18
contexto: >
  Widget Jarvis estava quebrado em 7+ bugs e so tinha botoes basicos.
  Usuario pediu evolucao completa em 3 niveis com logica de descarte
  de fala ao parar e reativar.
decisao: >
  Evolucao completa do widget em 3 niveis implementada no unified_bridge.py:
  Nivel 1 - Fixes: buffer aliasing (textos=list(buffer)), persistencia de
  posicao via _on_close antes de destruicao, tracking de sempre_topo e
  dimensoes reais (outerWidth/outerHeight). Nivel 2 - Funcionalidade:
  microfone via Web Speech API (webkitSpeechRecognition pt-BR), campo
  de texto para digitar comandos, texto falado em tempo real no info.
  Nivel 3 - Inteligencia: status CPU/RAM/disco via psutil, notificacoes
  em runtime/widget_notifs.json, modos narrador/dialogo/silencioso,
  historico de comandos em runtime/widget_history.json. Botao Repetir
  fala o ultimo resumo salvo. Logica buffer_descartado: ao clicar Parar
  Fala, flag buffer_descartado=True; ao reativar, flush_buffer descarta
  o conteudo antigo. Ultimo resumo preservado em ultimo_resumo.json.
impacto: >
  Widget passa de 220x284 para 280x420. Microfone funciona em Chromium.
  Modo silencioso desativa voz automaticamente. Narrador nao fala mais
  conteudo antigo apos parar e reativar.
---
