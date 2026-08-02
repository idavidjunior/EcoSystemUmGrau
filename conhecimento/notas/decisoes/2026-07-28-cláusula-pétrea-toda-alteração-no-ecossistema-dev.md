---
tags: [decisao, opencode]
aliases: [2026-07-28: Cláusula Pétrea — Toda alteração no ecossistema ]
date: 2026-08-01
---

# 2026-07-28: Cláusula Pétrea — Toda alteração no ecossistema deve ser testada antes de aplicar

**Fonte:** opencode

# 2026-07-28: Cláusula Pétrea — Toda alteração no ecossistema deve ser testada antes de aplicar

**Categoria:** decisao
**Contexto:** Adição de servidores MCP via npx quebraram a inicialização do OpenCode. Ao reiniciar, os modelos não carregavam → sistema inutilizável. O usuário precisou apagar arquivos manualmente para recuperar.
**Gravidade:** CRÍTICA — impeditiva, sem diagnóstico visível

## Decisão

Estabelecemos a **Cláusula Pétrea de Resiliência**: nenhuma alteração em config, MCP, plugins ou agents pode ser aplicada sem passar por validação prévia.

## Mecanismos criados

1. **Triângulo da Resiliência** (testar sempre antes de aplicar):
   - Teste de INIT: MCP server responde `initialize` sem travar?
   - Teste de TOOLS: servidores expõem tools válidas?
   - Teste de JSON: config gerado é JSON válido?
   - Teste de ESTRUTURA: todos os campos obrigatórios existem?

2. **Pre-flight check automático** (`scripts/preflight_check.py`):
   - Valida JSON do config template antes de deploy
   - Testa cada MCP server com initialize + tools/list
   - Verifica se providers, plugins e instructions estão íntegros
   - Só aplica se TODOS os testes passarem

3. **Vigilante com guard rail**:
   - Antes de deployar config, executa preflight
   - Se falhar: loga erro, NÃO aplica, notifica
   - Rollback automático para última config válida

4. **Agentes com cláusula pétrea**:
   - `00-system-rules.md`: constituição — "testar antes de aplicar" é regra imutável
   - `00-maestro.md`: passo obrigatório — validar antes de implementar
   - `08-revisor.md`: gate de qualidade que verifica preflight

## Trigger

Sempre que qualquer alteração for feita em:
- `config/opencode.jsonc` (template)
- `config/agents/*.md`
- `scripts/mcp-*-server.py`
- `plugins/*`
- `config/opencode-model-fallback.jsonc`

## Próximos passos

1. Criar `scripts/preflight_check.py`
2. Integrar no vigilante
3. Atualizar system-rules e Maestro
4. Testar ciclo: alterar config → preflight barra → rollback

## Conexoes

- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[2026-07-27-setup-plug-play-e-organizacao-github]]
- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[decisao-hub-decisoes]]