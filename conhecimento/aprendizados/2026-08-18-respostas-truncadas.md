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
em "as pronúncias atu" em vez de "as pronúncias atuais".

## Causa provável

Corte na geração no limite de tokens/contexto da LLM. A resposta é entregue
truncada no meio da última palavra.

## Regra de mitigação (aplicar SEMPRE)

1. Antes de entregar qualquer resposta, conferir a última palavra.
2. Se a palavra estiver incompleta, ou a frase sem pontuação final, completar.
3. Se a mensagem foi cortada a meio de uma sentença, retomar a partir do
   ponto onde parou e concluir o pensamento.
4. Nunca entregar resposta terminando em palavra parcial sem correção.

## Validação

- Padrão confirmado pelo usuário com exemplo real.
- Regra registrada na memória episódica (memory #377).

## Lição

Cortes de geração no fim da resposta são o sintoma mais comum de estouro de
limite. A verificação final de completude é obrigatória antes de cada entrega.

## Conexoes

- [[2026-08-03-scan-proativo-orquestradorapk-flutter]]