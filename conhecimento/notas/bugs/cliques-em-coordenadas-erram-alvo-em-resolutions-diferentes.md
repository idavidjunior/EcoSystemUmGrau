---
tags: [bug, treinamentonavegacao]
aliases: [Cliques em coordenadas erram alvo em resolutions diferentes]
date: 2026-07-28
---

# Bug: Cliques em coordenadas erram alvo em resolutions diferentes

**Projeto:** treinamento_navegacao

## Causa Raiz
Coordenadas absolutas nao escalam entre dispositivos ou janelas redimensionadas

## Correcao
Calcular coordenadas como porcentagem da viewport: x = viewportWidth * 0.5, y = viewportHeight * 0.75; obter viewport via window.innerWidth/innerHeight
