# 2026-08-02 - Regras do ecossistema: garantia de obediÃªncia pelo LLM

## Contexto
O usuÃ¡rio perguntou se as regras estavam no local correto. InvestigaÃ§Ã£o honesta
revelou que NÃƒO estavam: `config/agents/00-system-rules.md` era um "agente fantasma"
(sem frontmatter, sem referÃªncias de outros agents) e nÃ£o existia AGENTS.md â€” ou seja,
as ClÃ¡usulas PÃ©treas dependiam do LLM "lembrar" de invocar o agente. Na prÃ¡tica nÃ£o
eram aplicadas.

## Problema raiz
- `00-system-rules.md` nÃ£o tinha frontmatter YAML â†’ nÃ£o era agente vÃ¡lido (sÃ³ aparecia
  `options:{}`, sem `mode` no debug config)
- Nenhum agent referenciava as regras (busca por system-rules sÃ³ achava o prÃ³prio arquivo)
- NÃ£o existia `AGENTS.md` (convenÃ§Ã£o do opencode: auto-carregado em toda sessÃ£o)
- `instructions` do opencode.jsonc nÃ£o incluÃ­am as regras

## CorreÃ§Ã£o (3 camadas para garantir obediÃªncia)
1. **`AGENTS.md` na raiz** â€” auto-carregado pelo opencode em TODA sessÃ£o. ContÃ©m as
   3 ClÃ¡usulas PÃ©treas + 5 Regras de Ouro em formato executÃ¡vel. ConfirmaÃ§Ã£o: o
   system-reminder da sessÃ£o atual mostrou o AGENTS.md sendo injetado.
2. **`instructions` no template `config/opencode.jsonc`** â€” adicionadas
   `AGENTS.md` e `config/agents/00-system-rules.md` (injeÃ§Ã£o redundante proposital).
3. **Frontmatter no `00-system-rules.md`** â€” `description` + `mode: subagent`
   (agora aparece como agente vÃ¡lido no debug config; subagent, nÃ£o primary, para nÃ£o
   competir com o Maestro).

## ValidaÃ§Ã£o
- `opencode debug config`: CONFIG VALIDA
- `preflight_check.py`: TODOS TESTES PASSARAM
- `ecosystem sync`: commit + push (d523c6f), deploy OK, agentes (16) copiados

## LiÃ§Ã£o
- Regras que devem valer SEMPRE â†’ `AGENTS.md` (auto-carregado) + `instructions` no
  opencode.jsonc. Um arquivo em `config/agents/` sem frontmatter nÃ£o garante nada.
- `mode: primary` criaria 2 agentes primÃ¡rios (conflito com Maestro) â†’ usar `subagent`.

## Conexoes

- [[cluster-hub-programacao]]