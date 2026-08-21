---
tags: [chega, cognitivo, conhecimento, fala, general, vivo]
aliases: [# Aprendizado — 2026-07-31 — Pontuação automática de transcr]
date: 2026-08-21
---

# # Aprendizado — 2026-07-31 — Pontuação automática de transcrições de voz (Jarvis)

**Dominio:** general

# Aprendizado — 2026-07-31 — Pontuação automática de transcrições de voz (Jarvis)

## Contexto
- O Android STT (SpeechRecognizer) devolve texto corrido, sem pontuação e **sem prosódia** (a melodia da fala não chega à bridge). O usuário pediu: `?` em perguntas, pontuação correta e **primeira letra maiúscula** sempre.
- Já existia `fix_punctuation()` básico; a reivisão ampliou regras e corrigiu um bug de acentuação.

## O que foi feito (`scripts/jarvis_bridge.py`)
1. **Clas

# Aprendizado — 2026-07-31 — Reorg: catálogo único Habilidades/ + caminhos novos

## Contexto
- Skills estavam espalhadas em `skills/` e `scripts/` (clima, busca), e o array `plugin` do opencode.jsonc apontava para `plugins/ponytail` (inexistente — Cláusula Pétrea). Decisão `2026-07-31-habilidades-catalogo-unico-jarvis.md`: Habilidades = ações executáveis; Agentes = tomadores de decisão (não mexer).

## O que foi feito
1. **`Habilidades/`** — catálogo único, 38 habilidades:


# Política de Resposta Rápida — caminhos rápidos constantes no Jarvis

- **Data:** 01/08/2026
- **Sessão:** Ensino permanente de caminhos de resposta rápida + otimização de latência

## Pedido do usuário
"Ensine o Jarvis a SEMPRE procurar caminhos de rápida resposta nas conexões e
caminhos de conexão mais rápidas para respostas mais rápidas. Isso deve ser
constante."

## O que foi feito

### 1. Política permanente no prompt (JARVIS_SYSTEM.md)
Nova seção logo após "Identidade

# Pontuação da transcrição voltando ao balão do app (corrigido)

- **Data:** 01/08/2026
- **Sessão:** Bug — "Que horas são" transcrito sem o sinal "?"

## Problema
O usuário perguntou "Que horas são" e o balão da transcrição no app não mostrava
o "?". A pontuação JÁ era aplicada pela bridge (`fix_punctuation`), mas o app
exibia a transcrição crua do STT — a correção nunca voltava para a tela.

## Causa raiz
- App (`VoxViewModel.onSttResult`): `mensagens + Mensagem(texto,

---
tipo: aprendizado
tags: [jarvis-bridge, voz, widget, grafo, pywebview, comando-voz, cerebro-vivo]
data: 2026-08-04
contexto: Usuario pediu o 'foco vocal via Jarvis' — comando de voz orienta o grafo do conhecimento (cerebro vivo). Bridge Jarvis roda na porta 8765 (processo separado) e o widget do grafo (pywebview) e outro processo; sem API entre eles.
decisao: Usar o filesystem como canal entre processos (o widget ja vigia arquivos do vault). (1) jarvis_bridge._comando_grafo(t) em caminho_rap
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]