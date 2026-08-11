---
tipo: padrao
tags: [flutter, build-local, gradle, android, orquestrador, streamumgrau]
data: 2026-08-08
contexto: Ciclo de build do StreamUmGrau migrado do GitHub Actions (primário) para o PC local (primário), com CI como rede de segurança.
decisao: Instalar Flutter 3.44.9 local (mesma versão do CI), ajustar gradle.properties para a RAM da máquina (4GB → -Xmx1536M), usar flutter analyze+test como gate antes de qualquer push, versionar o scaffold android/ e criar o agente 13-flutter-orquestrador.
impacto: Build local ~1-2min incremental (vs ~7,5min no CI); erros que o CI não pegava (import relativo errado, teste MyApp) agora são capturados por flutter analyze local; CI simplificado (sem scaffold/rename frágil).
---

# Build local Flutter + Orquestrador

## O que aconteceu

1. Flutter 3.44.9 instalado em `C:\Users\David Jr\.flutter_auto\flutter` (extraído do zip já baixado).
2. `flutter doctor` exigia Android SDK 36 → instalado via `sdkmanager` (`platforms;android-36`, `build-tools;36.0.0`).
3. Primeiro build local falhou: **"Gradle build daemon disappeared unexpectedly"** — o `gradle.properties` padrão do Flutter usa `-Xmx8G`, mas o PC tem **3,9GB de RAM**. Corrigido para `-Xmx1536M -XX:MaxMetaspaceSize=512M -XX:ReservedCodeCacheSize=256m` + `org.gradle.workers.max=2`.
4. `flutter analyze` local achou **5 issues** que o CI nunca via: import relativo errado já corrigido, `MyApp` no teste do scaffold, deprecations (`anonKey`→`publishableKey`, `background`→`surface`), const no Text. Zero issues agora.
5. `flutter test` passando (smoke test reescrito para `StreamUmGrauApp`).
6. Build local OK (10,5min no 1º por baixar CMake; incrementais serão bem mais rápidos).
7. Instalação no Redmi: `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (assinatura diferente do APK do GitHub) → desinstalar primeiro; depois `INSTALL_FAILED_USER_RESTRICTED` → usuário confirmou popup da MIUI.
8. App rodando: PID 2504, `mCurrentFocus=com.umgrau.stream/.MainActivity`, sem FATAL EXCEPTION.

## Decisões consolidadas

- **Caminho primário de build = PC local**; GitHub Actions = rede de segurança.
- **`android/` versionado** (com `gradle.properties` ajustado e package `com.umgrau.stream`) → CI não regenera scaffold nem renomeia mais. O workflow agora só faz `pub get` + `analyze` + `test` + `build apk`.
- **Fonte única do rename de package**: `scripts/rename_flutter_package.sh` (com `OLD_PKG` usando pontos, não barras — lição do erro `ClassNotFoundException`).
- **Gate obrigatório antes de push**: `flutter analyze` (zero issues) + `flutter test`.
- **Novo agente**: `config/agents/13-flutter-orquestrador.md` (build/empacotamento/instalação; não escreve código de negócio).

## Caminhos úteis

- Flutter local: `C:\Users\David Jr\.flutter_auto\flutter\bin\flutter.bat`
- Android SDK: `C:\Users\David Jr\AppData\Local\Android\Sdk` (`ANDROID_HOME` já setado)
- Script rename: `scripts/rename_flutter_package.sh <dir_projeto>`
- ADB wireless: `adb connect 100.64.71.9:5555` → `adb install -r -t <apk>`

## Conexoes

- [[cluster-hub-programacao]]