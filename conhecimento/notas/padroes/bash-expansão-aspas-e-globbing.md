---
tags: [bash, falha, falhar, padrao, parte, pipe]
aliases: [Bash: expansão, aspas e globbing]
date: 2026-08-11
---

# Bash: expansão, aspas e globbing

**Fonte:** bash

Bash processa comandos em fases: parsing, expansão e execução. Toda a magia (e bugs) está na ordem de expansão. A ordem relevante: brace expansion (múltiplos `{a,b}`), tilde (`~`), parameter expansion (`$var`), command substitution (`$(...)`), arithmetic (`$((...))`), word splitting (divide resultado em palavras por IFS) e pathname expansion (globbing `*` `?` `[...]`).

Aspas mudam tudo:
- Aspas simples `'...'`: literal total — sem expansão de $var, sem escapes. Use para strings fixas e para valores com caracteres especiais.
- Aspas duplas `"..."`: expansão de variáveis/comandos/arithmetic, MAS sem word splitting nem globbing. NUNCA deixe variáveis sem aspas: `ls $files` quebra em palavras e sofre globbing; `ls "$files"` preserva o valor exato.
- Sem aspas: word splitting + globbing — os maiores geradores de bugs em scripts.

Globbing: `*` (qualquer sequência, excluindo dotfiles), `?` (um caractere), `[...]` (classes, `[a-z]`). Glob de arquivos que NÃO existem não se expande — vira o literal `*.txt` (anti-bug: cheque com `nullglob`/`failglob`). `set -f` desliga globbing; `shopt -s nullglob` elimina matches vazios; `dotglob` inclui dotfiles; `globstar` (`**`) recursivo.

Armadilhas clássicas:
- `if [ $x = "foo" ]` sem aspas quebra se `$x` for vazio ou tiver espaços — SEMPRE `[[ "$x" = "foo" ]]` (o `[[ ]]` de Bash, não POSIX, não sofre splitting e suporta `==`, `=~`, `&&`/`||`).
- `[` é um COMANDO (`test`), precisa de espaços ao redor; `[[` é palavra reservada da shell.
- Word splitting usa IFS (default espaço/tab/nova linha); mudar IFS sem restaurar corrompe tudo.
- `$(...)` remove trailing newlines; para preservar use `$(...; echo)` ou aspas.
- Brace expansion `{1..10}` não é globbing — acontece antes, não depende de arquivos.

Melhores práticas: `set -euo pipefail` no topo de todo script (erro aborta, variável indefinida aborta, pipe falha se qualquer parte falhar). Use `set -x` para debug. Aspas em TODAS as variáveis; `readarray`/`mapfile` para listas; para paths, prefira aspas duplas sempre. `for f in *.txt; do ...` com nullglob se o glob puder não achar nada.
## Conexoes

- [[bash-exit-codes-controle-de-fluxo-e-funções]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]