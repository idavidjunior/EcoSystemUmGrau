---
tipo: padrao
tags: [interacao, estilo-usuario, comunicacao, financas]
data: 2026-08-24
contexto: David pediu explicitamente que o ecossistema aprenda com sua forma de fazer perguntas, exemplificando ao reformular a duvida de investimento como "a cada 100 reais qual e meu lucro 90 centavos por mes"
decisao: Registrar padrao de interacao na memoria (preferencia #509) e responder validacoes numericas confirmando/corrigindo o numero primeiro
impacto: Respostas do ecossistema passam a abrir com a confirmacao exata da cota perguntada antes de contexto adicional
---

# Padrao de pergunta: validacao numerica por cota

## Observado
David formula duvidas de confirmacao usando numeros arredondados sobre uma unidade base.
Exemplo real: "a cada 100 reais qual é o meu lucro 90 centavos em media por mes?"

## Como responder (contrato)
1. Confirmar ou corrigir o numero na primeira frase, sem preambulo
2. Trabalhar sempre por cota unitaria (por 100 reais), nao por percentual abstrato
3. Contexto so depois do numero confirmado

## Aplicacao imediata
Resposta dada nesta sessao: confirmado que 90 centavos/mes por 100 reais e a media conservadora correta (95 centavos no inicio com IR de 22,5%, subindo conforme tabela regressiva ate ~1 real com resgate apos 2 anos, sujeito a queda se Copom cortar juros).
