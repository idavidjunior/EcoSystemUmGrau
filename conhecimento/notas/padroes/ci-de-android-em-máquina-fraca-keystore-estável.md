---
tags: [dir, gradle, jvm, opencode, padrao, qualquer]
aliases: [CI de Android em máquina fraca + keystore estável]
date: 2026-08-23
---

# CI de Android em máquina fraca + keystore estável

**Fonte:** opencode

## Problema real
O PC (3,9GB RAM, OpenCode desktop ocupando ~1GB) mata qualquer JVM do Gradle:
"daemon disappeared" sem hs_err, sem OOM no log, mesmo com -Xmx768m e --no-daemon.
Build local inviável durante uso normal do ecossistema.

## Solução adotada
Workflow mínimo no próprio repositório do app (não no ecossistema):

```yaml
- Restore debug keystore: echo "$KEYSTORE_B64" | base64 -d > ~/.android/debug.keystore
- ./gradlew assembleDebug --no-daemon
- actions/upload-artifact com o APK
```

Download e install:
```
gh run download <run-id> -R idavidjunior/Mp3Player -n mp3player-debug-apk -D dir
adb uninstall com.mp3player.debug   # apenas na primeira troca de assinatura
adb install -r app-debug.apk
```

## Bugs encontrados no caminho
1. **Gate commitava no repo errado**: `-Repo Mp3Player` caía no `return $ecoDir`
   porque Test-Path('Mp3Player') falhava fora de Projetos\. O commit manual foi
   parar no EcoSystemUmGrau com mensagem do Mp3Player (commit 568d479f, já
   pushado — conteúd
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]