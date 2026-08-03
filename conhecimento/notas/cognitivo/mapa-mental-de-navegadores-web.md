---
tags: [browser-architecture, cognitivo, composicao, dom, dominio, gpu]
aliases: [Mapa mental de navegadores web]
date: 2026-08-03
---

# Mapa mental de navegadores web

**Dominio:** browser-architecture

Navegadores modernos sao multi-processo: processo browser (UI), processo renderer (DOM/JS), processo GPU (composicao). Cada processo e isolado. Crash no renderer nao derruba o browser. Cada aba tem seu proprio processo renderer. DevTools roda no processo browser
## Conexoes

- [[cluster-hub-navegacao]]
- [[cognitivo-hub-cognitivo]]