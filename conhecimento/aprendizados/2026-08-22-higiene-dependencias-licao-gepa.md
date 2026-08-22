---
tipo: erro
tags: [dependencias, higiene, dspy, gepa, grafo]
data: 2026-08-22
contexto: Inventario das 167 bibliotecas pip do ambiente do ecossistema.
decisao: Remocao de libs mortas so apos triagem em 4 camadas (AST, transitivas, refs CLI, refs ativos) e validacao de imports POS-remocao.
impacto: gepa removida quebrou o import do dspy; detectado na validacao e revertido com pip install. Ambiente final integro.
---

# Higiene de dependencias — licao do gepa

Ao limpar dependencias orfas, o parser de Requires-Dist nao capturou a
dependencia real entre dspy e gepa (import interno condicional). A remocao
de gepa quebrou import dspy. Detectado porque a validacao rodou DEPOIS da
desinstalacao.

## Regra extraida

Desinstalacao so e concluida apos: 1) lista candidata por analise estatica,
2) exclusao de transitivas com normalizacao underscore/hifen, 3) busca de uso
via CLI e imports dinamicos, 4) teste de imports criticos pos-uninstall.

## Resultado

19 notas frameworks criadas (libs usadas sem documentacao), 40 bibliotecas
conectadas ao grafo (antes 26), 6 pacotes mortos removidos, setup-auto.ps1
corrigido (dspy no lugar do alias antigo dspy-ai).
