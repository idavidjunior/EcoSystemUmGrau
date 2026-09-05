---
tags: [chama, grava, opencodeopencode, padrao, resetar, ultimo]
aliases: [Fix ativação de voz + Sistema de frases unificado]
date: 2026-08-17
---

# Fix ativação de voz + Sistema de frases unificado

**Fonte:** opencode+opencode

## Problemas resolvidos

### 1. Narrador falava histórico passado ao ativar voz
**Causa**: `narrador_desktop.py` lê `narrador_posicao.json` (último timestamp processado). Ao ativar voz, continuava de onde parou.
**Fix**: `cmd_voz(True)` agora chama `_resetar_posicao_narrador()` que grava `ultimo_ts = now()` em ms no `narrador_posicao.json`. Narrador passa a ler apenas mensagens **novas** a partir da ativação.

### 2. Frase fixa "Voz ativada" repetitiva
**Fix**: Pool de 8 frases base + aprendizado automático. Não repete no dia (`usadas_hoje`). Persiste em `runtime/frases_ativacao.json`.

### 3. Sem feedback de voz nas ações do widget
**Fix**: 6 ações ganharam frases variadas:
- `mic_on` / `mic_off` — microfone
- `interromper` — parar fala
- `minimizar` — esconder janela
- `topo` / `tras` — Z-order

### 4. Duplicação de lógica anti-repetição (widget vs bridge)
**Fix**: Módulo unificado `scripts/frases_manager.py`:
- `FraseManager` — classe genérica para qualquer ação
- Estado compartilha
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]