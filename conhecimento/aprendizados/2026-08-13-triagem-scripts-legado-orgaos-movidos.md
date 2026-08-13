---
tipo: padrao
tags: [organizacao, limpeza, scripts, orfaos, legado, manutencao, triagem]
data: 2026-08-13
contexto: Seguindo o objetivo de evoluir organizado, o ecossistema acumulou
~30 scripts/artefatos em scripts/ sem nenhuma referência externa real. A
triagem revelou também 12.812 arquivos no repo, a maioria artefatos de build
(Projetos/aegis/target, Projetos/StreamUmGrau/build) — não rastreados ou
rastreados por engano, que contaminavam qualquer varredura de referências.
decisao: Criar scripts/_legado/ como destino seguro e recuperável para órfãos.
Critérios de triagem usados: 1) varredura de referências cruzadas em todo o
repo (excluindo .git, node_modules, backups, target, build, incremental, deps,
bin, obj e logs de redirecionamento); 2) excluir auto-referências; 3) checar
atalhos do Startup do Windows e tarefas agendadas (found watchdog_start.bat,
opencode_desktop_guardian_start.bat, vigilante.ps1 como USADOS — não mover);
4) hash MD5 para pares duplicados (hotkey_pause x hotkey_pause_win32 65 linhas
em comum; preditor_uso x previsor_gargalos 30 linhas); 5) confirmar que o
equivalente ativo existe (rebuild_widget.py -> generate-graph-html.py).
Resultado: 30 arquivos movidos com git mv (renames preservados), README de
justificativa na pasta, suíte test-ecosystem 32 PASS / 0 FAIL, runtime boot
intacto. Padrão validado: ANTES de apagar/mover, sempre verificar atalhos de
Startup e Scheduled Tasks — referências externas ao repo invisíveis para
grep.
evidencia: scripts/_legado/README.md; test-ecosystem.ps1 32 PASS.
