---
tipo: decisao
tags: [vox, tailscale, winhttpautoproxysvc, sc-config, conectividade, bridge, android-diagnostics]
data: 2026-09-04
---

# Restauracao da conectividade Tailscale do Vox

## Contexto
Bridge Jarvis saudavel (PID rodando, porta 8765 escutando em 0.0.0.0) mas o app
VoxUmGrau nao conectava. O usuario escolheu a estrategia de corrigir o Tailscale.

## Diagnostico
Causa raiz: servico WinHttpAutoProxySvc estava desabilitado e, mesmo forcado a
Start=3 (Manual) via registro, recusava iniciar com erro 1058 ("servico nao pode
ser iniciado porque esta desativado ou nao tem dispositivos ativados associados").
Como iphlpsvc (e portanto Tailscale) dependiam do WinHttpAutoProxySvc, ambos
falhavam com erro 1068 (dependencia), derrubando toda a conectividade do tailnet.

Erros confirmados: sc query iphlpsvc -> 1068; sc start WinHttpAutoProxySvc -> 1058.

## Decisao / Workaround
Reescrever as dependencias dos servicos via sc config (elevado), removendo o
WinHttpAutoProxySvc da cadeia:

- sc config iphlpsvc start= auto depend= RpcSS/winmgmt/tcpip/nsi
- sc config Tailscale start= auto depend= Dnscache/netprofm

Ambos passaram a Running. O celular redmi-note-11 voltou ao tailnet (ativo) e o
app faz heartbeat a cada 15s no bridge_log.

## Correlato: probe do android_diagnostics.py
O script usava {"tipo":"ping","origem":"diagnostico"} na primeira mensagem. A
bridge so reconhece o health-check com origem EXATAMENTE "health-check" para
responder pong sem disparar a saudacao LLM (lenta). Background "diagnostico" cai
na saudacao e estoura o timeout de 3s. Correcao:
- origem = "health-check"
- open_timeout e timeout de recv = 8s (a bridge pode levar 3-4s quando ocupada)

## Impacto
- Conectividade ponta a ponta restaurada (ponto USB 10.201.3.188, tailnet
  100.91.141.101 via celular 100.64.71.9).
- Self-test do android_diagnostics.py: ADB ok, WebSocket conectado e respondendo.
- Diagnostico completo: 0 erros, app rodando (PID 5016, 100 MB, v1.1.1).

## Observabilidade
- TRACE Velocidade: antes de criar um servico novo, verificar dependencias dos
  servicos envolvidos (WinHttpAutoProxySvc e dependencia silenciosa do iphlpsvc /
  Tailscale). Servico Windows "desabilitado" nao reverte simplesmente por Start=3;
  a causa pode ser politica/trigger e o workaround real e remover a dependencia.
