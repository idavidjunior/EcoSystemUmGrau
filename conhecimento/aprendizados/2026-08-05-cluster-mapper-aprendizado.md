# ClusterMapper — Mapeamento Aprendido de Notas/Nós (2026-08-05)

## Contexto
O mapeamento cluster nota->nó era um dict estático (`CLUSTERS`) + match exato.
O `slugify` colapsa underscores (`ler_auditoria` -> `lerauditoria`) e o RAKE
concatena tags duplicadas (`android-pure-sdkandroid-pure-sdk`), então **44%**
das 365 notas caíam em "geral".

## Decisão
Criar `scripts/cluster_mapper.py` — algoritmo que APRENDE e OUSA:

1. **Normalização**: remove pontuação/espaços (`norm`) + dedup de strings
   repetidas (`dedupe`: 'xx' -> 'x', 'androidpuresdkandroidpuresdk' -> simples).
2. **Cascata de resolução** em `resolver(tags, fonte, categoria, slug)`:
   1. match exato normalizado no índice;
   2. substring de fonte conhecida dentro do token;
   3. associação APRENDIDA (co-ocorrência ponderada de tokens por cluster);
   4. análise do SLUG/título quando tags/fonte não bastam (ousadia extra);
   5. pista por categoria (cognitivo/heuristicas -> 'cognicao');
   6. 'geral' só como último recurso.
3. **Treino ignora 'geral'**: notas sem cluster não poluem o aprendizado.
4. **Sugestão de clusters novos**: detecta fontes coesas sem cluster
   (`_sugerir_novos_clusters`) e reporta, sem alterar a base.
5. **Persistência**: aprendizado exportado para
   `conhecimento/aprendizados/cluster_mapper.json` (memória de mapeamento).

## Resultado
Distribuição de 339 nós no widget:
- ANTES: geral 85 (23%) | ecossistema 115 (31%)
- DEPOIS: geral 12 (3.5%) | ecossistema 120 (35%) | cognicao 64 (19%)
  | navegacao 46 (13.6%) | mp3player 43 (12.7%) | android 34 (10%) | ler 20 (6%)

Padrões aprendidos: `opencode`->ecossistema (85), `debugging`->cognicao (12),
`treinamentonavegacao`->navegacao (35), `lerauditoria`->ler.

## Impacto
- `generate-graph-html.py`: treina o mapper no início de `extrair_nos()` e usa
  `_resolver_cluster(tags, fonte, mapper, categoria, slug)`.
- `generate-obsidian-notes.py`: usa `cluster_da_nota(tags, categoria, slug,
  mapper)` para hubs de cluster consistentes com o grafo.
- Widget rebuilt (`docs/grafo_widget.html`) + reiniciado.

## Lições
- Aprender sob o rótulo 'geral' cria ruído; só aprenda com clusters conhecidos.
- `treinar(reset=True)` por padrão para não inflar contadores entre execuções.
- O slug/título é fonte rica quando tags estão vazias (2 casos resolvidos).
