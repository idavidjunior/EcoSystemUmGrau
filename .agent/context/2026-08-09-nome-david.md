---
tipo: decisao
tags: [pronuncia, nome, david, usuario, tts]
data: 2026-08-09
contexto: ecosistema-opencode
decisao: Nome do usuario e David (pronuncia Dávid, com acento na primeira silaba)
impacto: Alta - Jarvis deve pronunciar corretamente em saudacoes e respostas
---

# Nome do Usuário: David

## Pronúncia Correta
- **Nome:** David
- **Pronúncia:** Dávid (com acento tônico na primeira sílaba, como em inglês)
- **Errado:** Davi (que é um nome diferente, "Dá-vi")

## Contexto
O usuário se chama David. O Jarvis (assistente de voz) deve pronunciar o nome corretamente em todas as saudações, respostas e menções.

## Implementação
- `scripts/pronuncias.json` — entrada `"david": {"fala": "Dávid"}`
- `scripts/jarvis_bridge.py` — sistema prompt menciona "usuário David"
- `ler-runtime/knowledge/knowledge_graph.json` — pattern `pronuncia_nome_usuario`

## Observação TTS
O edge-tts com voz `pt-BR-AntonioNeural` pode ter dificuldade com nomes próprios em inglês. Se necessário, usar "Dávid" (com acento) para forçar a pronúncia correta na sílaba tônica.
