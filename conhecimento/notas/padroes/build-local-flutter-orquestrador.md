---
tags: [background, const, opencode, padrao, surface, text]
aliases: [Build local Flutter + Orquestrador]
date: 2026-08-08
---

# Build local Flutter + Orquestrador

**Fonte:** opencode

## O que aconteceu

1. Flutter 3.44.9 instalado em `C:\Users\David Jr\.flutter_auto\flutter` (extraído do zip já baixado).
2. `flutter doctor` exigia Android SDK 36 → instalado via `sdkmanager` (`platforms;android-36`, `build-tools;36.0.0`).
3. Primeiro build local falhou: **"Gradle build daemon disappeared unexpectedly"** — o `gradle.properties` padrão do Flutter usa `-Xmx8G`, mas o PC tem **3,9GB de RAM**. Corrigido para `-Xmx1536M -XX:MaxMetaspaceSize=512M -XX:ReservedCodeCacheSize=256m` + `org.gradle.workers.max=2`.
4. `flutter analyze` local achou **5 issues** que o CI nunca via: import relativo errado já corrigido, `MyApp` no teste do scaffold, deprecations (`anonKey`→`publishableKey`, `background`→`surface`), const no Text. Zero issues agora.
5. `flutter test` passando (smoke test reescrito para `StreamUmGrauApp`).
6. Build local OK (10,5min no 1º por baixar CMake; incrementais serão bem mais rápidos).
7. Instalação no Redmi: `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (assinatura dife
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]