---
tags: [300, chama, check, decisao, opencode, resil]
aliases: [Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper]
date: 2026-08-27
---

# Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper

**Fonte:** opencode

## Diagnostico (antes)
- `system_guardian.py` (Python): RAM/CPU, restart de bridge 8765, serve 8767,
  narrador, tts, widget; instala o `ensure_bridge_flag` e chama `opencode_resilience`.
- `watchdog.ps1` (PowerShell): SEGUNDO loop para bridge/serve + limpeza de orfaos
  CLI + widget unico + certificacao forense de kill.
- `vigilante.ps1`: orquestrador que ja mantem `system_guardian.py` vivo (timer 5 min).
- `bridge_resiliencia.py` / `connection_guardian.py`: dominio ADB/Tailscale
  (conectividade), NAO processo do PC — confundido no primeiro diagnostico, corrigido.

Tripla redundancia em bridge/serve. A peca que faltava no guardian era a gestao
PROATIVA de RAM (alerta antes do limite) e a portabilidade da certificacao forense.

## O que foi feito
1. **Camada proativa de RAM** (ja implementada antes desta unificacao): constantes
   `RAM_EARLY_WARN_MB=1024`, `PROACTIVE_COOLDOWN_S=300`; funcoes `_record_ram_sample`,
   `_ram_slope_mb_per_min`, `check_proactive_ram` (chama `opencode_resil
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]