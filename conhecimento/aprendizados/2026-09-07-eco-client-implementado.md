---
tipo: episodio
tags: [eco-client, runtime, implementacao, stdlib]
data: 2026-09-07
contexto: implementação do cliente Python embutido sem mudar a UI
decisao: EcoClient com import direto e falha suave reutilizando runtime e memória
impacto: integração programática imediata com teste de fumaça aprovado
---

O cliente vive em scripts e eco client. Ele resolve a base sozinho.
Ele usa import tardio para evitar ciclo e falha suave.
O teste de fumaça passou com status e busca e checkpoint.
A validação do kernel e a auditoria responderam certo.
A spec mudou de proposta para ativa após a entrega.
