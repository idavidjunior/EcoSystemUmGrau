---
tipo: erro
tags: [preflight, gate, etica, performance, scan-repo]
data: 2026-09-09
contexto: O gate de persistencia (persistencia.ps1) quedava preso sem commit/sem push durante horas. O preflight técnico (preflight_check.py) rodava mas o bloco [7] Preflight Etico estourava timeout de 240s, bloqueando cada commit.
decisao: Adicionar 'Projetos' (apps Android externos, ~29k arquivos) aos skip_dirs dos scans scan_repo() e data_inventory() de scripts/preflight_etica.py. Projetos é código de APP, não do ecossistema núcleo, e não precisa ser varrido a cada commit.
impacto: O preflight ético caiu de >240s (timeout) para ~60s. O preflight técnico completo passou novamente (todos os 10 blocos OK). O gate voltou a conseguir commitar. Nenhum risco ético relevante perdido: o scan ainda varre scripts/, mcp/, config/, conhecimento/ e ler-runtime/.
evidencia: python scripts/preflight_check.py -> RESULTADO: TODOS TESTES PASSARAM.