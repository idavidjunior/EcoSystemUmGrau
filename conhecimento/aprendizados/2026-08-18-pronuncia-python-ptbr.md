---
tipo: padrao
tags: [pronuncia, python, pt-br, tts, pronuncias.json]
data: 2026-08-18
contexto: >
  Usuario pediu que Python seja pronunciado como "páiton" em portugues,
  nao em ingles. O glossario_tecnico.json listava Python como termo tecnico
  em ingles, mas o PronunciationEngine do SpeechPipeline tem prioridade
  quando existe entrada em pronuncias.json.
decisao: >
  Adicionar "python": {"fala": "páiton"} ao pronuncias.json.
  O PronunciationEngine aplica substituicao de texto puro antes de enviar
  ao edge-tts, que suporta apenas substituicao de texto (nao SSML custom).
impacto: >
  Python agora e pronunciado "páiton" em todo o ecossistema TTS.
  Funciona automaticamente no unified_bridge.py e jarvis_bridge.py.
---

## Conexoes

- [[cluster-hub-programacao]]
- [[norma-culta-x-coloquial-no-pt-br-quando-usar-cada-registro-n]]
- [[python-sintaxe-e-núcleo-da-linguagem]]