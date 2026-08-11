---
tipo: erro
tags: [tts, edge-tts, ssml, ponte-de-voz, jarvis-bridge]
data: 2026-08-02
contexto: Usuário reportou que, no início das conversas, antes de falar "David", o Jarvis pronunciava caracteres que não deveriam. Investigação da saudação revelou causa na camada de TTS.
decisao: edge-tts >= 7.x removeu suporte a SSML custom. O __init__ do Communicate() aplica escape() em todo o texto, convertendo < e > em &lt; e &gt;. Assim, tags <break>, <phoneme>, <say-as> e <prosody> nunca são interpretadas como SSML — são lidas literalmente pela voz. Confirmado via WordBoundary: o motor sintetizava "Boa tarde, break time = 350ms phoneme alphabet = ipa ph = ... David".
impacto: A bridge (jarvis_bridge.py) enviava SSML via gerar_audio(). Correção: enviar TEXTO PURO ao edge-tts. Pronúncias devem usar o campo "fala" (grafia falada = substituição de texto) em pronuncias.json, nunca tags <phoneme>. Removidas as funções _ssml_enriquecer, _prosodia_frases e _escapar (código morto). test_vox.py: teste_ssml_prosodia substituído por teste_audio_sem_ssml (valida que o texto de áudio não contém < > &lt; &gt;).
proximo_passos: Monitorar se alguma outra voz/script ainda injeta tags SSML no edge-tts. Verificar vox_audio.py (usa texto puro, ok).
