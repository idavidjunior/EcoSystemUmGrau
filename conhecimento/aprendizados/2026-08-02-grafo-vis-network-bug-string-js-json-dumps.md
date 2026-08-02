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
decisao: Diagnosticado via headless Chrome + Node. Causa raiz: um no (label "Why - User expects a blank slate...") continha quebra de linha literal dentro de string JS delimitada por aspas simples -> sintaxe invalida em TODO o script -> vis-network nem inicializava. Tambem usavamos template literal (`title:`...`) que quebra com crase ou ${ }. Corrigido montando nodes/edges via json.dumps(ensure_ascii=False) que escapa qualquer caractere corretamente. Segundo problema: lib via CDN unpkg nao carrega em file:// (bloqueio de script externo em pagina local) -> baixado docs/vendor/vis-network.min.js (689KB) e referenciado localmente (offline).
impacto: Grafo agora renderiza: 226 nos, 1460 conexoes, force-directed, cores por categoria, hover com texto. Validacao headless: canvas 764px + classe vis-network presente no DOM dump. Teste em Node valida sintaxe dos arrays (nodes/edges) antes de abrir.
detalhe: Licao de debugging: "a pagina abre mas o canvas vazio" != "HTML quebrado" — o JS dos dados estava quebrado. Fluxo de validacao que funciona: (1) node valida sintaxe do vendor lib, (2) node valida arrays extraidos do HTML com mock do vis.DataSet, (3) chrome --headless --dump-dom procura <canvas> + classe vis-network.
