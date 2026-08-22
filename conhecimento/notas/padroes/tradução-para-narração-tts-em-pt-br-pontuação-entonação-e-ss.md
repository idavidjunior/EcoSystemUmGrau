---
tags: [emojis, joão, padrao, remova, símbolos, traducao-audio]
aliases: [Tradução para narração TTS em pt-BR: pontuação, entonação e ]
date: 2026-08-22
---

# Tradução para narração TTS em pt-BR: pontuação, entonação e SSML

**Fonte:** traducao-audio

O texto traduzido para TTS é escrito para a voz, não para o olho. O TTS lê pontuação como prosódia: ponto final gera pausa e queda de entonação; vírgula, micro-pausa; interrogação sobe a curva melódica. Pontuação pobre = voz robótica.

Escreva números por extenso ('R$ 25,50' vira 'vinte e cinco reais e cinquenta centavos'), evite abreviações e remova símbolos e emojis. SSML dá controle fino: <break time="500ms"/> para pausas, <prosody rate="90%"> para desacelerar e <phoneme> para corrigir nomes que o TTS erra, como 'João' (/ʒuˈɐ̃w/).

Para narração (voz over), use cerca de 150 palavras por minuto: 1 minuto de vídeo = ~150 palavras.

Armadilha: copiar siglas e números do original ('2º' lido errado como 'segundo grau'). Adapte tudo para texto limpo que o sintetizador leia corretamente.
## Conexoes

- [[cluster-hub-traducao]]
- [[dublagem-versão-sincronização-labial-tamanho-da-fala-e-natur]]
- [[legendagem-limite-de-caracteres-tempo-em-tela-e-leitura-rápi]]
- [[padrao-hub-padroes]]
- [[pipeline-de-tradução-de-áudio-stt-tradução-tts]]
- [[tradução-de-fala-coloquial-e-falas-sobrepostas-em-podcasts-e]]