---
tipo: decisao
tags: [auditoria, consolidacao, mapa-camadas, responsabilidade-unica]
data: 2026-09-17
contexto: Auditoria encontrou 9 ferramentas de auditoria e relatório no ecossistema (audit_eco, audit_runner, audit_triagem, audit_engine, architecture_integrity_monitor, adherence_audit, self_assessment_engine, runtime_auditor, preflight_check). O inventário marcava a função de 6 delas como PENDENTE (ambiguidade condenada pela cláusula anti-Frankestein). Foi preciso mapear quem chama o quê antes de qualquer consolidação cega.
decisao: Não fundir as 9 em uma superfície única (quebraria contratos consumidos por vigilante, jarvis_bridge, sync_rules, system_guardian, cognitive_core e runtime_boot). Em vez disso: (1) documentar a responsabilidade única de cada ferramenta no inventário, eliminando o status PENDENTE; (2) registrar o mapa de chamadores para provar quais estão vivas e quais são órfãs; (3) eliminar apenas a duplicação real comprovada.
impacto: Responsabilidades inequívocas por ferramenta, inventário sem ambiguidade, contratos de saída preservados, ganho de clareza arquitetural sem risco de regressão.
chamadores:
  audit_eco: audit_runner.py, jarvis_bridge.py
  audit_runner: system_guardian.py (lê runtime/audit_result.json)
  audit_triagem: vigilante.ps1 (--fix)
  audit_engine: cognitive_core.py, runtime_boot.py
  architecture_integrity_monitor: vigilante.ps1 (--json, timer 4h)
  adherence_audit: sync_rules.py
  self_assessment_engine: observability_reliability.py, jarvis_interface.py
  runtime_auditor: agent_bootstrap.py, eco_client.py, runtime_context.py
  preflight_check: gates de deploy e @sync
arquivo_gerado: conhecimento/aprendizados/2026-09-17-consolidacao-ferramentas-auditoria.md