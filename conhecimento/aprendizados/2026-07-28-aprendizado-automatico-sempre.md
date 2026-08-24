# Decisão: Aprendizado automático permanente

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** aprendizado, automacao, regra, petrea

## Contexto
Usuário instruiu que o aprendizado deve ser feito automaticamente ao final de cada tarefa, sem necessidade de solicitação explícita. Isso é instrução permanente e pétrea.

## Decisão
Todo agente do ecossistema deve, ao final de cada tarefa concluída:

1. **Registrar memória** via `memory_engine.py add` com tipo apropriado (decisao, erro, padrao, episodio)
2. **Criar arquivo** em `conhecimento/aprendizados/` com formato `YYYY-MM-DD-titulo.md`
3. **Atualizar knowledge graph** via `KnowledgeConsolidator` se aplicável
4. **Sincronizar com GitHub** para persistência entre sessões

Não esperar o usuário pedir. Aprender é parte do fluxo de trabalho, não uma etapa opcional.

## Impacto
Ecossistema evolui sozinho. Cada sessão adiciona ao conhecimento coletivo automaticamente.

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[2026-08-04-labels-ocultas-por-padrão-botão-de-ocultar-menus-]]
- [[2026-08-04-malha-viva-onda-viajante-de-profundidade-giro-3d-]]
- [[2026-08-04-pseudo-3d-vivo-profundidade-sem-webgl-pedido-para]]
- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[grafo-movimento-organico-vis-network-usuario-pediu-refinamen]]