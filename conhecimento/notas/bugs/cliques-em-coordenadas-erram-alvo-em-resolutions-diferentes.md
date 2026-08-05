---
tags: [bug, diferentes, janelas, projeto, redimensionadas, treinamentonavegacao]
aliases: [Cliques em coordenadas erram alvo em resolutions diferentes]
date: 2026-08-05
---

# Cliques em coordenadas erram alvo em resolutions diferentes

**Projeto:** treinamento_navegacao

## Causa Raiz
Coordenadas absolutas nao escalam entre dispositivos ou janelas redimensionadas

## Correcao
Calcular coordenadas como porcentagem da viewport: x = viewportWidth * 0.5, y = viewportHeight * 0.75; obter viewport via window.innerWidth/innerHeight
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-navegacao]]
- [[css-selector-priority-ladder]]
- [[dom-element-hierarchy-mapping]]
- [[iframecontenteditable-text-entry]]
- [[spa-navigation-detection]]