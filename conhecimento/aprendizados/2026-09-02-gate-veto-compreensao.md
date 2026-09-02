---
tipo: decisao
tags: [governanca, veto, checklist, compreensao-pedidos, kernel]
data: 2026-09-02
contexto: Implementar mecanismo de governança no EcoSystemUmGrau: fluxo de compreender pedido -> checklist/veto -> aprovação -> executar -> entregar. Fase 1 aprovada pelo usuário: implementar sem tocar no kernel; kernel fica para Fase 2.
decisao: Implementado bloco VETOS + _checklist_entrega + gerar_checklist no compreensao.py e tool MCP veto_pedido no server.py. Gate retorna status BLOQUEADO/APROVADO. Não houve alteração no kernel nesta fase.
impacto: Pedidos destrutivos, de commit direto, de exposição de segredos e de fechamento do desktop são bloqueados antes da execução. Fase 2 pode exigir aprovação real no kernel antes de route_task.
nota_tecnica: Bug de teste adversarial resolvido — regex DESTRUICAO original era restrito demais (ex.: 'apagar definitivamente') e não capturava 'apagar'. Reescrito para verbos destrutivos genéricos (apagar|deletar|remover|excluir|rm -rf|formatar|destruir).
