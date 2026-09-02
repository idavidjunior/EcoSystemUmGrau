---
tags: [bloqueados, decisao, destruir, execução, opencode, são]
aliases: [gate veto compreensao]
date: 2026-09-02
---

# gate veto compreensao

**Fonte:** opencode

---
tipo: decisao
tags: [governanca, veto, checklist, compreensao-pedidos, kernel]
data: 2026-09-02
contexto: Implementar mecanismo de governança no EcoSystemUmGrau: fluxo de compreender pedido -> checklist/veto -> aprovação -> executar -> entregar. Fase 1 aprovada pelo usuário: implementar sem tocar no kernel; kernel fica para Fase 2.
decisao: Implementado bloco VETOS + _checklist_entrega + gerar_checklist no compreensao.py e tool MCP veto_pedido no server.py. Gate retorna status BLOQUEADO/APROVADO. Não houve alteração no kernel nesta fase.
impacto: Pedidos destrutivos, de commit direto, de exposição de segredos e de fechamento do desktop são bloqueados antes da execução. Fase 2 pode exigir aprovação real no kernel antes de route_task.
nota_tecnica: Bug de teste adversarial resolvido — regex DESTRUICAO original era restrito demais (ex.: 'apagar definitivamente') e não capturava 'apagar'. Reescrito para verbos destrutivos genéricos (apagar|deletar|remover|excluir|rm -rf|formatar|destruir).

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]