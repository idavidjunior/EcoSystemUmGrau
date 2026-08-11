# 2026-07-28: ClÃ¡usula PÃ©trea â€” Toda alteraÃ§Ã£o no ecossistema deve ser testada antes de aplicar

**Categoria:** decisao
**Contexto:** AdiÃ§Ã£o de servidores MCP via npx quebraram a inicializaÃ§Ã£o do OpenCode. Ao reiniciar, os modelos nÃ£o carregavam â†’ sistema inutilizÃ¡vel. O usuÃ¡rio precisou apagar arquivos manualmente para recuperar.
**Gravidade:** CRÃTICA â€” impeditiva, sem diagnÃ³stico visÃ­vel

## DecisÃ£o

Estabelecemos a **ClÃ¡usula PÃ©trea de ResiliÃªncia**: nenhuma alteraÃ§Ã£o em config, MCP, plugins ou agents pode ser aplicada sem passar por validaÃ§Ã£o prÃ©via.

## Mecanismos criados

1. **TriÃ¢ngulo da ResiliÃªncia** (testar sempre antes de aplicar):
   - Teste de INIT: MCP server responde `initialize` sem travar?
   - Teste de TOOLS: servidores expÃµem tools vÃ¡lidas?
   - Teste de JSON: config gerado Ã© JSON vÃ¡lido?
   - Teste de ESTRUTURA: todos os campos obrigatÃ³rios existem?

2. **Pre-flight check automÃ¡tico** (`scripts/preflight_check.py`):
   - Valida JSON do config template antes de deploy
   - Testa cada MCP server com initialize + tools/list
   - Verifica se providers, plugins e instructions estÃ£o Ã­ntegros
   - SÃ³ aplica se TODOS os testes passarem

3. **Vigilante com guard rail**:
   - Antes de deployar config, executa preflight
   - Se falhar: loga erro, NÃƒO aplica, notifica
   - Rollback automÃ¡tico para Ãºltima config vÃ¡lida

4. **Agentes com clÃ¡usula pÃ©trea**:
   - `00-system-rules.md`: constituiÃ§Ã£o â€” "testar antes de aplicar" Ã© regra imutÃ¡vel
   - `00-maestro.md`: passo obrigatÃ³rio â€” validar antes de implementar
   - `08-revisor.md`: gate de qualidade que verifica preflight

## Trigger

Sempre que qualquer alteraÃ§Ã£o for feita em:
- `config/opencode.jsonc` (template)
- `config/agents/*.md`
- `scripts/mcp-*-server.py`
- `plugins/*`
- `config/opencode-model-fallback.jsonc`

## PrÃ³ximos passos

1. Criar `scripts/preflight_check.py`
2. Integrar no vigilante
3. Atualizar system-rules e Maestro
4. Testar ciclo: alterar config â†’ preflight barra â†’ rollback

## Conexoes

- [[cluster-hub-programacao]]