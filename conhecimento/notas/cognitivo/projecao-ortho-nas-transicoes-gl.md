---
tags: [1080x2400, cognitivo, general, multiplicacao, pos, proporcao]
aliases: [Projecao ortho nas transicoes GL]
date: 2026-08-21
---

# Projecao ortho nas transicoes GL

**Dominio:** general

﻿---
tipo: erro
tags: [opengl, transicoes, biblia, projecao, ortho]
data: 2026-08-19
contexto: Motor de transicoes OpenGL ES 2.0 do app BibliaEstudoCompleta
decisao: Trocar frustumM por orthoM(-1,1,-1,1,2,8) e remover a multiplicacao pos.x *= uOldAspect no shader
impacto: Pagina preenche a tela inteira sem distorcao; 4 efeitos validados no device
---

# Projecao ortho nas transicoes GL

## Problema
A pagina capturada tem a mesma proporcao da tela (1080x2400, aspect 0.45).
Com frustumM(-aspect, a
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]