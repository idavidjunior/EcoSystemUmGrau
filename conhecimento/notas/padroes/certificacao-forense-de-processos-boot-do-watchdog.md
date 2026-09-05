---
tags: [alvo, diferente, evita, morto, opencodeopencode, padrao]
aliases: [Certificacao forense de processos + boot do watchdog]
date: 2026-08-06
---

# Certificacao forense de processos + boot do watchdog

**Fonte:** opencode+opencode

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
8. **Portas LISTEN adicionais
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[fase2-limpeza-git-artefatos-rastreados]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]