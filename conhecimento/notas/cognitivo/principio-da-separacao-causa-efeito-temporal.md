---
tags: [cognitivo, debugging]
aliases: [Principio da separacao causa-efeito-temporal]
date: 2026-07-30
---

# Principio da separacao causa-efeito-temporal

**Dominio:** debugging

Em sistemas distribuidos ou assincronos, a CAUSA de um bug pode ter ocorrido muito antes do EFEITO ser observado. Nao procure perto do sintoma. Trace estados globais (logs, snapshots, checkpoints) para encontrar quando o estado correto foi violado, nao quando o erro foi reportado. Exemplo: crash no ExoPlayer 30s apos iniciar musica pode ser causado por configuracao do Equalizer que foi aplicada no momento 0.
