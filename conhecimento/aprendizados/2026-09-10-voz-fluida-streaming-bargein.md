---
tipo: padrao
tags: [voxumgrau, voz, streaming, sentenca, barge-in, turn-taking, stt, tts]
data: 2026-09-10
contexto: Conversa por voz do VoxUmGrau tinha dois problemas: transcrição parcial do STT encerrando o turno no meio da fala e áudio todo de uma vez (sem streaming progressivo). Sem barge-in.
decisao: Criar spec voxumgrau-voz-fluida com 3 movimentos (turn-taking no STT, streaming progressivo por sentença no TTS, barge-in). Na bridge, gerar_audio_stream usa SpeechPipeline.stream_sentencas (chunk = sentença MP3 tocável) e a resposta roda em task cancelável _responder_fala; handler {"tipo":"cancelar"} cancela a task e responde {"tipo":"cancelado"} com audio_done. No app, VoxStt separa onPartial (exibição) de onResult (envio único do turno); VoxViewModel expõe transcricaoParcial e interromperResposta; VoxAudioPlayer toca chunks em fila progressiva (cada chunk imediatamente), stop() limpa a fila; VoxWebSocket.cancelarResposta envia o cancelar.
impacto: Parcial exibido ao vivo sem enviar à bridge; áudio começa antes do fim da resposta, por sentença; usuário interrompe a fala a qualquer momento. Kotlin compila (BUILD SUCCESSFUL), testes scripts/test_voz_fluida.py passam (streaming + contrato barge-in), spec validada, preflight técnico e ético aprovados. Falta validação manual em aparelho (critérios MANUAL da spec).
