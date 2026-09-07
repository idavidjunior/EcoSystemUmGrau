---
tags: [assinado, chave, fonte, opencode, padrao, ram]
aliases: [CI de Android em máquina fraca + keystore estável]
date: 2026-08-23
---

# CI de Android em máquina fraca + keystore estável

**Fonte:** opencode

---
tipo: padrao
tags: [ci, android, gradle, assinatura, gate, mp3player]
data: 2026-08-23
contexto: Build do Mp3Player impossível no PC local (4GB RAM); deploy ao celular exigia APK assinado com a mesma chave.
decisao: |
  1. CI no GitHub Actions (.github/workflows/build.yml) constrói o APK: ubuntu
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]