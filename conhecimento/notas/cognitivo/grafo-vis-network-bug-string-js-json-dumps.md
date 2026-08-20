---
tags: [atualiza, cognitivo, general, invalida, todo, vault]
aliases: [grafo vis network bug string js json dumps]
date: 2026-08-20
---

# grafo vis network bug string js json dumps

**Dominio:** general

---
tipo: erro
tags:
  - obsidian
  - grafo
  - html
  - js
  - vis-network
  - debugging
  - gerador
data: 2026-08-02
contexto: Geramos docs/grafo.html com vis-network para visualizar o conhecimento como grafo. A pagina renderizava header/legenda mas o canvas ficava vazio.
decisao: Diagnosticado via headless Chrome + Node. Causa raiz: um no (label "Why - User expects a blank slate...") continha quebra de linha literal dentro de string JS delimitada por aspas simples -> sintaxe invalida em TODO 

---
tipo: aprendizado
tags: [grafo, vis-network, fisica, barnesHut, movimento-organico, cerebro-vivo, sinapses, widget]
data: 2026-08-04
contexto: Usuario pediu refinamento do widget do grafo do conhecimento: movimento organico perpetuo (stabilization:false + barnesHut com timestep lento), respiracao do layout e "pulse" de sinapses (arestas brilham quando o vault atualiza).
decisao: Implementado em scripts/generate-graph-html.py (bloco JS do grafo gerado): physics.stabilization=false + minVeloci
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]