## Evolução Contínua do Conhecimento

Este projeto mantém uma base de conhecimento viva em `.opencode/skills/android-pure-sdk/SKILL.md` (espelhada em `~/.claude/skills/android-pure-sdk/SKILL.md`).

### Regras para o AI

1. **Sempre que resolver um problema não-trivial** (bug, nova funcionalidade, descoberta técnica) — atualize o `SKILL.md` com o aprendizado.

2. **Quando atualizar:**
   - Um bug foi encontrado e corrigido (adicione à tabela de erros comuns com causa raiz e fix)
   - Um novo padrão de código foi estabelecido
   - Uma decisão de design importante foi tomada
   - Uma técnica/dica útil foi descoberta
   - O build pipeline ganhou novo parâmetro ou funcionalidade

3. **Formato das atualizações:**
   - Se for erro: adicione linha na tabela de erros comuns
   - Se for padrão: adicione nova seção no local apropriado
   - Se for decisão: adicione item em "Key Design Decisions"
   - Se for dica: adicione subseção no contexto relevante

4. **Mantenha a consistência:** Sincronize o arquivo global (`~/.claude/skills/`) sempre que atualizar o local.

5. **Nunca remova** conhecimento existente — apenas adicione ou refine.
