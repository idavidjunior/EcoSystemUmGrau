---
tags: [geolite2, local, localização, opencodeopencode, padrao, sensíveis]
aliases: [Análise de Jarvis opensource — aprendizados aplicáveis]
date: 2026-08-30
---

# Análise de Jarvis opensource — aprendizados aplicáveis

**Fonte:** opencode+opencode

## Contexto

O usuário pediu para buscar no GitHub projetos Jarvis opensource e avaliar o que podem ensinar ao EcoSystemUmGrau. Foram analisados três repositórios alinhados com a stack do ecossistema (Python/MCP/voz): isair/jarvis (1.7k stars), Priler/jarvis (2.9k, Rust/Tauri) e heardlabs/heard (173 stars, camada de voz para agentes de código).

## O que cada projeto faz

1. **isair/jarvis** — assistente de voz 100% offline em Python + Ollama + MCP. Inteligência de voz: wake word em qualquer posição da frase, LLM intent judge para classificação de intenção (eco, comando stop, extração de query), detecção de eco da própria fala, memória com knowledge graph, tool router com filtragem por relevância, digest passes para modelos pequenos, planner de subtarefas, dictation mode offline, filtros de alucinação do Whisper, redação automática de dados sensíveis, localização via GeoLite2 local.

2. **Priler/jarvis** — assistente offline em Rust + Tauri + Svelte. STT via Vosk, wake word via Rustpot
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]