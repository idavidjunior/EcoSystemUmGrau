---
tipo: erro
tags: [cerebro-vivo, grafo, widget, generate-graph-html, tema-padrao, fisica, vis-network, javascript]
data: 2026-08-13
contexto: Auditoria do widget "Cérebro Vivo" (docs/grafo.html, gerado por scripts/generate-graph-html.py).
Linha de trabalho escolhida: corrigir o tema Padrão + sanar bugs. Fase 1 mapeou estados e fluxos;
Fase 2 validou todos os blocos JS com node --check (principal 740KB + widget-extra.js + resize.js).
decisao: 1) TEMAS.padrao.forca usava as chaves {grav, central} enquanto _aplicarForcasTema lê
{gravit, gravidade} — ao aplicar o tema Padrão, _fisBase recebia undefined e a física quebrava.
Corrigido padronizando o tema Padrão para gravit: -720, gravidade: 0.30 (os demais temas já usavam
esse formato). 2) aplicarTema lia t.statsBg, mas os temas definem statsFundo — a cor do painel de
stats nunca era aplicada. Corrigida a leitura para t.statsFundo. 3) limpar() não resetava
_tickPausado: com foco ativo (_expandirFoco seta true), "Limpar" congelava o grafo. Adicionado
_tickPausado = false. 4) Click handler só chamava _expandirFoco quando !_destacado: após o
primeiro foco, clicar em outro nó apenas dava flash, sem refocar. Removido o guard — clique sempre
refoca. 5) flashNo restaurava o nó para orig.color após 750ms, apagando o estilo do foco
(corViva/crescimento do microscópio). Agora, com _destacado ativo, o restore é ignorado.
6) Removidos estados órfãos: _labelsAnimated (lido de localStorage, nunca gravado nem usado),
_corDestaque e _headerCor (gravados em aplicarTema, nunca lidos).
impacto: Tema Padrão volta a aplicar física correta; stats ganha a cor definida por tema; Limpar não
congela mais o grafo; é possível saltar de foco em foco clicando em nós; o flash não apaga mais o
foco ativo. Grafo regenerado com 521 nós, 2224 arestas; sintaxe JS validada (node --check OK).
padrao_extraido: 1) Contratos de dados entre gerador e template JS devem ter as MESMAS chaves —
auditar pares "escreve X / lê Y" (aqui grav/central vs gravit/gravidade e statsFundo vs statsBg)
antes de assumir tema/quase qualquer configuração. 2) Reset (limpar/reiniciar) deve destravar TODOS
os flags de pausa criados por estados anteriores. 3) Restore temporário (flash) deve respeitar o
estado visual ativo — nunca restaurar "original" se outro efeito já dominou aquele nó.
erros_encontrados:
- [FIX] TEMAS.padrao.forca {grav, central} incompatível com _aplicarForcasTema {gravit, gravidade}
- [FIX] aplicarTema lia t.statsBg (inexistente) em vez de t.statsFundo (definido nos temas)
- [FIX] limpar() não resetava _tickPausado (grafo congelava após Limpar com foco ativo)
- [FIX] click com _destacado=true não refocava novo nó (só flash)
- [FIX] flashNo sobrescrevia o estilo do foco ao restaurar orig.color após 750ms
- [FIX] removidos órfãos: _labelsAnimated, _corDestaque, _headerCor

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[javascript-assincronismo-event-loop-promises-e-asyncawait]]
- [[javascript-closures-escopo-e-hoisting]]
- [[javascript-this-prototypes-e-herança]]
- [[javascript-tipos-coerção-e-igualdade]]