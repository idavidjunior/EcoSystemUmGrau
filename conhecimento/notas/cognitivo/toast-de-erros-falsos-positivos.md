---
tags: [cognitivo, falado, falhou, general, reais, texto]
aliases: [Toast de Erros - Falsos Positivos]
date: 2026-08-20
---

# Toast de Erros - Falsos Positivos

**Dominio:** general

---
tipo: erro
tags: [widget, deteccao, falsos-positivos, regex]
data: 2026-08-20
---

# Toast de Erros - Falsos Positivos

## Problema
O toast de erros do widget Jarvis mostrava janela vermelha piscando sem erros reais.

## Causa
O regex pegava linhas do log do narrador que continham palavras como "erro" e "falhou" no texto falado. Exemplo:
"falando (140 chars): O dialogo de erro e do crash anterior..."

Essa linha e o Jarvis FALANDO sobre um erro passado, nao um erro real.

## Correcao
Filtrar
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]