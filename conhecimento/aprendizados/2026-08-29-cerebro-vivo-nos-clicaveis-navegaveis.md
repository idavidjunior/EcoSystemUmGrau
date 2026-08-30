---
tipo: decisao
tags: [cerebro-vivo, widget, navegacao, grafo, frontend]
data: 2026-08-29
contexto: O usuário pediu para tornar os nós do Cérebro Vivo clicáveis e navegáveis. O clique antes só abria o arquivo no VS Code e pausava a rotação.
decisao: Reformatado o comportamento de clique em www/cerebro.html: clicar num nó voa até ele e centraliza, destaca o nó e seus vizinhos diretos (esmaecendo o resto), abre um painel de detalhes dentro do widget (título, tipo/cluster, grau, resumo, tags, caminho e botão "Abrir no editor") e lista os vizinhos conectados para navegar de nó em nó. Clique em espaço vazio limpa a seleção. Em scripts/widget_grafo.py, o payload do vault foi enriquecido com _filePath/_summary/_tags/_kind via novo helper mapa_caminhos(), para as notas abrirem no editor via /open-file da bridge (8766).
impacto: Interação mais rica e navegável no grafo; abertura de arquivo movida do clique para o botão do painel. Sem mudança na estrutura de dados nem regressão no preflight (todos os testes passaram).
funcoes: selecionarNo, vizinhosDe, preencherPainelInfo, limparSelecao, abrirArquivo (cerebro.html); mapa_caminhos + campos extras (widget_grafo.py).

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[treinamento-especializado-em-navegacao-multi-plataforma-reco]]