---
titulo: Analise de Jarvis opensource e aprendizados aplicaveis ao ecossistema
tipo: padrao
tags: [jarvis, voz, tts, stt, mcp, narracao, whisper, pesquisa]
data: 2026-08-29
---

# Análise de Jarvis opensource — aprendizados aplicáveis

## Contexto

O usuário pediu para buscar no GitHub projetos Jarvis opensource e avaliar o que podem ensinar ao EcoSystemUmGrau. Foram analisados três repositórios alinhados com a stack do ecossistema (Python/MCP/voz): isair/jarvis (1.7k stars), Priler/jarvis (2.9k, Rust/Tauri) e heardlabs/heard (173 stars, camada de voz para agentes de código).

## O que cada projeto faz

1. **isair/jarvis** — assistente de voz 100% offline em Python + Ollama + MCP. Inteligência de voz: wake word em qualquer posição da frase, LLM intent judge para classificação de intenção (eco, comando stop, extração de query), detecção de eco da própria fala, memória com knowledge graph, tool router com filtragem por relevância, digest passes para modelos pequenos, planner de subtarefas, dictation mode offline, filtros de alucinação do Whisper, redação automática de dados sensíveis, localização via GeoLite2 local.

2. **Priler/jarvis** — assistente offline em Rust + Tauri + Svelte. STT via Vosk, wake word via Rustpotter/Porcupine. WIP, readme desatualizado, suporta só russo. Pouco aplicável à stack Python do ecossistema.

3. **heardlabs/heard** — Apache 2.0, camada de voz para agentes de código (Claude Code, Codex). Narra com julgamento (decide o que dizer pelo contexto), três modos de escuta (Co-pilot/Companion/Focus), saliência multi-agente (um fala, outros resumidos), personas em Markdown, "catch me up" (recapitula o que o usuário perdeu), hooks fire-and-forget via Unix socket.

## Aprendizados aplicáveis ao EcoSystemUmGrau

1. **Detecção de eco do TTS** — o Jarvis ignora a própria fala comparando a transcrição ouvida com a resposta falada. O ecossistema tem bridge/STT; vale verificar se o dialogo.py já ignora o eco ao ouvir após falar.

2. **Filtros de alucinação do Whisper** — dois thresholds objetivos: `whisper_min_confidence` (dropa segmentos com confiança baixa) e `no_speech_threshold` (dropa segmento que o próprio Whisper diz não conter fala). Diretamente aplicável ao vox_audio.py/STT local para evitar transcrições fantasmas em silêncio.

3. **Narração com julgamento e modos de escuta** — Heard narra por relevância (não tudo) e tem 3 modos: Co-pilot (signposts curtos), Companion (briefings completos, olhos fora da tela), Focus (só alertas). O ecossistema já tem narração seletiva por relevância; os modos de escuta seriam evolução natural (ex.: modo Focus para quando o usuário está em reunião).

4. **Saliência multi-agente** — quando vários agentes disparam, narra o mais saliente (bloqueado/decisão/falha) e resume os outros. Aplicável ao Maestro ao coordenar o Conselho/especialistas.

5. **Catch me up** — recapitular em poucas frases o que aconteceu na janela de ausência do usuário. Aplicável ao boot/saudação: "enquanto você esteve fora: X concluído, Y rodando".

6. **Digest passes para modelos pequenos** — memória digest e tool-result digest encurtam o prompt antes de injetar em modelos pequenos (≤7B), evitando estourar o contexto. Reforça o padrão já usado no runtime_context (BM25 semântico).

7. **Redação automática de dados sensíveis** — emails, tokens e senhas são redigidos antes de gravar em disco. Reforça a cláusula de deveres externos (LGPD) — o ecossistema grava memória em disco; vale checar redação antes de persistir.

8. **Hooks fire-and-forget** — a narração nunca bloqueia o agente. O ecossistema já usa threads/async no narrador; manter esse invariante.

## Verificação

- Repositórios acessados em 2026-08-29 via GitHub (isair/jarvis, Priler/jarvis, heardlabs/heard).
- Dados de stars e features confirmados nos READMEs oficiais.

## Regra aprendida

Antes de reinventar inteligência de voz/STT, os padrões de projetos Jarvis maduros (filtros de alucinação, detecção de eco, narração por relevância, digest de contexto) cobrem a maioria das lacunas; adaptar padrões validados é mais barato que criar do zero.

## Possíveis melhorias futuras

- Adicionar filtros de alucinação (confidence/no_speech) ao STT local.
- Verificar/implementar detecção de eco no dialogo.py.
- Avaliar modos de escuta da narração (Focus) e catch me up na saudação.

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]