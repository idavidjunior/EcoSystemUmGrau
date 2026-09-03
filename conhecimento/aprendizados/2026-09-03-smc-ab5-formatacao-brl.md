---
tipo: decisao
tags: [smc, calculadora, formatacao, brl, android-pure-sdk]
data: 2026-09-03
contexto: 5a aba "Simples" do SupermarketCalculator mostrava número cru (1000, 10.5) no visor.
decisao: Manter scCurrent como string crua com ponto decimal e sem milhar; formatar apenas o texto exibido via formatDisplay() (milhar com . e fracao fixa com 2 casas e virgula: 1.000, 10,50). formatNumber() passa a retornar string crua; todo display/expression passa por formatDisplay(). parse() blindado com try/catch retornando NaN para nao crashar apos divisao por zero encadeada.
impacto: Visor em formato brasileiro sem quebrar calculo; robustez contra NumberFormatException.

## Conexoes

- [[encoding-utf-8-in-javac-required-on-windows-to-prevent-corru]]
- [[form-starts-empty-input-forms-never-auto-load-from-file-user]]
- [[merge-by-name-if-name-matches-existing-item-increment-quanti]]
- [[salvar-new-file-explicit-save-creates-timestamped-snapshot-n]]
- [[stringbuilder-for-price-fine-grained-control-over-display-fo]]
- [[why-d8-doesnt-accept-directory-trees-of-class-files-it-needs]]
- [[why-user-expects-a-blank-slate-when-entering-a-form-tab-cons]]