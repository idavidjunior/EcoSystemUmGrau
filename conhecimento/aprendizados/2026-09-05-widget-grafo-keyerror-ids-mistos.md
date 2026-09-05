---
tipo: erro
tags: [widget, cerebro, grafo, keyerror, tipos, str-int, payload]
data: 2026-09-05
contexto: O widget "Cerebro Vivo" (scripts/widget_grafo.py + www/cerebro.html) exibia canvas em branco e seu log repetia "vigia: KeyError: 162". O grafo nunca recebia payload.
decisao: Corrigir a inconsistência de tipos de id entre nós e arestas em memories_to_widget e blindar layout_3d contra arestas órfãs.
impacto: Payload combined passou a ser enviado (1007 nós / 4869 arestas, zero arestas órfãs) e o grafo voltou a desenhar.
---

## Causa raiz

Na montagem do payload (memories_to_widget), os nós tinham seu id convertido para string (`str(n["id"])`), mas as arestas guardavam o id original da API (int). Em layout_3d, a indexação `idx[a]` (com idx de chaves str) falhava para aresta com id int (ex.: 162), gerando `KeyError` antes de o payload chegar ao canvas. Resultado: canvas em branco com fundo escuro e nenhum nó desenhado.

## Correção aplicada em scripts/widget_grafo.py

1. `id_to_idx = {str(n["id"]): i for i, n in enumerate(nos)}`
2. `src = str(link.get("source"))`, `tgt = str(link.get("target"))` e arestas gravadas com `str(valid_nodes[id_to_idx[src]]["id"])` (e id de destino idem)
3. Blindagem em `layout_3d`: `arestas = [(a, b) for a, b in arestas if a in idx and b in idx]` antes de montar os vetores de índices

## Validação

- Teste standalone reproduziu o KSKeyError antes da correção (vault OK, combined FAIL)
- Após a correção: `COMBINED OK: nos=1007 ar=4869`, arestas órfãs = 0
- Log do widget após restart: `payload enviado: 1007 nos, 4869 arestas`
- Captura direta da janela (PrintWindow): 3630 cores únicas de conteúdo (antes, só fundo ~72 cores), pixels gráficos desenhados

## Lições

- Sempre normalizar o tipo dos ids (str) em TODA a cadeia: nós E arestas, mesmo lugar de origem diversa (vault vs API de memória)
- Be2indar funções de layout contra ids ausentes (defensivo), nunca confiar em consistência externa
- Para inspecionar janela WebView2, usar PrintWindow (ignora janelas sobrepostas); CopyFromScreen pode capturar outra janela por cima

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]