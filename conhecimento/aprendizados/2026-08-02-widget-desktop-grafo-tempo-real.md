---
tipo: padrao
tags: [grafo, cerebro-vivo, widget, pywebview, tempo-real, javascript-bridge]
data: 2026-08-02
contexto: Usuario pediu um widget desktop para ver o grafo do conhecimento em tempo real, acompanhando o cerebro crescer enquanto o LER aprende.
decisao: Criado scripts/widget_grafo.py que abre docs/grafo.html numa janela pywebview e injeta um bloco JS de bridge. O JS chama window.pywebview.api.versao() a cada 2s; a versao e uma string composta pelos mtime_ns de knowledge_graph.json, do maior mtime sob conhecimento/ e do proprio grafo gerado. Se a versao muda, a pagina recarrega com cache-bypass (v=ts na URL).
impacto: Janela desktop em tempo real do cerebro vivo sem re-abrir o navegador. Padrao reutilizavel: pywebview.js_api resolve JS<->Python no mainloop, sem conflito de threads; versao por mtime e simples, barata e suficiente.
uso: pip install pywebview; python scripts/widget_grafo.py
uso (sem console): pythonw scripts\widget_grafo.py  (ou clicar widget-grafo.bat)
detalhe: o .bat usa pythonw.exe para suprimir a janela de terminal, deixando
apenas a janela do grafo frameless.
