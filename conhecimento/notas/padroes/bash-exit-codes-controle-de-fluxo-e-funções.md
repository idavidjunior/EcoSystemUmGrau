---
tags: [awk, bash, padrao, reinventar, sed, xargs]
aliases: [Bash: exit codes, controle de fluxo e funções]
date: 2026-08-14
---

# Bash: exit codes, controle de fluxo e funções

**Fonte:** bash

Todo comando retorna um exit code: 0 = sucesso, não-zero = falha (1 genérico; 126 permissão; 127 comando não encontrado; 128+N sinal N, ex. 130 = SIGINT). `$?` guarda o último código; `$!` o PID do último job em background. O último comando do script define o exit code geral; use `exit N` explicitamente.

Controle de fluxo:
- `if cmd; then ...; elif ...; else ...; fi` — `if` testa o exit code do comando, não o valor. `[[ -e file ]]` (existe), `[[ -d dir ]]`, `[[ -f ]]`, `[[ -z "$var" ]]` (vazio), `[[ "$a" -eq "$b" ]]` (numérico) vs `[[ "$a" = "$b" ]]` (string); `=~` regex, `[[ "$s" =~ ^[0-9]+$ ]]`.
- Loops: `while cmd`, `until`, `for x in ...`, `for ((i=0; i<n; i++))`. `continue`/`break` com contagem: `break 2`.
- `case` é o switch do shell com globs: `case "$x" in start) ... ;; stop) ... ;; *) ... ;; esac`.
- Operadores: `;` sequência, `&&` roda se anterior sucesso, `||` se falha — `cmd1 && cmd2 || echo 'falhou'` (mas cuidado: `||` também roda se o próprio `cmd2` falhar; prefira `if` para lógica com mais de uma etapa).

Funções: `nome() { ...; }` (ou `function nome`). Escopo de variáveis é global por padrão — declare `local` dentro de função (`local x=1`). `$1..$9`, `${10}`, `$@` (todos), `$#` (contagem), `"$@"` expande cada argumento separado (use sempre com aspas, diferente de `$*` que junta). Retorno com `return N` (só números; para retornar texto, use `echo` + command substitution ou variável global). Params com defaults: `x="${1:-default}"`, obrigatório: `x="${1:?uso: precisa de arg}"`.

Armadilhas:
- Sem `set -e`, o script continua após erro silenciosamente — mas `set -e` também aborta em funções chamadas com `$?` no condicional; combine com `|| true` quando for intencional.
- `local` é apenas dentro de função; em script top-level use variáveis globais conscientemente.
- `trap 'cleanup' EXIT` garante cleanup; `trap ... ERR` para debug de linha de erro.
- Funções e aliases: aliases não funcionam em scripts não-interativos (expandem só em shells interativos) — use funções.

Melhores práticas: funções curtas por responsabilidade; documente os exit codes; `trap` para temp files; valide args no início com `[[ $# -ge 1 ]]`; mensagens de erro em `>&2`. Bash puro é ótimo até certo ponto — além disso, chame ferramentas (awk, sed, jq, xargs) em vez de reinventar.
## Conexoes

- [[bash-expansão-aspas-e-globbing]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]