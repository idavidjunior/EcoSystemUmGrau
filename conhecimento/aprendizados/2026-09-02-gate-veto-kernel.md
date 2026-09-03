---
tipo: decisao
tags: [gate, veto, kernel, governanca, roteamento, compreensao-pedidos]
data: 2026-09-02
contexto: Fase 2 do mecanismo de governanca — integrar o gate de veto no roteamento do kernel, apos a Fase 1 (gerar_checklist + tool MCP veto_pedido) aprovada.
decisao: Adicionar o metodo gate_veto ao kernel (scripts/runtime_kernel.py) e chamar no route_task, logo apos authorize. Pedidos que disparam regra de veto retornam route BLOQUEADO antes de rotear. execute_plan trata BLOQUEADO sem crash. Reutiliza gerar_checklist do modulo compreensao via importlib (mesmo padrao que o kernel ja usava para compreender) — sem duplicar a logica de vetos (anti-Frankestein).
impacto: Pedidos destrutivos (DESTRUICAO) ou de sincronizacao de git sem o gate (SINCRONIZAR_GIT) sao bloqueados no roteamento. Toda chamada a route_task (CLI route, execute-plan, integracoes) passa pelo gate. Fail-soft: se o modulo de compreensao estiver indisponivel, o pedido segue APROVADO (nao trava a execucao).
validacao: py_compile OK; route "criar csv" -> DIRECT/APROVADO; route "apagar pasta de producao" -> BLOQUEADO (DESTRUICAO); route "commit direto sem gate" -> BLOQUEADO (a partir de SINCRONIZAR_GIT, complexidade HIGH); execute-plan bloqueado nao crasha. JSON do gate confirma aprovado/vetos/itens/motivo.
nota_tecnica: o memory_engine.add pode demorar por causa da reindexacao semantica (chama LLM); usar timeout amplo. A primeira execucao do add pode persistir a memoria mas o shell cortar a saida no timeout — conferir sempre no memories.json.
