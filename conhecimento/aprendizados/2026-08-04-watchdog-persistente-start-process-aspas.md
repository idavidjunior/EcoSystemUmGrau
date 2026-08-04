---
tipo: padrao
tags: [watchdog, persistencia, powershell, start-process, espacos]
data: 2026-08-04
contexto: Watchdog do ecossistema morria ao ser iniciado em background via Start-Process.
decisao: Start-Process -ArgumentList quebra o caminho com espacos (cada espaco vira argumento separado). Passar '-File \"caminho\"' como UM argumento unico com aspas embutidas resolve.
impacto: Watchdog roda estavel, monitora bridge 8765 + serve 8767 (health com auth), limpa orfaos do OpenCode. cmd /c start trava o shell; Start-Process direto nao.
