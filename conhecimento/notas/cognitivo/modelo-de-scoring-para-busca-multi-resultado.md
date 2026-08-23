---
tags: [algorithm, baixo, cognitivo, errada, informacao, retornar]
aliases: [Modelo de scoring para busca multi-resultado]
date: 2026-08-23
---

# Modelo de scoring para busca multi-resultado

**Dominio:** algorithm

Quando uma busca retorna multiplos resultados, nao aceite o primeiro. Atribua scores: match exato + peso alto, match parcial + peso medio, overlap lexical + peso baixo. Defina thresholds por modo (estrito vs relaxado). Acompanhe o melhor score entre TODOS os resultados, nao apenas o primeiro. Retorne null se nenhum resultado atingir o threshold minimo — e melhor falhar que retornar informacao errada. O usuario pode entao tentar modo relaxado.
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]