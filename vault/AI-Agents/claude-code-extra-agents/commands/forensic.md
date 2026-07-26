# /forensic — Debug Forense
Aciona o agente debug-forensic para investigar erros em produção.

## Uso
`/forensic`

## O que acontece
1. O agente coleta evidências (stack trace, ambiente, mudanças recentes)
2. Triangula causa raiz cruzando código, logs e histórico
3. Apresenta hotfix, correção definitiva e prevenção futura
4. Gera mini-postmortem

## Quando usar
- Erro 500 em produção
- Crash sem causa óbvia
- Comportamento intermitente
- Regressão após deploy

## Exemplo
`/forensic`
"Erro 500 em produção. Stack trace: NullPointerException em OrderService.java:142"
