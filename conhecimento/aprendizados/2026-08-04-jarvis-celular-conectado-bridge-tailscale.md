---
tipo: episodio
tags: [jarvis, bridge, celular, tailscale, websocket, voxumgrau, conectividade, validado]
data: 2026-08-04
fonte: tarefa
contexto: Usuario enfatizou que o importante e manter o Jarvis do celular conectado ao bridge. Verificacao de estado da ponte (PID 2676, porta 8765) e da conexao do celular.
decisao: Confirmado e documentado que o Jarvis do celular conecta ao bridge via rede Tailscale por WebSocket, de forma independente de ADB/USB. A conexao usa o IP fixo 100.64.71.9 e funciona em WiFi ou dados moveis.
impacto: A prioridade do ecossistema (celular fala com Jarvis) esta garantida pela rede Tailscale, nao depende de cabo USB nem do estado do ADB. Bridge saudavel: Responding=True, 24MB RAM.
---

# 2026-08-04: Jarvis do celular conectado ao bridge via Tailscale

## Verificacao validada (100%)
- **Bridge:** python PID 2676 escutando `0.0.0.0:8765`, Responding=True, 24MB RAM.
- **Conexao ativa:** TCP estabelecido `100.64.71.9:47112` -> `100.91.141.101:8765`
  (celular -> PC via Tailscale), confirmado com `Get-NetTCPConnection`.
- **Estado persistido:** `scripts/bridge_estado.json` -> ultima_conexao `2026-08-04 05:28:34`,
  ip `100.64.71.9` (registrado por `jarvis_bridge.py` linha 1008).
- **App no celular:** VoxUmGrau versionCode 14 instalado e rodando (PID 2803 em teste anterior).

## Conclusao arquitetural
O Jarvis do celular NAO depende de ADB/USB para manter-se conectado:

- ADB (USB/Tailscale/wireless) serve para **desenvolvimento/instalacao/espelhamento** (scrcpy).
- A **comunicacao de voz** do app com o bridge usa WebSocket sobre a rede Tailscale,
  rota independente, funciona em WiFi ou dados moveis, com IP fixo 100.64.71.9.

## Ferramentas de verificacao rapida
```powershell
# Bridge escutando?
Get-NetTCPConnection -LocalPort 8765 -State Listen
# Celular conectado agora?
Get-NetTCPConnection -LocalPort 8765 -State Established
# Estado salvo da ultima conexao
Get-Content scripts\bridge_estado.json
```
