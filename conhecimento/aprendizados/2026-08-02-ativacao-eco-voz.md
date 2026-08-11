---
tipo: decisao
tags: [voz, eco, clausula-petrea, bridge, config, regras]
data: 2026-08-02
contexto: O usuÃ¡rio pediu que o sistema de voz seja ativÃ¡vel em qualquer sessÃ£o do OpenCode (nova ou em andamento) com os comandos "Ativar Eco" e "Desativar Eco", seguindo as regras do EcoSystemUmGrau.
decisao: Adicionada a CLÃUSULA PÃ‰TREA â€” ATIVAÃ‡ÃƒO DE VOZ â€” ECO SYSTEM Ã  ConstituiÃ§Ã£o (config/agents/00-system-rules.md) e sincronizada nas 3 camadas (AGENTS.md regenerado via sync_rules.py, deployed em ~/.config/opencode/agents/). "Ativar Eco" confirma ativaÃ§Ã£o e passa a responder em Ã¡udio via jarvis_bridge.py (porta 8765, edge-tts AntonioNeural) + dispara dialogo.py --modo vad no PC. "Desativar Eco" volta ao modo texto.
impacto: Regra permanente e global, vale para qualquer sessÃ£o. sync_rules check PASS (3 camadas consistentes), preflight ALL PASS. TambÃ©m corrigido bug de escrita nÃ£o-atÃ´mica no memory_engine.py que corrompeu memories.json (memÃ³ria #46 truncada) â€” agora usa tmp + os.replace.
---

# ClÃ¡usula PÃ©trea â€” AtivaÃ§Ã£o de Voz (Eco System)

## Pedido do usuÃ¡rio

"Quando eu estiver falando com vocÃª pelo PC, vocÃª deve ativar o sistema de voz
seguindo as regras do ecossistema. Mesmo que eu abra uma nova sessÃ£o. Quando eu
digitar em qualquer sessÃ£o: **Ativar Eco**, entÃ£o vocÃª ativa todo o ecossistema e
passa a agir/responder dentro dele. **Desativar Eco** desliga."

## ImplementaÃ§Ã£o

Regra adicionada Ã  ConstituiÃ§Ã£o em `config/agents/00-system-rules.md`:

- **"Ativar Eco"** â†’ confirmar "Eco ativado. Sistema de voz online." + responder
  com Ã¡udio via `jarvis_bridge.py` (porta 8765, TTS `pt-BR-AntonioNeural`,
  base64 MP3) + disparar `python scripts/dialogo.py --modo vad` em background (PC)
- **"Desativar Eco"** â†’ confirmar "Eco desativado. Modo texto restaurado." +
  parar modo voz e finalizar `dialogo.py`
- **PersistÃªncia:** vale para QUALQUER sessÃ£o nova ou existente.

## SincronizaÃ§Ã£o (3 camadas)

1. `config/agents/00-system-rules.md` (fonte Ãºnica) â€” seÃ§Ã£o adicionada como CLÃUSULA PÃ‰TREA
2. `AGENTS.md` â€” regenerado via `python scripts/sync_rules.py update` (5 regras)
3. `~/.config/opencode/agents/00-system-rules.md` â€” deploy manual (copy) + `sync_rules check` PASS

## Bug corrigido durante a tarefa

`scripts/memory_engine.py` escrevia `memories.json` com `json.dump` direto no
arquivo final â€” a gravaÃ§Ã£o da memÃ³ria #46 foi interrompida e corrompeu o JSON
(entry truncado). Corrigido com escrita atÃ´mica (`.tmp` + `os.replace`), seguindo
a heurÃ­stica "Escrita atomica sempre" do CONHECIMENTO.md. Reparado `memories.json`
manualmente removendo o entry 46 incompleto e re-registrando a memÃ³ria.

## ValidaÃ§Ã£o

- `python scripts/sync_rules.py check` â†’ RESULTADO: 3 camadas consistentes
- `python scripts/preflight_check.py` â†’ TODOS OS TESTES PASSARAM (6/6 MCP)
- `memory_engine.py stats` â†’ 34 memÃ³rias ativas

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]