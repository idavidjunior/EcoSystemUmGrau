---
titulo: Fix TTS service duplicado causava audio engasgando
tipo: decisao
tags: [tts, audio-engasgando, cooldown, singleton]
data: 2026-08-31
status: RASCUNHO
resumo: |
  Áudio do narrador repetia 2-3x a mesma frase. Causa: system_guardian
  acordava tts_service.py sem cooldown nem singleton check, gerando 2-3
  processos que liam o mesmo comando e tocavam MP3 em paralelo.
contexto: |
  Log provou: 'fala req=A: Beleza chequei tudo' seguido de 'fala req=B:
  Beleza chequei tudo' com request_ids diferentes = audio duplicado.
decisao: |
  3 proteções em start_tts_service: (1) cooldown 15s entre restarts do
  mesmo script via _ULTIMO_RESTART; (2) is_tts_service_up() antes de
  Popen; (3) pid_file só é escrito após confirmar (a) processo vivo E
  (b) serviço gravou pid_file com seu próprio PID (se gravou outro,
  significa que detectou outro vivo e saiu pelo singleton dele).
testes_pendentes:
  - Esperar reinício natural do tts_service e confirmar que nasce só 1
  - Forçar reinício (matar processo) e confirmar cooldown bloqueia 2ª tentativa
  - Auditar log do tts_service.log: fala req com IDs únicos
arquivos_alterados:
  - scripts/system_guardian.py
