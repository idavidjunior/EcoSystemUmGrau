---
tipo: padrao
tags: [kernel, contexto, memoria, auditoria]
data: 2026-09-04
contexto: O Context Loader funcionava isoladamente, mas não participava da autorização do Kernel.
decisão: Incorporar o contexto recuperado ao contrato de entrada e corrigir chamadas de integração incompatíveis.
impacto: Cada autorização passa a carregar contexto relevante, memórias, conhecimento e decisões rastreáveis.
---

O kernel agora chama carregar_contexto para a tarefa atual e registra os resultados no contrato. O auditor passou a fornecer as tags exigidas por _carregar_decisoes. A busca de conhecimento usa carregamento explícito por caminho, evitando diagnóstico estático falso causado por import dinâmico implícito.

Validação: compilação dos módulos, seis testes focados, execução real do Context Loader e auditor adaptativo.
