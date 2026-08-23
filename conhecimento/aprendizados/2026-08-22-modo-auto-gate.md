---
tipo: decisao
tags: [persistencia, gate, modo-auto, limpeza, preflight, debounce]
data: 2026-08-22
contexto: Usuario aprovou ativar o modo AUTO do gate persistencia.ps1 com as politicas discutidas de commit automatico em camadas e limpeza pos-push.
decisao: |
  Politicas implementadas DENTRO do Invoke-RepoCommit, valendo somente quando config.modo = auto.
  Modo MANUAL permaneceu byte a byte igual (validado por teste).

  1. Classificacao das pendencias (Get-TipoPendencia): vivo = conhecimento/memoria, runtime,
     tfidf, CONHECIMENTO.md etc; codigo = extensoes py/ps1/js/html/css/kt/java/json/xml.
  2. Preflight minimo (Test-PreFlightCodigo): py_compile nos .py e node --check nos .js tocados.
     Falha = NADA comita; snapshot via git stash create + store (com git add -A temporario para
     incluir untracked, depois git reset para restaurar o indice). Working tree preservado.
  3. Debounce (config.debounce_minutos=30): retira so lote puro de estado vivo; qualquer pendencia
     de codigo passa na hora. Timestamp em config.ultimo_auto_commit gravado apos todo commit auto.
  4. Add-GitignoreLixo antes do add: garante __pycache__/ e *.pyc no .gitignore, lixo nunca entra no espelho.
  5. Invoke-Limpeza pos push OK ($LASTEXITCODE=0): lista branca fixa (pycache, pyc, *.log 7d,
     %TEMP%/opencode 3d, locks) pulando arquivos TRACKED via git ls-files com relpath de barra normal.
  6. PUSH_FALHOU: retorna sem limpar nada. CLEAN path tambem faz push+limpeza (Invoke-PushELimpeza).

impacto: |
  RPO do estado vivo cai para ~30 min sem intervencao; codigo quebrado nunca suja a main;
  lixo regeneravel sai do disco apos cada push validado; espelho GitHub fica limpo.

limitacoes:
  - bash tool deste ambiente trava em git push real com transferencia; usar terminal_run-command.
  - limpeza avalia idade da PASTA __pycache__: arquivo novo dentro de pasta velha impede a remocao.
  - build/CerebroVivo trackeado no eco continua intocado ate decisao estrutural do usuario.
