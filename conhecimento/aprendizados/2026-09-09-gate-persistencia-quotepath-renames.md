---
tipo: erro
tags: [git, persistencia, gate, ps1, rename, quotePath]
data: 2026-09-09
contexto: Gate de persistência (scripts/persistencia.ps1) travava commits com "Test-Path : Caracteres inválidos no caminho" na linha 311, bloqueando Ciclo 6 e Ciclo 7.
decisao: Causa: git status --porcelain escapa caminhos não-ASCII com aspas + octais (`"...\303\255..."`) por padrão (core.quotePath=true), e renames saem como `R old -> new` gerando caminho inválido no parsing Substring(3). Correção mínima segura: `git -c core.quotePath=false status --porcelain --no-renames` nas linhas 91 e 292 do gate.
impacto: Gate destravado; commits do Ciclo 6/7 voltaram a fluir. Nenhum caminho de dado afetado.
evidencia: Diagnóstico iterou Test-Path linha a linha; `--no-renames` faz rename virar duas linhas simples (D + A) com caminhos válidos.