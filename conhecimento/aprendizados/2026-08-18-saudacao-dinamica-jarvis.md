---
tipo: padrao
tags: [saudacao, frases_manager, unified-bridge, personalidade, tts]
data: 2026-08-18
contexto: >
  Usuario queria saudacao mais humana e dinamica para o Jarvis.
  Sistema atual usava LLM para gerar saudacoes (complexo, lento).
  Queria algo casual, amigavel, dinamico, contextual, nao prolixo.
decisao: >
  Criar funcao saudacao_dinamica() no frases_manager.py.
  Baseada em: hora do dia (4 periodos), anti-repeticao no dia,
  deteccao de reconexão (<30min). Frases curtas com personalidade.
  Integrada ao unified_bridge.py: fala ao ativar narracao pela 1a vez.
impacto: >
  Jarvis agora cumprimenta de forma natural e variada.
  Anti-repeticao garante que nao fale a mesma frase no dia.
  Sem dependencia de LLM para saudacao inicial.
---
