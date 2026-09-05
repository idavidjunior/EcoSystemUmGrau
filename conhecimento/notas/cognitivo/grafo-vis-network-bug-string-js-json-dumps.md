---
tags: [cognitivo, general, inicializava, invalida, sintaxe, todo]
aliases: [grafo vis network bug string js json dumps]
date: 2026-08-04
---

# grafo vis network bug string js json dumps

**Dominio:** general

Tipo: erro

Tags: , obsidian, grafo, html, js, vis-network, debugging, gerador

Data: 2026-08-02

contexto: Geramos docs/grafo.html com vis-network para visualizar o conhecimento como grafo. A pagina renderizava header/legenda mas o canvas ficava vazio.

decisao: Diagnosticado via headless Chrome + Node. Causa raiz: um no (label "Why - User expects a blank slate...") continha quebra de linha literal dentro de string JS delimitada por aspas simples -> sintaxe invalida em TODO o script -> vis-network nem inicializava. Tambem usavamos template literal (`title:`...`) que quebra com crase ou ${ }. Corrigido montando nodes/edges via json.dumps(ensure_ascii=False) que escapa qualquer caractere corretamente. Segundo problema: lib via CDN unpkg nao carrega em file:// (bloqueio de script externo em pagina local) -> baixado docs/vendor/vis-network.min.js (689KB) e referenciado localmente (offline).

impacto: Grafo agora renderiza: 226 nos, 1460 conexoes, force-directed, cores p
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]