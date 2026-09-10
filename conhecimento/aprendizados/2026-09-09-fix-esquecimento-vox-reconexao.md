---
tipo: padrao
tags: [vox, reconexao, persistencia, retomada, jarvis_bridge]
data: 2026-09-09
contexto: Usuário relatou que o Vox não se lembra de solicitações pendentes quando a conexão volta. Investigação revelou que a fala do usuário só era persistida DEPOIS da resposta ser gerada — uma queda durante o processamento LLM perdia a solicitação completamente, e a reconexão não tinha nada para retomar.
decisao: Persistir a fala do usuário IMEDIATAMENTE ao recebê-la (__gravar_fala_usuario no Cliente), antes de qualquer chamada LLM, de forma idempotente. Fechar o turno com __gravar_turno (idempotente) que completa a resposta sem duplicar a fala. Na reconexão, _retomar_ultima_tarefa agora detecta ambos os cenários: (a) fala sem resposta no histórico e (b) resposta do Jarvis que é APENAS uma pergunta de volta puramente interrogativa (sem ponto final antes do '?'), sinal de esclarecimento pendente — reenviando a solicitação ao LLM com contexto completo.
impacto: Solicitações do usuário nunca mais se perdem por queda de conexão durante o processamento. A reconexão retoma automaticamente inclusive o caso "Qual mapeamento você gostaria que eu faça?" em que o Jarvis tinha respondido apenas com pergunta de esclarecimento. Heurística evita falso positivo em respostas informativas seguidas de pergunta opcional (ex.: "fiz X. Quer detalhes?").
---