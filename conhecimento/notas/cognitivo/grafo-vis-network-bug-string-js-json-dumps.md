---
tags: [cognitivo, general, invalida, simples, sintaxe, todo]
aliases: [grafo vis network bug string js json dumps]
date: 2026-08-04
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
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]