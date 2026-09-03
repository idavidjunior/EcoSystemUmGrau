---
tipo: decisao
tags: [smc, calculadora, percentual, acrescimo, resultado, display, android-pure-sdk]
data: 2026-09-03
contexto: Correcao do percentual em BigDecimal validada; usuario pediu exibir resultado e acrescimo em destaque na 5a aba "Simples".
decisao: Ao clicar em '%' com operacao pendente, resolve imediato montando: scExpression mostra a conta (a + p% =), novo campo scResult mostra o resultado (a+p% ou equivalente), e scDisplay (40sp bold) mostra o acrescimo = |resultado - operando inicial a| em fonte grande. No '=' normal (sem %), resultado vai so para scResult e scDisplay fica vazio (sem duplicar). formatDisplay() nao forca mais 2 casas decimais: mantem 0,6 como 0,6 e 0,60 como 0,60; so preenche "00" se a fracao estiver vazia (15. -> 15,00), respeitando a digitacao do usuario.
impacto: Conta no campo pequeno, resultado no campo medio, acrescimo em fonte grande abaixo; sem duplicacao do resultado; formato decimal fiel ao digitado.

## Conexoes

- [[encoding-utf-8-in-javac-required-on-windows-to-prevent-corru]]
- [[form-starts-empty-input-forms-never-auto-load-from-file-user]]
- [[merge-by-name-if-name-matches-existing-item-increment-quanti]]
- [[salvar-new-file-explicit-save-creates-timestamped-snapshot-n]]
- [[stringbuilder-for-price-fine-grained-control-over-display-fo]]
- [[why-d8-doesnt-accept-directory-trees-of-class-files-it-needs]]
- [[why-user-expects-a-blank-slate-when-entering-a-form-tab-cons]]