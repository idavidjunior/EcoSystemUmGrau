---
tipo: padrao
tags: [ci, android, gradle, assinatura, gate, mp3player]
data: 2026-08-23
contexto: Build do Mp3Player impossível no PC local (4GB RAM); deploy ao celular exigia APK assinado com a mesma chave.
decisao: |
  1. CI no GitHub Actions (.github/workflows/build.yml) constrói o APK: ubuntu-latest,
     JDK 17 temurin, gradle assembleDebug, upload de artifact. Push em app/** dispara.
  2. Secret ANDROID_DEBUG_KEYSTORE (debug.keystore em base64) é restaurado para
     ~/.android/debug.keystore no runner — o Gradle assina igual à máquina local e o
     adb install -r funciona sem desinstalar (exceto na PRIMEIRA troca de origem).
  3. Gate de persistência: Get-RepoPath agora resolve nomes simples contra Projetos\
     antes do fallback silencioso para o repo raiz (bug de commit cruzado corrigido).
impacto: |
  Builds Android não dependem mais da RAM local; Regra de Ouro (build + deploy +
  GitHub) viabilizada nesta máquina. Commit via gate com -Repo <Nome> confiável.
  Pendências conhecidas: debounce do gate retém mudanças só-de-YAML até 30min;
  primeira instalação pós-CI exige adb uninstall (assinatura antiga no aparelho).
---

# CI de Android em máquina fraca + keystore estável

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
   pushado — conteúdo legítimo pendente, mensagem enganosa; histórico preservado,
   sem force-push). Correção: resolver `$projectsDir\$Key` antes do fallback.
2. **EffectsChain.kt não compilava**: faltava `import kotlin.math.pow`
   (o erro "Overload resolution ambiguity" na linha seguinte era cascata do tipo
   quebrado — um import resolveu os dois).
3. **Debounce do gate**: arquivos .yml são classificados como estado "vivo", não
   código; commits só-de-workflow esperam até 30min (ultimo_auto_commit).

## Evidência
CI verde run 32681780441 (3m37s) após correção do import; APK 11.355.303 bytes;
commits 31ea42e e ccdd704 no master do Mp3Player via gate.
