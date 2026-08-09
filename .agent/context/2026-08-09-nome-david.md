---
tipo: decisao
tags: [pronuncia, nome, david, deivid, usuario, tts]
data: 2026-08-09
contexto: ecosistema-opencode
decisao: Nome do usuario e David (escreve-se David, pronuncia-se Deivid)
impacto: Alta - Jarvis deve pronunciar corretamente em saudacoes e respostas
---

# Nome do Usuário: David

## Pronúncia Correta
- **Nome escrito:** David
- **Pronúncia:** Deivid (como em inglês, som de "ei")
- **Errado:** Davi, Dávid (que são nomes diferentes)

## Contexto
O usuário se chama David. O Jarvis (assistente de voz) deve pronunciar o nome corretamente em todas as saudações, respostas e menções. A grafia é "David" mas a fala é "Deivid".

## Implementação
- `scripts/pronuncias.json` — entrada `"david": {"fala": "Deivid"}`
- `scripts/jarvis_bridge.py` — sistema prompt instrui pronúncia "Deivid"
- `ler-runtime/knowledge/knowledge_graph.json` — pattern `pronuncia_nome_usuario`

## Observação TTS
O edge-tts com voz `pt-BR-AntonioNeural` deve receber "Deivid" para pronunciar corretamente.
