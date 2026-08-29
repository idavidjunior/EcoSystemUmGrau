---
tags: [cognitivo, general, inteiros, não, percentuais, tratava]
aliases: [ordinais text normalizer]
date: 2026-08-29
---

# ordinais text normalizer

**Dominio:** general

---
tipo: erro
tags: [tts, ordinal, text_normalizer, pronuncia, placeholder]
data: 2026-08-29
contexto: text_normalizer.py expandia 1º/2ª como "umº" (sufixo ordinal mantido), pois _normalize_numbers só tratava inteiros/percentuais. Correção necessária para expandir ordinais por extenso.
decisao: Adicionar ordinal_por_extenso(n, genero) (1..999, masc/fem) e regex (?<![\d.,])(\d{1,3})([ºª]) com placeholder "=ORDO<chave_letras>M/F=" (chave só-de-letras via _letras_de para a regex de inteiros não ca
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]