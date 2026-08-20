---
tipo: erro
tags: [widget, unified-bridge, auditeria, bugs, pywebview]
data: 2026-08-18
contexto: >
  Auditoria do widget Jarvis Controle (unified_bridge.py) identificou 7 bugs.
  Bug critico: ler_estado_voz() chamada mas nunca definida/importada.
  Causava NameError silencioso capturado por except:pass.
  UI nunca atualizava estado, botoes nao funcionavam.
decisao: >
  (1) Definir ler_estado_voz() lendo CONTROLE (narracao_estado.json).
  (2) Refatorar estado_ativo() para usar ler_estado_voz().
  (3) Toggle voz: calcula novo_ativo antes de escrever, sem variavel morta.
  (4) Botao fala: alterna pausado (antes so pausava). Só escreve parar_fala ao pausar.
  (5) Close: trocar os._exit(0) por _release_lock() + sys.exit(0).
  (6) FindWindowW: usar constante TITLE em vez de string hardcoded.
impacto: >
  Widget agora funciona corretamente. Botoes voz/fala alternam estado.
  Lock e liberado ao fechar. Titulo da janela e configuravel.
---
