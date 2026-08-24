# Backfill de created_at no KG interno via memórias

## Contexto
Os 305 nós do grafo interno (`runtime/knowledge_graph/nodes.json`) tinham created_at fabricado: todos em 2026-08-17, hora da importação em massa que criou o KG — não a data real de cada descoberta. O arquivo nunca foi commitado (sem histórico git) e as notas do vault casavam por nome com só 6 nós.

## Decisão
Cruzamento nó → memória: interseção de tokens (palavras >3 chars, sem acento) entre name+properties do nó e task+summary da memória. Match forte (>= 60% do menor conjunto) adota o created_at real da memória de origem.

Resultado: 286 nós datados de verdade (distribuição realista de 28/07 a 17/08), 19 sem match ficaram honestamente na data de migração. Backup em `nodes.json.bak`, escrita atômica (tmp + os.replace).

## Aprendizados técnicos
- memories.json usa campo `created_at`, NÃO `timestamp` (472 entradas com timestamp vazio foram armadilha na primeira tentativa).
- Datas de importação em massa parecem válidas mas são todas idênticas — distribuição por mês/dia expõe o problema na hora.
- Proxy por similaridade lexical só vale com taxa alta de match (301/305 aqui); abaixo disso seria fabricar precisão.

## Impacto
Linha do tempo interna do ecossistema agora reflete quando o conhecimento nasceu, não quando foi migrado.
