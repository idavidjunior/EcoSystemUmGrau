---
tipo: erro
tags: [android, gradle, ram, build, performance, xmx, tail-scale, adb]
data: 2026-08-03
fonte: tarefa
contexto: Build do projeto VoxUmGrau (Android, Kotlin/Compose) travava no gradlew assembleDebug — processo era morto pelo timeout do shell tool (>10 minutos) na etapa desugarDebugFileDependencies.
decisao: Diagnosticada falta de memória RAM (máquina com 4GB total / apenas 256MB livres) combinada com Gradle daemon configurado com -Xmx2048m, causando thrashing de memória e slowness extrema; somado a daemons órfãos de builds anteriores interrompidos. Corrigido reduzindo heap para -Xmx1024m, limitando workers a 2 e desativando parallel, além de parar daemons antes do rebuild.
impacto: Build passou de >10min (travado/morto) para 48s (BUILD SUCCESSFUL). APK versionCode 14 (name 1.0.0) instalada via ADB sobre Tailscale (100.64.71.9:5555) com sucesso. Aprendizado registrado em memory_engine #71.
---

# 2026-08-03: Build Android lento travava por falta de RAM

## Problema
O build do `VoxUmGrau` (`gradlew assembleDebug`) travava e era terminado pelo timeout do shell tool (120s / 300s / 600s) na etapa `desugarDebugFileDependencies`.

## Causa raiz
- Máquina com apenas **4 GB de RAM total** e **256 MB livres**.
- `gradle.properties` com `org.gradle.jvmargs=-Xmx2048m` (heap de 2 GB) — insuficiente headroom para a RAM disponível → **thrashing de memória**.
- **5 daemons órfãos** registrados em `~/.gradle/daemon/8.11.1` de builds anteriores interrompidos pelo `ChildProcess.kill`, alguns com tarefas parcialmente concluídas.

## Solução aplicada
Edição de `Projetos/VoxUmGrau/gradle.properties`:

```properties
org.gradle.jvmargs=-Xmx1024m -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8
org.gradle.daemon=true
org.gradle.workers.max=2
org.gradle.parallel=false
org.gradle.caching=true
```

Antes do rebuild: `gradlew.bat --stop` para limpar daemons.

## Resultado
- `clean assembleDebug`: **BUILD SUCCESSFUL in 48s** (28 tasks executadas, 8 do cache).
- APK `app-debug.apk` (versionCode **14**, versionName **1.0.0**) instalado via ADB sobre Tailscale (`100.64.71.9:5555`) → `Success`, verificado com `dumpsys package`.

## Lição
Em máquinas com pouca RAM (<8GB) e builds Android, o heap do Gradle precisa ser ajustado para a realidade física. `gradlew --stop` entre builds interrompidos evita daemons órfãos. Builds que "param" no `desugarDebugFileDependencies` com saída vazia frequentemente indicam thrash ou daemon corrompido — não necessariamente um problema do código.

## Conexoes

- [[cluster-hub-android]]