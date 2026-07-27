# /doctor — Auto-Diagnóstico do Ambiente
Aciona o agente doctor para diagnosticar e corrigir vulnerabilidades do ambiente Claude Code.

## Uso
`/doctor`

## O que acontece
1. Verifica cache e lock (não executa se já rodou há menos de 6h)
2. Detecta SO, shell, versão do Claude Code
3. Diagnostica WebSearch, WebFetch, memory-keeper, dev-env-copilot
4. Identifica brechas de configuração
5. Oferece corrigir automaticamente

## Comandos
| Comando | Ação |
|---------|------|
| `/doctor` | Diagnóstico manual completo |
| `/doctor schedule 7d` | Agendar verificação a cada 7 dias |
| `/doctor schedule 30d` | Agendar verificação a cada 30 dias |
| `/doctor off` | Desativar modos automáticos |
| `/doctor on` | Reativar modos automáticos |
| `/doctor status` | Ver última verificação e agenda |

## Exemplo
`/doctor`
`/doctor schedule 7d`
