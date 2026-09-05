---
tags: [aprende, crescer, enquanto, ler, opencode, padrao]
aliases: [widget desktop grafo tempo real]
date: 2026-08-04
---

# widget desktop grafo tempo real

**Fonte:** opencode

Tipo: padrao

Tags: [grafo, cerebro-vivo, widget, pywebview, tempo-real, javascript-bridge]

Data: 2026-08-02

Contexto: Usuario pediu um widget desktop para ver o grafo do conhecimento em tempo real, acompanhando o cerebro crescer enquanto o LER aprende.

Decisão: Criado scripts/widget_grafo.py que abre docs/grafo.html numa janela pywebview e injeta um bloco JS de bridge. O JS chama window.pywebview.api.versao() a cada 2s; a versao e uma string composta pelos mtime_ns de knowledge_graph.json, do maior mtime sob conhecimento/ e do proprio grafo gerado. Se a versao muda, a pagina recarrega com cache-bypass (v=ts na URL).

Impacto: Janela desktop em tempo real do cerebro vivo sem re-abrir o navegador. Padrao reutilizavel: pywebview.js_api resolve JS<->Python no mainloop, sem conflito de threads; versao por mtime e simples, barata e suficiente.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]