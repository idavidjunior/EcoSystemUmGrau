---
tipo: padrao
tags: [organizacao, git, gitignore, artefatos, build, limpeza, manutencao]
data: 2026-08-13
contexto: Fase 2 da organização do EcoSystemUmGrau. O repositório eco tinha 1553
arquivos rastreados e o .git já ignorava corretamente target/build/backups/logs
(*.log). Porém havia lixo rastreado sem uso real: HTMLs de teste do widget
(test_grafo.html 526KB, teste_*.html, test_graph_controls.html), screenshots
(shot_*.png, screen_full.png), backup do config (opencode.jsonc.bak), logs .err
e .txt efêmeros, e 9 arquivos de lixo que haviam entrado em scripts/_legado na
fase 1 (logs/estado de runtime que não deveriam ser versionados).
decisao: (1) git rm (disco + git) para lixo sem uso real: 16 arquivos
(test_grafo.html, teste_*.html, widget_log.txt, widget_drag_result.json,
widget_e2e_result.json, grafo_widget_geometria.json, opencode_serve.log.err,
debug_output.txt, network_block.txt, test_github_integration.txt,
widget_test_output.txt, grafico_widget_debug.bat). (2) git rm --cached (mantém
no disco, sai do git) para screenshots e config backup: 6 arquivos. (3) git rm
dos 9 arquivos efêmeros que estavam em _legado. (4) .gitignore ampliado: *.bak,
docs/test_*.html, docs/teste_*.html, docs/widget_log.txt, docs/widget_drag_result.json,
docs/widget_e2e_result.json, docs/grafo_widget_geometria.json, docs/*.log.err,
docs/screen_full.png, docs/shot_*.png, debug_output.txt, network_block.txt,
test_github_integration.txt, widget_test_output.txt, grafico_widget_debug.bat.
(5) README de _legado atualizado explicando que logs efêmeros não ficam lá.
(6) Descoberto: os projetos irmãos aegis e StreamUmGrau JÁ ignoram target/build
nos próprios .gitignore (66 e 70 arquivos rastreados, repos limpos); os 6.4GB
de build são só disco, regeneráveis via cargo build / flutter build.
Resultado: git limpo (renames + remoções corretas), test-ecosystem 32/32 PASS,
boot intacto. Padrão: revisar periodicamente git ls-files em busca de artefatos
rastreados; projeto irmão deve ter .gitignore próprio para target/build.
evidencia: git status (31 remoções), test-ecosystem.ps1 32 PASS, runtime_boot --status OK.
