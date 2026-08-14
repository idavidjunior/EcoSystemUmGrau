---
tags: [aplicada, cognitivo, debugging, erro, momento, reportado]
aliases: [Principio da separacao causa-efeito-temporal]
date: 2026-08-14
---

# Principio da separacao causa-efeito-temporal

**Dominio:** debugging

Em sistemas distribuidos ou assincronos, a CAUSA de um bug pode ter ocorrido muito antes do EFEITO ser observado. Nao procure perto do sintoma. Trace estados globais (logs, snapshots, checkpoints) para encontrar quando o estado correto foi violado, nao quando o erro foi reportado. Exemplo: crash no ExoPlayer 30s apos iniciar musica pode ser causado por configuracao do Equalizer que foi aplicada no momento 0.
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[debugging-em-cascata-reversa]]
- [[diagnostico-por-eliminacao-em-config-complexa]]
- [[encoding-aware-diagnostics]]
- [[hipotese-falsificacao-terminal]]