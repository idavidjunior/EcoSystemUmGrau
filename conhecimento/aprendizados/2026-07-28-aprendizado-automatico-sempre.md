# DecisÃ£o: Aprendizado automÃ¡tico permanente

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** aprendizado, automacao, regra, petrea

## Contexto
UsuÃ¡rio instruiu que o aprendizado deve ser feito automaticamente ao final de cada tarefa, sem necessidade de solicitaÃ§Ã£o explÃ­cita. Isso Ã© instruÃ§Ã£o permanente e pÃ©trea.

## DecisÃ£o
Todo agente do ecossistema deve, ao final de cada tarefa concluÃ­da:

1. **Registrar memÃ³ria** via `memory_engine.py add` com tipo apropriado (decisao, erro, padrao, episodio)
2. **Criar arquivo** em `conhecimento/aprendizados/` com formato `YYYY-MM-DD-titulo.md`
3. **Atualizar knowledge graph** via `KnowledgeConsolidator` se aplicÃ¡vel
4. **Sincronizar com GitHub** para persistÃªncia entre sessÃµes

NÃ£o esperar o usuÃ¡rio pedir. Aprender Ã© parte do fluxo de trabalho, nÃ£o uma etapa opcional.

## Impacto
Ecossistema evolui sozinho. Cada sessÃ£o adiciona ao conhecimento coletivo automaticamente.

## Conexoes

- [[grafo-movimento-organico-vis-network-usuario-pediu-refinamen]]