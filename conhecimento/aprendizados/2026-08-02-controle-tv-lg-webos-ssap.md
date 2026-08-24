---
tipo: padrao
tags: [tv, lg, webos, ssap, tv_control, python]
data: 2026-08-02
contexto: Aprendizado do controle nativo da TV LG 50UT8050PSA (webOS) via SSAP wss://192.168.15.6:3001
decisao: Criar scripts/tv_control.py como biblioteca unica de controle da TV
impacto: Jarvis agora controla volume, tela, apps, teclas e poder da TV por voz
---

# Controle da TV LG webOS via SSAP

## Contexto

O usuário pediu um plano e sequência de aprendizado do controle da TV e execução em segundo plano. A infraestrutura existente tinha apenas scripts de pareamento (`lg_pair_tv.py`, `tv_pair_prompt.py`, `device_probe.py`) e uma chave salva em `scripts/keys/lgtv_50UT8050PSA.json`.

## Decisão

Criar `scripts/tv_control.py` — biblioteca SSAP com classe `TvSap` cobrindo: registro, status (poder + volume), volume set/step, mute, power_off, screen on/off, launch_app, get_foreground_app, get_input_list, media control e teclas remotas via pointer input socket.

## Aprendizados técnicos

- A resposta de `register` vem como `{"type":"registered","payload":{"client-key":"..."}}` — **sem** `returnValue`. A verificação inicial errada quebrava a conexão.
- A chave salva (f61bccaabd247d8ae1702672d3f9c4f5) foi registrada com um manifesto **limitado** (sem `READ_INSTALLED_APPS`). Por isso `listApps` retorna `401 insufficient permissions`, mas volume, tela, launch e teclas funcionam.
- Para listar apps é preciso re-parear com o manifesto completo (constante `MANIFEST` no tv_control.py). A TV bloqueia tentativas em excesso com `403 too many pairing requests` — é preciso aguardar e refazer o pareamento na tela da TV (PROMPT).
- Teclas remotas usam `ssap://com.webos.service.networkinput/getPointerInputSocket` + conexão WSS com `hello` (socketPath) + mensagens `button` (key, down true/false).
- Wake-on-LAN com magic packet para `00:a1:59:82:bb:08` liga a TV mesmo desligada.

## Validação

- `python tv_control.py status` → poder Active, volume confirmado
- `python tv_control.py volume 10` → sucesso (regra: inicializar volume em 10)
- `launch_app('youtube.leanback.v4')` → YouTube abriu (foreground confirmado)
- `key ok` → tecla OK enviada com sucesso
- `screen off/on` → responderam sem erro

## Próximos passos

- Re-parear na TV com manifesto completo (aguardar janela sem `403`) para liberar `listApps` e todos os 147 apps.
- Integrar os comandos de TV no `jarvis_bridge.py` para controle por voz.

## Conexoes

- [[python-decoradores-e-metaprogramação]]
- [[python-gil-e-concorrência]]
- [[python-idioms-e-boas-práticas]]
- [[python-sintaxe-e-núcleo-da-linguagem]]