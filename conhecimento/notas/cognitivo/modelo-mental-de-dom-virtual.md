---
tags: [cognitivo, web-rendering]
aliases: [Modelo mental de DOM virtual]
date: 2026-07-30
---

# Modelo mental de DOM virtual

**Dominio:** web-rendering

SPAs (React/Vue/Angular) mantem DOM virtual que difere do DOM real. Mudancas de estado nao sao imediatamente visiveis no DOM real. Esperar pelo menos 1 ciclo de renderizacao (requestAnimationFrame ~16ms) apos cada acao antes de consultar o DOM
