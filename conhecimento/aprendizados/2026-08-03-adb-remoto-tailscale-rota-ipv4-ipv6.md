---
tipo: padrao
tags: [adb, tailscale, ipv6, ipv4, celular, android, script, powershell, scrcpy]
data: 2026-08-03
fonte: tarefa
contexto: Conexao ADB remota ao Redmi Note 11 via Tailscale falhava intermitentemente. O IPv4 100.64.71.9:5555 dava timeout as vezes, mas o IPv6 direto funcionava em outros momentos.
decisao: Criado scripts/adb-redmi.ps1 que automatiza a descoberta da rota correta. O endereco de conexao direta (CurAddr) do celular no Tailscale muda conforme a rede (WiFi local vs dados moveis): quando em rede local, a rota direta e via IP local (192.168.15.4) e o IPv4 do tailnet funciona; em dados moveis, a rota direta e IPv6 e o IPv4 do tailnet falha. O script tenta IPv6 do CurAddr primeiro e cai para IPv4.
impacto: Conexao ADB remota confiavel sem digitar IP manualmente. Instalado scrcpy 4.1 via winget para espelhamento/controle da tela do celular pelo PC. Descoberto bug PowerShell: "$target:5555" em string interpolada e lido como variavel de escopo "target:5555" (retorna vazio) - correto e "${target}:5555".
---

# 2026-08-03: ADB remoto via Tailscale - script automatico de rota (IPv4/IPv6)

## Contexto
O ADB para o Redmi Note 11 falhava de forma intermitente. `adb connect 100.64.71.9:5555`
funcionava as vezes e dava timeout (10060) em outras. Investigacao mostrou:

- `tailscale status` (texto): a linha do celular mostra o IP tailnet (IPv4 `100.64.71.9`)
  E o endereco de conexao direta atual (`CurAddr`) entre colchetes.
- Quando o celular esta na rede WiFi local, o `CurAddr` e o IP local (ex: `192.168.15.4:47999`)
  e o IPv4 do tailnet responde.
- Quando o celular muda para dados moveis ou outra rede, o `CurAddr` vira IPv6
  (ex: `[2804:18:d1:79da:991f:ad10:14b0:e76]:46423`) e o IPv4 do tailnet NAO responde
  na porta 5555 (sem caminho/derp naquela rota).

## Solucao
`scripts/adb-redmi.ps1` (auto-descoberta da rota):
1. Le `tailscale status` (formato texto - o JSON nao expoe os peers nesta versao).
2. Extrai IPv6 do CurAddr (regex `\[([0-9a-fA-F:]+)\]:\d+`) e o IPv4 tailnet (primeira coluna).
3. Tenta `adb connect` para cada candidato (IPv6 primeiro, IPv4 depois) ate conseguir.
4. Exibe `adb devices` e dicas se falhar.

## Aprendizados tecnicos
- **Rota direta muda dinamicamente**: nunca hardcodar IP do celular no Tailscale.
- **`adb tcpip 5555` nao persiste entre reboots**: apos reiniciar o celular, e preciso
  USB + `adb tcpip 5555` de novo, OU usar Wireless Debugging (`adb pair`) do Android 11+.
- **Bug PowerShell**: em string interpolada, `"$target:5555"` e parseado como variavel
  de escopo `target:5555` (vazia). Usar `${target}:5555`.
- **scrcpy** (winget: Genymobile.scrcpy) espelha e controla a tela via ADB, com
  `--adb=<path> -s <serial>` para usar um adb especifico.

## Estado
- `scripts/adb-redmi.ps1` criado e testado (conectou via IPv4 100.64.71.9:5555).
- scrcpy 4.1 instalado (win64, caminho no WinGet Links) e janela de espelhamento aberta.
- Wireless Debugging do Android ainda pendente de pareamento manual (adb pair).

## Conexoes

- [[cluster-hub-ler]]