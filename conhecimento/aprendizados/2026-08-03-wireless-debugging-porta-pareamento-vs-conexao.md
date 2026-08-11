---
tipo: erro
tags: [android, adb, wireless-debugging, pareamento, mdns, porta]
data: 2026-08-03
fonte: tarefa
contexto: Pareamento do Wireless Debugging do Android (Redmi Note 11, Android 13) falhava com 'adb pair' retornando 'protocol fault (couldn't read status message): No error' mesmo com codigo valido.
decisao: Diagnosticado que a porta mostrada na tela junto do codigo de pareamento e a porta de PAREAMENTO, e nao a porta de CONEXAO. O comando 'adb pair' precisa da porta _adb-tls-pairing, mas depois o 'adb connect' usa a porta _adb-tls-connect. Descobrir ambas via 'adb mdns services'. Ao gerar um novo codigo, a porta de pareamento muda (a de conexao tende a se manter).
impacto: Pareamento bem-sucedido: 'Successfully paired to 192.168.15.4:38591'. Conexao oficial via wireless debugging: adb connect 100.64.71.9:40755 (porta de conexao via Tailscale). script adb-redmi.ps1 atualizado para descobrir a porta de conexao automaticamente via mdns.
---

# 2026-08-03: Wireless Debugging Android - porta de pareamento vs porta de conexao

## Problema
`adb pair 100.64.71.9:40755 <codigo>` retornava:
`error: protocol fault (couldn't read status message): No error`

O usuario fornecia o IP:porta e o codigo mostrados na tela de pareamento do celular,
mas o pareamento sempre falhava.

## Causa raiz
O Android Wireless Debugging tem **DUAS portas distintas**:

1. **Porta de pareamento (pairing)** — usada pelo `adb pair`. Exibida na tela junto
   do codigo. Servico mDNS: `_adb-tls-pairing._tcp`.
2. **Porta de conexao (connect)** — usada pelo `adb connect`. Servico mDNS:
   `_adb-tls-connect._tcp`.

A tela do celular mostra **o IP:porta de conexao** (ou uma porta de pareamento efemera?),
mas o `adb pair` espera a porta de pareamento. Parear na porta errada causa protocol fault.

## Descoberta via mDNS
```
adb mdns services
adb-6d92eed7-VIUVer   _adb-tls-pairing._tcp   192.168.15.4:38591
adb-6d92eed7-VIUVer   _adb-tls-connect._tcp   192.168.15.4:40755
```
- Pareamento: `adb pair 192.168.15.4:38591 <codigo>` -> `Successfully paired`
- Conexao: `adb connect 100.64.71.9:40755` (mesma porta, via Tailscale)

## Detalhe importante
- Ao tocar "Gerar novo codigo", a **porta de pareamento muda**; a de conexao tende a
  permanecer enquanto o servico estiver ativo.
- O pareamento fica **salvo no celular** — nao precisa parear toda vez, apenas conectar.
- Apos **reboot** do celular, a porta de conexao pode mudar -> consultar via
  `adb mdns services` (o script adb-redmi.ps1 ja faz isso automaticamente).

## Estado
- Pareamento concluido (guid adb-6d92eed7-VIUVer).
- `scripts/adb-redmi.ps1` atualizado: detecta porta de conexao via mdns e tenta
  com fallback para 5555 (tcpip classico).

## Conexoes

- [[cluster-hub-programacao]]