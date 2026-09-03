---
tipo: decisao
tags: [smc, calculadora, formatacao, brl, android-pure-sdk]
data: 2026-09-03
contexto: 5a aba "Simples" do SupermarketCalculator mostrava número cru (1000, 10.5) no visor.
decisao: Manter scCurrent como string crua com ponto decimal e sem milhar; formatar apenas o texto exibido via formatDisplay() (milhar com . e fracao fixa com 2 casas e virgula: 1.000, 10,50). formatNumber() passa a retornar string crua; todo display/expression passa por formatDisplay(). parse() blindado com try/catch retornando NaN para nao crashar apos divisao por zero encadeada.
impacto: Visor em formato brasileiro sem quebrar calculo; robustez contra NumberFormatException.
