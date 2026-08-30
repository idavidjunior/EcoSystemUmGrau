---
tipo: padrao
tags: [cerebro-vivo, neurociencia, fala, areas-cerebrais, metafora, frontend]
data: 2026-08-30
contexto: O usuário pediu que o Cérebro Vivo mostrasse em tempo real as "áreas" que se ativam quando o Eco fala, inspirado no cérebro humano. Pesquisei a neurociência da produção da fala para fundamentar a metáfora.
decisao: Mapeei as áreas funcionais da fala no grafo de conhecimento e as acendo em cascata quando o Eco fala. Fonte: produção de fala envolve áreas do hemisfério esquerdo e um modelo de 3 estágios (conceitualização -> formulação -> articulação), com áreas específicas para cada etapa.
impacto: Visual mais fiel ao cérebro: quando o Eco fala, os neurônios de cada área funcional se acendem em sequência, e o usuário pode filtrar pelo Foco "Fala" para ver os 45 neurônios de fala.
---

# Neurociência da fala aplicada ao Cérebro Vivo

## O que a neurociência diz (pesquisa)

A produção da fala não é um único "botão", mas uma rede de áreas que se ativam em sequência no hemisfério esquerdo (em destros):

1. **Conceitualização** — a intenção e a seleção dos conceitos que serão ditos.
2. **Formulação** — codificação gramatical (seleção de palavras/lemma e sintaxe), codificação morfo-fonológica (quebra em sílabas) e codificação fonética (gestos articulatórios).
3. **Articulação** — execução motora pelo aparelho vocal (pulmões, laringe, língua, lábios, mandíbula).

Áreas-chave envolvidas (modelo de Levelt + anatomia):
- **Área de Broca** (giro frontal inferior esquerdo): planejamento e produção gramatical.
- **Área de Wernicke** (lobo temporal superior): compreensão da linguagem.
- **Córtex motor primário** (giro pré-central): comanda a articulação (músculos vocais).
- **Área motora suplementar (AMS)**: iniciação e sequenciamento da fala.
- **Ínsula esquerda**: coordenação articulatória.
- **Cerebelo**: sequencia sílabas em palavras rápidas, suaves e rítmicas.
- **Gânglios da base**: controle motor automático.
- **Lobo temporal**: memória semântica e de linguagem.

## Como foi aplicado ao Cérebro Vivo

O grafo não tem anatomia, então agrupei os neurônios em **áreas funcionais** por palavras-chave nos rótulos:

- `conceito` (conceitualização): planeja, conceito, ideia, missao, estrategia...
- `formula` (Broca/gramática): gramatica, sintaxe, estrutura, padrao, codigo, linguagem...
- `fonema` (codificação fonológica): fono, silaba, palavra, som, semantica, lexico...
- `motor` (articulação): voz, tts, audio, fala, speech, microfone, articulacao...
- `compreende` (Wernicke/compreensão): compreens, entend, leitura, contexto, interpretacao...

Quando o Eco fala (`ECO_FALANDO`), o grafo percorre as áreas em sequência (a cada ~720 ms) e acende alguns neurônios de cada área com a cor dela, imitando o impulso conceitualização → formulação → fonologia → articulação → compreensão.

## Aprendizados
- Metáfora biológica agrega significado e beleza ao widget, e dá um vocabulário comum ("áreas de fala").
- Contagens no payload real: conceito 11, formula 26, fonema 5, motor 44, compreende 6; Foco "Fala" mostra 45 neurônios.
- A cascata usa `disparoNeural` (reaproveitado) com cor por área, mantendo consistência visual.

## Conexoes

- [[pronúncia-járvis-escrita-sem-acento-fala-com-acento]]