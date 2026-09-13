---
tipo: padrao
tags: [cerebro-vivo, rotacao, zero, bug, ajuste]
data: 2026-09-12
contexto: Usuário reportou que ao colocar Rotação = 0% no painel Ajustes, o grafo continuava girando devagar.
decisao: No loop principal laco() (linha 1450 do cerebro.html), o rotAlvo tinha base 0.0015 sempre presente: `0.0015 + (AJUSTES.rotacao || 0.6) * 0.0045`. Corrigido para: `AJUSTES.rotacao > 0 ? (0.0015 + AJUSTES.rotacao * 0.0045) : 0`. Agora rotação 0% = rotação zero real (grafo para completamente).
impacto: Slider de Rotação no painel Ajustes funciona corretamente: 0% = parado, >0% = gira proporcional.
reutilizavel: Sim. Para qualquer parâmetro que deve zerar de verdade: usar ternário explícito `valor > 0 ? calculo : 0` em vez de base fixa + multiplicador.