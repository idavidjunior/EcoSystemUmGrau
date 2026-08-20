---
tipo: decisao
tags: [voz, eco, clausula-petrea, bridge, config, regras]
data: 2026-08-02
contexto: O usuário pediu que o sistema de voz seja ativável em qualquer sessão do OpenCode (nova ou em andamento) com os comandos "Ativar Eco" e "Desativar Eco", seguindo as regras do EcoSystemUmGrau.
decisao: Adicionada a CLÃUSULA PÉTREA — ATIVAÇÃO DE VOZ — ECO SYSTEM à Constituição (config/agents/00-system-rules.md) e sincronizada nas 3 camadas (AGENTS.md regenerado via sync_rules.py, deployed em ~/.config/opencode/agents/). "Ativar Eco" confirma ativação e passa a responder em áudio via jarvis_bridge.py (porta 8765, edge-tts AntonioNeural) + dispara dialogo.py --modo vad no PC. "Desativar Eco" volta ao modo texto.
impacto: Regra permanente e global, vale para qualquer sessão. sync_rules check PASS (3 camadas consistentes), preflight ALL PASS. Também corrigido bug de escrita não-atômica no memory_engine.py que corrompeu memories.json (memória #46 truncada) — agora usa tmp + os.replace.
---

# Cláusula Pétrea — Ativação de Voz (Eco System)

## Pedido do usuário

"Quando eu estiver falando com você pelo PC, você deve ativar o sistema de voz
seguindo as regras do ecossistema. Mesmo que eu abra uma nova sessão. Quando eu
digitar em qualquer sessão: **Ativar Eco**, então você ativa todo o ecossistema e
passa a agir/responder dentro dele. **Desativar Eco** desliga."

## Implementação

Regra adicionada à Constituição em `config/agents/00-system-rules.md`:

- **"Ativar Eco"** â†’ confirmar "Eco ativado. Sistema de voz online." + responder
  com áudio via `jarvis_bridge.py` (porta 8765, TTS `pt-BR-AntonioNeural`,
  base64 MP3) + disparar `python scripts/dialogo.py --modo vad` em background (PC)
- **"Desativar Eco"** â†’ confirmar "Eco desativado. Modo texto restaurado." +
  parar modo voz e finalizar `dialogo.py`
- **Persistência:** vale para QUALQUER sessão nova ou existente.

## Sincronização (3 camadas)

1. `config/agents/00-system-rules.md` (fonte única) — seção adicionada como CLÃUSULA PÉTREA
2. `AGENTS.md` — regenerado via `python scripts/sync_rules.py update` (5 regras)
3. `~/.config/opencode/agents/00-system-rules.md` — deploy manual (copy) + `sync_rules check` PASS

## Bug corrigido durante a tarefa

`scripts/memory_engine.py` escrevia `memories.json` com `json.dump` direto no
arquivo final — a gravação da memória #46 foi interrompida e corrompeu o JSON
(entry truncado). Corrigido com escrita atômica (`.tmp` + `os.replace`), seguindo
a heurística "Escrita atomica sempre" do CONHECIMENTO.md. Reparado `memories.json`
manualmente removendo o entry 46 incompleto e re-registrando a memória.

## Validação

- `python scripts/sync_rules.py check` â†’ RESULTADO: 3 camadas consistentes
- `python scripts/preflight_check.py` â†’ TODOS OS TESTES PASSARAM (6/6 MCP)
- `memory_engine.py stats` â†’ 34 memórias ativas

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]