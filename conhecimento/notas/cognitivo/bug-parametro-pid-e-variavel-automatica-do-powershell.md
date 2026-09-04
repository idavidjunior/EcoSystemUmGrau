---
tags: [apertar, botão, cognitivo, general, recalculava, repetidamente]
aliases: [Bug: parametro Pid e variavel automatica do PowerShell]
date: 2026-08-06
---

# Bug: parametro Pid e variavel automatica do PowerShell

**Dominio:** general

---
tipo: erro
tags: [watchdog, powershell, bug, resiliencia]
data: 2026-08-06
contexto: Certificacao forense de processos no watchdog.ps1 (Test-ForensicoLixo / Invoke-KillCertificado)
decisao: Renomear parametro [int]Pid para [int]ProcessId nas funcoes forenses
impacto: Evita que o watchdog mate o proprio processo (variavel automatica PID read-only)
---

# Bug: parametro Pid e variavel automatica do PowerShell

## Sintoma
A funcao `Test-ForensicoLixo` e `Invoke-KillCertificado` declaravam `[int

---
tipo: erro
tags: [calculadora, supermarket, precedencia, bug, idempotencia-igual, android, puresdk]
data: 2026-09-03
contexto: Reescrevi a tab Calculadora Simples (setupSimpleCalc da MainActivity.java do SupermarketCalculator, pure SDK) para aceitar expressão completa com precedência matemática e corrigir o bug do botão = que recalculava ao apertar repetidamente.
decisao: Avalei a expressão tokenizada com precedência ×÷ antes de +− (esquerda-direita) via BigDecimal. O handler op, no caso pós
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]