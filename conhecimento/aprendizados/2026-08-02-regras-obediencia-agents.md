# 2026-08-02 - Regras do ecossistema: garantia de obediência pelo LLM

## Contexto
O usuário perguntou se as regras estavam no local correto. Investigação honesta
revelou que NÃO estavam: `config/agents/00-system-rules.md` era um "agente fantasma"
(sem frontmatter, sem referências de outros agents) e não existia AGENTS.md — ou seja,
as Cláusulas Pétreas dependiam do LLM "lembrar" de invocar o agente. Na prática não
eram aplicadas.

## Problema raiz
- `00-system-rules.md` não tinha frontmatter YAML â†’ não era agente válido (só aparecia
  `options:{}`, sem `mode` no debug config)
- Nenhum agent referenciava as regras (busca por system-rules só achava o próprio arquivo)
- Não existia `AGENTS.md` (convenção do opencode: auto-carregado em toda sessão)
- `instructions` do opencode.jsonc não incluíam as regras

## Correção (3 camadas para garantir obediência)
1. **`AGENTS.md` na raiz** — auto-carregado pelo opencode em TODA sessão. Contém as
   3 Cláusulas Pétreas + 5 Regras de Ouro em formato executável. Confirmação: o
   system-reminder da sessão atual mostrou o AGENTS.md sendo injetado.
2. **`instructions` no template `config/opencode.jsonc`** — adicionadas
   `AGENTS.md` e `config/agents/00-system-rules.md` (injeção redundante proposital).
3. **Frontmatter no `00-system-rules.md`** — `description` + `mode: subagent`
   (agora aparece como agente válido no debug config; subagent, não primary, para não
   competir com o Maestro).

## Validação
- `opencode debug config`: CONFIG VALIDA
- `preflight_check.py`: TODOS TESTES PASSARAM
- `ecosystem sync`: commit + push (d523c6f), deploy OK, agentes (16) copiados

## Lição
- Regras que devem valer SEMPRE â†’ `AGENTS.md` (auto-carregado) + `instructions` no
  opencode.jsonc. Um arquivo em `config/agents/` sem frontmatter não garante nada.
- `mode: primary` criaria 2 agentes primários (conflito com Maestro) â†’ usar `subagent`.
