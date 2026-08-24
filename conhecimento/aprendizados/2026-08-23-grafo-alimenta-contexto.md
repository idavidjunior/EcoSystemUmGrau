# Grafo vivo alimenta o contexto das sessões

## Contexto
O Cerebro Vivo e o vault Obsidian eram apenas visualização/arquivo: o runtime_context montava contexto com BM25 (memória + corpus + notas) mas ignorava as sinapses — os links [[...]] entre notas, que codificam vizinhança semântica real.

## Decisão
Integração mínima em `scripts/runtime_context.py`:
- Nova função `_carregar_sinapses(conhecimento)`: para cada resultado BM25 de fonte "nota", localiza o arquivo (varre conhecimento/notas E aprendizados), extrai até 4 links [[...]] do corpo e devolve como campo estruturado `sinapses` no contexto.
- Hubs (`*-hub-*`) e Home filtrados — são navegação, não conhecimento.
- Seção "Sinapses do grafo (vizinhança das notas)" no render textual; incluída no resumo final.
- Sem índice novo, sem tocar search_knowledge.py: reusa corpus/BM25 existentes.

## Impacto
- Tarefa nova agora chega à LLM com decisões relacionadas e antipadrões conectados às notas recuperadas, não só documentos soltos.
- Fecha o ciclo declarado na missão: conhecimento acumulado → decisão melhor por sessão.

## Aprendizados técnicos
- Muitos aprendizados em conhecimento/aprendizados têm 0 links (gerador reportou "0 receberam conexões") — expansão por sinapse neles é nula; candidatos a enriquecimento futuro do gerador.
- BM25 retorna resultados mesmo para consultas sem sentido real (score mínimo 0.1 baixo) — sinapses podem aparecer para lixo; aceitável, score expõe a qualidade.

## Testes
- py_compile OK; consulta "controle tv lg webos" → 2 sinapses com vizinhos reais (aprendizado TV LG, secrets guard, widget grafo); --json válido (3 sinapses); consulta sem match → 0 sinapses sem erro.
