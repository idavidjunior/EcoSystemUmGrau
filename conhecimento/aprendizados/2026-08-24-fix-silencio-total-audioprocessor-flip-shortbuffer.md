---
tipo: erro
tags: [audio, exoplayer, audioprocessor, bytebuffer, dsp, mp3player, ci, adb]
data: 2026-08-24
contexto: Mp3Player portado para DSP próprio (EqualizerAudioProcessor como AudioProcessor do Media3 1.2.1). App tocava "sem som": decodificador consumia MP3 normalmente, AudioTrack ficava STATE_ACTIVE mas com playbackTime de ~13ms após 14s (faminto), silêncio total.
---

# Sintoma
ExoPlayer + processador de áudio custom: decoder saudável, AudioTrack ativo, zero áudio. Logs EqDbg mostravam `qIn` consumindo bytes e `getOut got=0` eternamente.

# Causa raiz
Em `queueInput`, a conversão float→int16 escrevia via **ShortBuffer-view** (`cachedOutBuf.asShortBuffer().put(...)`). A view tem position/limit PRÓPRIOS e **não move o position do ByteBuffer pai**. Depois, `cachedOutBuf.flip()` usava o position do pai (ainda 0) para definir o limit → `limit=0`, `remaining()=0`. Todo output saía vazio. O caminho bypass não sofria porque usa `put(ByteBuffer)` direto no pai.

# Correção
Substituir `flip()` por reposicionamento manual:
```kotlin
cachedOutBuf.clear()
cachedOutBuf.limit(outBytes)
// ... escrita via view ...
cachedOutBuf.position(0)   // pronto para leitura; limit já correto
outputBuffer = cachedOutBuf
```
Commit 7f7ab03.

# Lições
1. **ByteBuffer view ≠ pai**: escrita por `asShortBuffer()` não adianta o ponteiro do buffer original. `flip()` no pai após escrever pela view = armadilha clássica.
2. **Instrumentação remota vence teoria**: logs `qIn rem / ACTIVE done outRem esperado / getOut got` localizaram o ponto exato em UM ciclo CI (~4 min build GitHub Actions + install USB + logcat). Sem isso, seriam horas de adivinhação.
3. **Pipeline de depuração Android sem Gradle local** (máquina fraca): commit código → gate → CI verde → `gh run download` → `adb install -r` (assinatura estável desde que debug.keystore versionado + signingConfig explícito em app/build.gradle.kts) → uiautomator dump para tocar na UI por coordenadas → logcat filtrado.
4. `install -r` pode falhar silenciosamente (saída engolida): sempre confirmar `dumpsys package | lastUpdateTime`.

## Conexoes

- [[album-art-download-com-redirect-loop-manual-instancefollowre]]
- [[audioprocessorisactive-must-be-dynamic]]
- [[filename-artist-extraction-two-strategies]]
- [[itunes-search-with-scoring-thresholds]]
- [[metadata-busca-em-multi-fontes-acoustid-itunes-br-musicbrain]]
- [[renderersfactory-for-custom-audioprocessor]]
- [[searchmodenormal-relaxed-auto-fallback-se-normal-retorna-nul]]