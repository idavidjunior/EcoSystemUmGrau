---
tipo: padrao
tags: [adb, android, cmd, miui, redmi-note-11, skill, automacao]
data: 2026-08-06
contexto: Usuario pediu para Jarvis virar perito em ADB. Skill adb-perito/SKILL.md ja existia (749 linhas) mas usuario reiterou o pedido exigindo estudo completo.
decisao: Explorar o subsystem `cmd` no celular real (Redmi Note 11 via Tailscale 100.64.71.9:5555). O `cmd -l` listou ~300 servicos do MIUI/HyperOS. Testei individualmente 12+ servicos via `cmd SERVICE help` e capturei a saida real. Cada um tem sintaxe e subcomandos proprios. Descobri que `cmd package` == `pm`, `cmd activity` == `am`, `cmd window` == `wm`, mas `cmd appops`/`cmd shortcut`/`cmd uimode` etc nao tem alias - sao acessiveis somente via `cmd`. `cmd appops` e mais granular que `pm grant/revoke` (4 modos: allow/ignore/deny/default por operacao). `cmd uimode night yes` liga o dark mode instantaneamente. `cmd location providers add-test-provider` permite mock GPS depois de `appops set PKG android:mock_location allow`. Erros de digitacao presentes no skill original foram corrigidos (Xiaomi, "Saudaveis extras"->"Verbosidades extras", "sideshow"->adb pull, "ponto meio"->gesto de acessibilidade etc).
impacto: Jarvis agora opera ADB com cobertura completa do ecossistema Android - nao so pm/am/input/logcat, mas tambem todos os servicos do sistema via `cmd`. Skill atualizada de 749 -> ~1010 linhas. Script de diagnostico PowerShell e padrao de deteccao de tela bloqueada adicionados para automacao. Habilita troubleshooting avancado, automacao de UI, depuracao granular e manipulacao de estado do sistema via bridge por voz.
aprendizados:
  - `cmd -l` lista todos os servicos disponiveis para `cmd SERVICE` (varia por OEM)
  - `cmd package` == `pm`, `cmd activity` == `am`, `cmd window` == `wm` (aliases)
  - `cmd appops set PKG android:mock_location allow` habilita mock GPS para `cmd location providers add-test-provider`
  - `cmd uimode night yes|no|auto|custom_schedule|custom_bedtime` controla dark mode programaticamente
  - `cmd statusbar expand-notifications|collapse` automatiza painel de notificacoes
  - `cmd notification post TAG "texto"` posta notificacao de teste
  - `cmd role get-role-holders android.app.role.BROWSER` descobre browser padrao
  - Em Redmi/Xiaomi, bootloader precisa Mi Unlock (7 dias de espera) - flash via fastboot so apos desbloqueio
  - Para detectar tela bloqueada: `dumpsys window | Select-String mShowingLockscreen`
fontes:
  - saida direta de `adb shell cmd <service> help` no Redmi Note 11 (37.0.1-15733141)
  - adb help completo
  - https://developer.android.com/tools/adb (timeout no webfetch, conteudo reconstruido empiricamente)
skill_alvo: mcp/android/habilidades/adb-perito/SKILL.md
---

# ADB Perito - Expansao Completa do Subsystem `cmd`

## O que foi feito
Skill `mcp/android/habilidades/adb-perito/SKILL.md` expandida de 749 para ~1010 linhas. Jarvis agora opera o ADB em modo perito, cobrindo nao so os subcomandos classicos (pm, am, input, logcat, dumpsys) mas tambem todo o subsystem `cmd` - a bridge moderna para servicos do sistema Android.

## Por que importa
O `cmd` e mais flexivel que `service call` (que usa codigos binder opacos) e expoe servicos que nao tem alias. `cmd appops` permite controle de permissoes runtime mais granular que `pm grant/revoke`. `cmd uimode` liga dark mode sem tocar UI. `cmd statusbar` automatiza a barra de status. `cmd location` permite mock GPS para testes.

## Servicos descobertos no Redmi Note 11 (MIUI)
~300 servicos via `cmd -l`. Os relevantes para automacao estao documentados na skill. Servicos MIUI especificos (HyperPackageManager, MiuiFreeDragService, miui.powerkeeper.PowerMillet etc) estao listados na secao "Hidden Gems".

## Erros corrigidos
- "Xiaomi/MIUI" (estava "Xiomi")
- "Verbosidades extras" (estava "Saudaveis extras")
- "adb pull /data/anr/traces.txt" (estava "adb sideshow")
- "HOME (gesto de acessibilidade)" (estava "HOME点半" com caracteres chineses)
- "Dispositivo secundario: emulador (Android Virtual Device)" (estava "emulador生殖" com caracter japones)
- Bloco de mapeamento mental floodado com marcadores de tabela

## Conexoes

- [[cluster-hub-programacao]]