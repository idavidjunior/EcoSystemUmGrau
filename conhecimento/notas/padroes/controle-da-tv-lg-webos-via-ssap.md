---
tags: [input, opencode, padrao, pointer, remotas, socket]
aliases: [Controle da TV LG webOS via SSAP]
date: 2026-08-04
---

# Controle da TV LG webOS via SSAP

**Fonte:** opencode

## Contexto

O usuário pediu um plano e sequência de aprendizado do controle da TV e execução em segundo plano. A infraestrutura existente tinha apenas scripts de pareamento (`lg_pair_tv.py`, `tv_pair_prompt.py`, `device_probe.py`) e uma chave salva em `scripts/keys/lgtv_50UT8050PSA.json`.

## Decisão

Criar `scripts/tv_control.py` — biblioteca SSAP com classe `TvSap` cobrindo: registro, status (poder + volume), volume set/step, mute, power_off, screen on/off, launch_app, get_foreground_app, get_input_list, media control e teclas remotas via pointer input socket.

## Aprendizados técnicos

- A resposta de `register` vem como `{"type":"registered","payload":{"client-key":"..."}}` — **sem** `returnValue`. A verificação inicial errada quebrava a conexão.
- A chave salva (f61bccaabd247d8ae1702672d3f9c4f5) foi registrada com um manifesto **limitado** (sem `READ_INSTALLED_APPS`). Por isso `listApps` retorna `401 insufficient permissions`, mas volume, tela, launch e teclas funcionam.
- Para l
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]
- [[widget-desktop-grafo-tempo-real]]