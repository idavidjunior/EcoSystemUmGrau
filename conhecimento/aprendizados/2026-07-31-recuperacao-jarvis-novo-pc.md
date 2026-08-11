# 2026-07-31 - Recuperação do Jarvis no novo PC

## Contexto
- Nova máquina (`C:\Users\David Jr\Documents\Default Project`), antiga era `C:\Users\Playtec-bancada\Desktop\Codigos`.
- Jarvis parado: sem Python, Node, opencode, ADB, Tailscale; configs apontando para a máquina antiga.

## O que foi feito
- Instalados: Python 3.12 (winget), Node.js LTS 24, opencode 1.18.10 (npm), JDK 17 Temurin, Android SDK (build-tools;35.0.0, platforms;android-35), ADB, Tailscale.
- Configurados: Tailscale (PC `100.91.141.101`, celular `100.64.71.9`), ADB USB + WiFi (`192.168.15.4:5555`), GitHub autenticado.
- Atualizados paths em `jarvis_bridge.py`, `run_bridge.py`, `run_serve.py`, `opencode-serve.jsonc`, `JARVIS_SYSTEM.md` (máquina antiga → nova).
- App VoxUmGrau: host atualizado para `100.91.141.101`, recompilado e instalado no celular.

## Aprendizados técnicos (importantes)
1. **edge-tts >= 7.x removeu o argumento `ssml`**: `Communicate(text, voice, ssml=True)` falha. Na 7.2.8 o texto SEMPRE passa por `escape()` (tags `<` viram `&lt;`) e o SSML é montado internamente via `mkssml`. Injetar `<phoneme>` inline no texto NÃO funciona mais — as tags são lidas literalmente (áudio com "caracteres no meio"). **Solução:** enviar texto puro; a voz nativa (pt-BR) pronuncia tudo corretamente.
2. **`opencode serve` na 1.18.10 não aceita `--dir` nem `-c`**: flags removidas. Usar `cwd=WORKDIR` no subprocess e config global (`~/.config/opencode/opencode.jsonc`) com `instructions`.
3. **`local.properties` do Gradle falha com BOM (EF BB BF)**: escrever com `[IO.File]::WriteAllText` e UTF8 sem BOM, e usar `sdk.dir=C:/...` (forward slashes).
4. **`build.ps1` requer `powershell -ExecutionPolicy Bypass -File`** quando a policy bloqueia scripts.
5. **ADB downgrade/assinatura**: versão instalada no celular (code 9) era mais nova e assinada com outra keystore; `adb install -r -d` falha por assinatura → desinstalar e reinstalar.
6. **`adb kill-server` pode derrubar o shell que o executa** — rodar separado.
7. **Caminhos hardcoded de outra máquina** quebram silenciosamente (bridge_log, SYS_PATH, PRON_PATH, WORKDIR). Usar `Path(__file__).parent` quando possível.

## Próximos passos
- Adicionar `OPENWEATHER_API_KEY` ao `.env` para o clima voltar a funcionar (hoje é omitido da saudação para não vazar texto técnico).
- Revisar demais scripts do ecossistema com paths antigos (`bootstrap.ps1`, `vigilante.ps1`, `watchdog.ps1`, `config/opencode.jsonc`, `estado_atual.md`).

## Conexoes

- [[cluster-hub-programacao]]