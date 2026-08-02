---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente), exclamacao (!)=pitch+8%/rate+6%, afirmacao sem prosody. (2) _processar_pedido_pronuncia() + _registrar_pronuncia(): usuario ensina pronuncia falando ("pronuncie GitHub como Guitirrãbi"), bridge grava {"palavra":{"fala":...}} em pronuncias.json e confirma em audio. Guarda anti-falso-positivo: alvo<=4 palavras, fala<=6, palavra==fala ignorado.
impacto: Voz do Jarvis ganhou entoacao por tipo de frase (perguntas sobem) e o usuario pode corrigir pronuncia em tempo real pela fala, sem editar JSON. test_vox: prosody 6/6, pronuncia 8/8 OK. preflight ALL PASS. Audio real gerado OK (57KB base64). pronuncias.json restaurado apos teste de registro.
detalhe: Falso positivo "fala o que você vai fazer como amanhã" nao casa por causa do guard de <=4 palavras no alvo (pega "o que você vai fazer" = 5). Registrar com lock simples (retry 3x) para nao corromper com geracao de audio paralela.
