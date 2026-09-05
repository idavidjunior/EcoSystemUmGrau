---
tags: [decisao, mainactivity, opencode, sclastwasequals, scsolvedexpr, scstartnewnumber]
aliases: [Calculadora — Formato Consolidado do Percentual Restaurado]
date: 2026-09-03
---

# Calculadora — Formato Consolidado do Percentual Restaurado

**Fonte:** opencode

Tarefa: restaurar o formato consolidado do percentual da calculadora simples (tab Simples da MainActivity.java).

O comportamento consolidado (baseline no commit 485dd9f) e:
- Expressao: `formatDisplay(a) + " " + scLastOp + " " + formatDisplay(p) + "% ="` — preserva a digitacao (0,6 fica 0,6).
- Resultado (`scResult`): `formatDisplay(bdToString(r))` — ex. 1.006.000.
- Display grande (`scDisplay`): `formatDisplay(bdToString(r.subtract(a).abs()))` — o acrescimo, ex. 6.000.

Validado no dispositivo (adb input tap + uiautomator dump): digitado `1.000.000 + 0,6%`, visor mostra `1.000.000 + 0,6% =`, `1.006.000` em scResult e `6.000` em scDisplay.

## Aprendizados
- O handler percent usa o modelo de tokens (scTokens/scCurNum/scStartNewNumber/scLastWasEquals/scSolvedExpr). A reescrita que havia quebrado o formato consolidado usava modelo antigo; o fix restaurou o modelo de tokens com os campos declarados fora do if.
- `formatDisplay` preserva a fracao como digitada (0,6 nao vira 0,60).
- Bug d
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]