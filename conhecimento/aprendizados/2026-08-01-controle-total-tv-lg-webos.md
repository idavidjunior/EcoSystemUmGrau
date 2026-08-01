# Controle de TV LG (01/08/2026)

## TV identificada
- Modelo: **50UT8050PSA** (LG 50" webOS, firmware p20.33.31.61)
- Hostname mDNS: `[LG] webOS TV UT8050PSA`
- IP local: `192.168.15.6` (MAC `00:a1:59:82:bb:08`, LG Electronics)
- Serial: `412AZAL87976`
- Serviços: SSAP (wss://3001), Google Cast (8009), AirPlay 2 (7000)

## Controle nativo (total)
- Biblioteca: `pywebostv` + CLI `lgtvremote-cli` (porta 3001 wss, secure).
- Pareamento: PROMPT (confirmação na tela) ou WoL para ligar.
- Client-key salvo em `scripts/keys/lgtv_50UT8050PSA.json` (`f61bccaabd247d8ae1702672d3f9c4f5`).
- Portas: 3000 (ws, bloqueado em TVs novas) → usar 3001 (wss). Porta 3000 faz reset em newer models → usar secure=True.

## Comandos
- `lgtv --tv 192.168.15.6 power-status` → {"power":"on/off",...}
- `lgtv --tv <ip> on` → Wake-on-LAN (MAC `00:a1:59:82:bb:08`)
- `lgtv --tv <ip> off|power|screen-on`
- `lgtv --tv <ip> apps|app <id>|inputs|input <n>`
- `lgtv --tv <ip> volume up|down|<n>|mute|nav <dir>`

## Regra de ouro (permanente, 01/08/2026)
- **Sempre iniciar no volume 10. Nunca deixar no máximo.** O usuário ajusta depois.

## Estado
- Pairing OK; TV controlada via SSH/CLI; ligar via WoL; SSAP 3000 bloqueado mas 3001 funciona.
