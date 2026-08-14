---
tags: [padrao, perde, robótico, soa, traducao-audio, vira]
aliases: [Pipeline de tradução de áudio: STT -> tradução -> TTS]
date: 2026-08-14
---

# Pipeline de tradução de áudio: STT -> tradução -> TTS

**Fonte:** traducao-audio

Pipeline de tradução de áudio em três estágios: transcrição automática (STT), que gera texto com timestamps; tradução para o idioma-alvo preservando sentido e tom; e síntese de voz (TTS), que gera o áudio respeitando pontuação e pausas.

Em pt-BR, use STT treinado em português brasileiro: reconhecedores genéricos erram 'a gente vai' (lido como 'agente') e 'mais'/'mas'. Whisper e Google Cloud STT têm boa precisão para pt-BR.

Erro comum: isolar os estágios. Tradução literal mata expressões idiomáticas ('chutar o balde' vira texto sem sentido) e o TTS soa robótico quando a pontuação se perde. Preserve timestamps e quebras de frase entre etapas e pontue a tradução para guiar as pausas do TTS.

Armadilha: medir qualidade só pelo STT. O gargalo está na tradução e na prosódia.
## Conexoes

- [[cluster-hub-traducao]]
- [[dublagem-versão-sincronização-labial-tamanho-da-fala-e-natur]]
- [[legendagem-limite-de-caracteres-tempo-em-tela-e-leitura-rápi]]
- [[padrao-hub-padroes]]
- [[tradução-de-fala-coloquial-e-falas-sobrepostas-em-podcasts-e]]
- [[tradução-para-narração-tts-em-pt-br-pontuação-entonação-e-ss]]