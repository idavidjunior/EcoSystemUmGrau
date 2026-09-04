---
tipo: decisao
tags: [calculadora, android, percentual, formato-consolidado]
data: 2026-09-03
contexto: Restaurar o formato consolidado do percentual na tab Simples da MainActivity.java do SupermarketCalculator.
decisao: O handler 'percent' foi reescrito para restaurar o comportamento consolidado: 'A + B%' mostra a expressão digitada, o resultado em 'scResult' e o acrescimo em 'scDisplay' (fonte grande).
impacto: Validado no dispositivo: '1.000.000 + 0,6% =' mostra '1.006.000' em scResult e '6.000' em scDisplay. Menos regressao e experiencia consistente com a versao 1.5.8.
---

# Calculadora — Formato Consolidado do Percentual Restaurado

Tarefa: restaurar o formato consolidado do percentual da calculadora simples (tab Simples da MainActivity.java).

O comportamento consolidado (baseline no commit 485dd9f) e:
- Expressao: `formatDisplay(a) + " " + scLastOp + " " + formatDisplay(p) + "% ="` — preserva a digitacao (0,6 fica 0,6).
- Resultado (`scResult`): `formatDisplay(bdToString(r))` — ex. 1.006.000.
- Display grande (`scDisplay`): `formatDisplay(bdToString(r.subtract(a).abs()))` — o acrescimo, ex. 6.000.

Validado no dispositivo (adb input tap + uiautomator dump): digitado `1.000.000 + 0,6%`, visor mostra `1.000.000 + 0,6% =`, `1.006.000` em scResult e `6.000` em scDisplay.

## Aprendizados
- O handler percent usa o modelo de tokens (scTokens/scCurNum/scStartNewNumber/scLastWasEquals/scSolvedExpr). A reescrita que havia quebrado o formato consolidado usava modelo antigo; o fix restaurou o modelo de tokens com os campos declarados fora do if.
- `formatDisplay` preserva a fracao como digitada (0,6 nao vira 0,60).
- Bug de digitacao em teste ADB: o toque de coordenada errada (`[672,1878]` e o botao 3, nao o 6) entrou digito incorreto; o botao 6 da tab Simples esta em `[672,1538]` (linha 4/5/6).
- Layout da tab Simples (centros): C [144,858], % [672,858], 6 [672,1538], 1 [144,1878], + [936,1878], 0 [145,2179], , [411,2179].
