---
tipo: padrao
tags: [watchdog, powershell, certificacao-forense, resiliencia, boot, startup]
data: 2026-08-06
contexto: "Apos a clausula petrea (memoria #129) e o watchdog resiliente (memoria #130), o filtro de orfaos ganhou certificacao forense: so mata processo se for 'lixo' comprovado. O watchdog precisa iniciar no boot sem exigir login de admin."
decisao: "Adotar Test-ForensicoLixo + Invoke-KillCertificado para TODOS os kills do watchdog, e iniciar via atalho na pasta Startup do usuario (sem privilegio de admin) em vez de tarefa agendada nativa."
impacto: "Nenhum processo vivo/em uso e morto por engano. Desktop (clausula petrea) intocavel. Watchdog sobe sozinho a cada login."
---

# Certificacao forense de processos + boot do watchdog

## Por que certificacao forense
O watchdog so pode matar lixo comprovado. Matar por engano um processo vivo quebra a
clausula petrea (desktop) e a resiliencia do proprio ecossistema.

## Test-ForensicoLixo — 10 criterios auditaveis
Retorna `@{ Liberar = bool; Motivos = [string[]] }` com a razao de CADA criterio.
So libera o kill se nenhum criterio de vida for violado:

1. **Processo existe** — inexistente = nada a fazer (nao libera).
2. **Nome confere** com o esperado (`python`, `opencode`) — nome diferente = nao e o alvo.
3. **Caminho protegido** (`opencode-aidesktop`) — jamais tocar (clausula petrea).
4. **Janela visivel** (`MainWindowHandle`/`MainWindowTitle`) — UI ativa nunca e lixo.
5. **Idade minima** — recem-criado (< N seg) nunca e morto (evita matar o que o proprio
   watchdog acabou de subir).
6. **Filhos vivos** — processo com filhos ativos = atividade real.
7. **Conexoes de rede ativas** (Established/CloseWait/TimeWait/etc.) — uso real de rede.
8. **Portas LISTEN adicionais** alem da porta orfa alvo — servico em uso.
9. **Processo pai** — pai vivo = supervisionado (audita); pai morto = orfao de verdade.
10. **Health-check HTTP** — se serve porta e responde, esta vivo.

## Invoke-KillCertificado
Envolve o teste e registra no log:
- `KILL CERTIFICADO [alvo PID n]: motivos` — matou lixo comprovado.
- `KILL BLOQUEADO [alvo PID n]: motivos` — preservou processo vivo/em uso.

Usado nos 3 caminhos do loop:
- `bridge-orfao`: socket na porta 8765 com processo dono morto (`NomeEsperado python`).
- `serve-mau`: porta 8767 escuta mas sem health HTTP (`NomeEsperado opencode`).
- `orphan-cli`: `opencode.exe run` solto, sem serve e sem desktop (`IdadeMinimaSeg 60`).

## Bug critico corrigido nesta tarefa
O parametro era `[int]$Pid`. `$PID` e variavel AUTOMATICA read-only do PowerShell.
Com `$ErrorActionPreference="SilentlyContinue"`, a atribuicao falhava em silencio e a
funcao mataria o proprio watchdog. Renomeado para `$ProcessId` (memoria #133).
Toda ocorrencia de `$Pid`/`$PID` como variavel propria e PROIBIDA no ecossistema.

## Boot do watchdog (sem admin)
- `Register-ScheduledTask -AtStartup` exigiu `Acesso negado` (privilegio de admin).
- Solucao: **atalho na pasta Startup do usuario**
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EcoSystemUmGrau_Watchdog.lnk`
  apontando para `scripts\watchdog_start.bat` (imune a espacos via `%~dp0`).
- Cria-se com WScript.Shell COM (`CreateShortcut`), `WindowStyle 7`, sem elevacao.
- O lock de PID (`watchdog.lock`) garante instancia unica mesmo se o atalho e o
  processo manual colidirem.

## Estado atual (pos-teste)
- Watchdog ativo PID 2172, lock 2172, health-checks bridge (660) e serve (4724) OK.
- Desktop intocado (8 processos `OpenCode.exe`).
- Teste de resiliencia: serve derrubado -> reiniciado em <60s.
- Teste seco da certificacao: explorer fingindo python = BLOQUEADO com motivos;
  processo supervisionado (pai vivo) = BLOQUEADO (comportamento conservador).

## Memorias relacionadas
- #129 (decisao): Clausula petrea — nunca fechar OpenCode desktop automaticamente.
- #130 (padrao): Watchdog resiliente com lock de PID e protecao do desktop.
- #131 (padrao): Saudacoes inteligentes (reconexao vs primeira vez).
- #133 (erro): Bug do parametro `$Pid` (variavel automatica read-only).

## Conexoes

- [[cluster-hub-programacao]]