---
tags: [cobertura, conh, opencode, opencodeopencodeopencodeopencodeopencodeopencodeopencodeopen, padrao, virar]
aliases: [Aprendizado: Jarvis manifesta o que quer aprender]
date: 2026-08-10
---

# Aprendizado: Jarvis manifesta o que quer aprender

**Fonte:** opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode

## Resumo

Jarvis agora fala periodicamente o que gostaria de aprender, baseado em
experiências reais do ecossistema.

## Mecanismo

- `scripts/desejo_aprendizado.py` — coleta 4 sinais, escolhe até 3 (fora da
  janela das últimas 3 manifestações), persiste histórico e fala via TTS.
- `scripts/desejos_loop.py` — loop em background (intervalo 45min, janela
  9h-22h), configurável por env `DESEJOS_INTERVALO/INICIO/FIM`.
- `scripts/desejos_start.bat` — inicia o loop em background.

## Lições

- Proatividade de voz precisa de base real (memória/recorrências/cobertura) e
  anti-repetição (assinatura + janela), senão vira ruído.
- Quiet hours evitam manifestação em horário inoportuno.

## Próximos passos

- Iniciar loop em background quando o usuário quiser voz ativa.
- Integrar sugestões ao pipeline de aprendizado (o desejo manifestado pode virar
  uma tarefa de estudo registrada no runtime).

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[2026-08-04-labe
## Conexoes

- [[2026-08-03-adb-remoto-via-tailscale-script-automatico-de-rot]]
- [[cluster-hub-ecossistema]]
- [[compreensao-de-pedidos-refino-com-a-llm-do-opencode-primaria]]
- [[config-2026-07-28-formato-correto-do-mcp-no-opencode-1187]]
- [[eco-agente-e-comando-global]]
- [[padrao-hub-padroes]]