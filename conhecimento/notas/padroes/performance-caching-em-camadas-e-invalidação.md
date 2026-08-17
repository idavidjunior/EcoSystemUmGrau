---
tags: [forever, lentidão, negrito, padrao, performance, stale]
aliases: [Performance: caching em camadas e invalidação]
date: 2026-08-17
---

# Performance: caching em camadas e invalidação

**Fonte:** performance

Cache é a técnica de maior retorno/linha de código — e a maior fonte de bugs de consistência. O custo não é a leitura, é a invalidação (\"There are only two hard things in CS: cache invalidation and naming things\").

**Camadas (do mais rápido ao mais lento):** 1) in-process/in-memory (CPU cache, heap, Redis local — microssegundos); 2) CDN/edge (millissegundos, para assets e conteúdo público); 3) cache de aplicação distribuído (Redis/Memcached — sub-millisecond a millissegundos); 4) cache de banco (buffer pool, query cache, materialized views); 5) disco (filesystem, page cache do SO). Meta: quanto mais próximo do usuário e menor o custo de acesso, melhor; o mapeamento certo depende do custo de recomputar vs de guardar.

**Padrões de uso:** cache-aside (app consulta cache, miss → busca na fonte, popula cache, com TTL): simples e correto, preferido em 90% dos casos; read-through/write-through (a camada de cache é a interface de dados): consistência melhor, complexidade maior; write-behind (escreve no cache e assíncrono no banco): alto throughput, risco de perda. TTL com jitter (variar ±10%) evita stampede/thundering herd — todas as instâncias expirando juntas e batendo na fonte.

**Invalidação — o núcleo duro:** estratégias: 1) TTL: expiração absoluta (melhor para dados com validade de negócio); 2) invalidação explícita: invalidar por chave quando a escrita ocorre (mais preciso, mais eventos a cuidar); 3) versionamento (cache key com `?v=hash` para assets — padrão CDN); 4) log de invalidação (CDC do banco → fila → invalida cache). Regras práticas: cache key inclua os parâmetros da query (e o locale), nunca mais dados que o usuário vê do que deveria (não cacheie dados por-usuário em camada compartilhada); invalidação deve ser idempotente; sempre tenha caminho de fallback sem cache que funcione (cache down ≠ sistema down — use `fail-open` para leitura, `fail-closed` só onde consistência exige).

**Medição e armadilhas:** meça hit ratio, mas saiba que hit ratio alto com dado obsoleto é pior que miss. Armadilhas: cache de query com parâmetro variável alto (cardinalidade explode o cache), cache quente escondendo bug de produção (cold start expõe lentidão), negrito de cachear \"tudo\" sem TTL (stale forever). Regra de ouro: cacheie o que é caro de computar e pouco mutável; invalidar corretamente é mais importante que cachear mais.
## Conexoes

- [[cluster-hub-programacao]]
- [[espera-adaptativa-por-tipo-de-recurso]]
- [[padrao-hub-padroes]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]