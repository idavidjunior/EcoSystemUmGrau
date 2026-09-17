---
tipo: padrao
tags: [gate, persistencia, clausula-petrea, pre-commit-hook]
data: 2026-09-17
contexto: Mudancas feitas diretamente com git commit fora do gate persistencia.ps1 geravam 78 commits [LEA] e metricas de aderencia baixas.
decisao: Instalar git hook pre-commit forcando que todo commit passe pelo gate. O persistencia.ps1 cria .git/.gate_commit_active antes do git commit e remove depois. Commits sem marker sao bloqueados com orientacao de usar o gate. Detector passivo adicionado ao preflight_check.py (check 12).
impacto: Adesao forcada ao ponto unico de persistencia, metrica gate_persistencia converge para 100%, LER executor.py corrigido para usar persistencia.ps1 run-sync.
