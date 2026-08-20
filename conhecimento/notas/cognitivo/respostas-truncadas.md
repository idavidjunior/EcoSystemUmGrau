---
tags: [cognitivo, cortada, entregar, general, llm, mitigacao]
aliases: [respostas truncadas]
date: 2026-08-20
---

# respostas truncadas

**Dominio:** general

---
tipo: erro
tags: [resposta, truncamento, final, palavra, llm, mitigacao]
data: 2026-08-18
contexto: Respostas do assistente terminam com a última palavra cortada (ex.: "atuais" vira "atu")
decisao: Adicionar regra de mitigação: verificar final de toda resposta antes de entregar
impacto: Respostas completas, sem palavras cortadas
---

## Contexto

O usuário identificou um padrão recorrente: as respostas do assistente
terminam com a última palavra incompleta. Exemplo concreto: a frase terminou
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]