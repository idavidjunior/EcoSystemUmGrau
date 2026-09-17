---
tipo: padrao
tags: [inventario, auto-conhecimento, dependencias, watchdog, auditoria]
data: 2026-09-17
contexto: Auditoria do ecossistema revelou que o inventário só sabia o que existe, não o que sumiu, e que não havia mapa vivo de acoplamento entre os 217 scripts/arquivos ativos.
decisao: Adicionar espelho reverso ao inventory_manager (comando orphans, detecta estruturas do inventário que sumiram do disco, exit 1 se houver) e gerador de mapa de dependências no audit_triagem (--deps, escopo restrito a scripts/config/mcp, 217 nos / 782 arestas). Integrar ambos ao ciclo diário do vigilante.ps1 (triagem).
impacto: Ecossistema agora detecta automaticamente estruturas perdidas e visualiza a malha viva de acoplamento (hubs: .env 56, memory_engine 37, preflight_check 34, jarvis_bridge 21, sync_rules 19, persistencia.ps1 18).
licoes:
  - os.walk(BASE) varreria o repo inteiro e explodia o timeout; escopo restrito a scripts/config/mcp resolve.
  - Vigilante diário agora roda: audit_triagem --fix, inventory orphans, audit_triagem --deps.
  - Espelho reverso leva 293ms — custo desprezível para o ciclo do watchdog.
  - O _legado é quarentena legítima: nenhum arquivo é referenciado por import/path ativo (refs eram falsos positivos: funções start_widget/check_services, log paths, duplicatas com versão ativa).