---
tipo: padrao
tags: [saudacao, jarvis, auto-evolucao, frases_manager, autonoma]
data: 2026-08-18
contexto: >
  Sistema de saudacao dinamica precisava evoluir sem dependencia de LLM.
  Usuario queria que Jarvis gerasse novas frases por conta propria,
  como escolha livre e espontanea, nao por comando externo.
decisao: >
  Integrar auto-geracao direto na funcao saudacao_dinamica().
  Quando pool do periodo atinge 75% de uso, Jarvis combina templates
  e complementos para criar novas frases automaticamente.
  Pool cresce de 10 para 40 frases por periodo. Sem LLM, sem
  comando externo, sem intervencao humana.
impacto: >
  Jarvis agora e verdadeiramente autonomo nas saudacoes.
  Auto-replica repertório quando sente que esta ficando repetitivo.
  Zero dependencia externa para evolucao.
---

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]