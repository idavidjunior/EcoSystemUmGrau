## Objective
- Sincronizar o ecossistema (PC <-> GitHub <-> OpenCode desktop), evoluir a voz do Jarvis (TTS/STT/pronúncia), controlar totalmente a smart TV LG (SSAP+Cast), integrar monitor proativo de cotas NVIDIA, reorganizar habilidades para `mcp/`, e continuar o trabalho ativo de **widget Android** do app VoxUmGrau.
- Regra permanente: narrar/confirmar em áudio (TTS) antes/durante/depois de toda ação; feedback contínuo a cada passo; reutilizar soluções já existentes (pesquisar GitHub/web) antes de programar do zero.

## Important Details
- Repo `C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau`; branch de trabalho **`reorg/habilidades`**; default no GitHub **`opencode/mighty-meadow`** (mesmos commits).
- **Reorg `mcp/` (decisão `2026-08-04-reorg-mcp-habilidades`):** habilidades agora em `mcp/desenvolvimento/habilidades/` (30), `mcp/android/habilidades/` (4), `mcp/internet/habilidades/` (busca-web, clima-api, endereco-geo, navegacao-perita), `mcp/memoria/habilidades/` (busca-conhecimento), `mcp/comportamentais/ponytail/`, `mcp/multimidia/`, índice `mcp/manifesto_geral.json`. Geolocalização movida para `mcp/internet/habilidades/clima-api/geolocalizacao.py`.
- **Pronúncia — NOVO: usa só o campo `fala`** (não `ipa`, não `<phoneme>`). **edge-tts >= 7.x não suporta SSML custom** (escapa tags `<phoneme>/<break>/<say-as>`, lidas literalmente). Removidas: `corrigir_pronuncia()`, `_prosodia_frases()`, `_ssml_enriquecer()`. `aplicar_phonemes()` substitui pela grafia `fala` no texto do áudio (ex.: `{"fala":"Guitirrãbi"}`); a tela continua com ortografia correta; nunca deformar a escrita.
- **Autoevolução de pronúncia (02/08/2026):** usuário ensina falando — bridge `_processar_pedido_pronuncia` reconhece "pronuncie X como Y" / "fala X como Y" e grava `{"X":{"fala":"Y"}}` no `pronuncias.json` automaticamente. Guardas: palavra <= 4 palavras, fala <= 6, `palavra==fala` ignorado.
- **Prosody dinâmico DESCONTINUADO (02/08/2026):** entonação nativa do edge-tts basta (`?` ascendente, `.` descendente); pontuar via `fix_punctuation()` + `melhorar_fala()`.
- **Bridge `jarvis_bridge.py`:** WebSocket server na porta **8765**; watchdog a cada 20s; histórico `conversa_unica.json` max **500 pares**; Auth serve Basic `opencode` / `OPENCODE_SERVER_PASSWORD`; `.env` via python-dotenv. OpenCode serve doc usa **porta 8767** (health `/api/health`); base code tinha `PORTA_SERVE=8767, RESERVA=8768`.
- **Widget Android em andamento:** muitos scripts novos de diagnóstico em `scripts/`: `dbg_widget*.py`, `diag_canvas*.py`, `diag_pixel.py`, `diag_pyShot*.py`, `diag_shot.py`, `diag_state.py`, `shot_clean.ps1`/`shot_colors.ps1`/`shot_full.ps1`, `widget_grafo.py`, `gen_test_plano.py`, `check_widget_data.py`, `dbg_plano.py`, `dbg_puro.py`, `dbg_devtools.py`, `dbg_title.py` — captura de tela (screenshots) e depuração do widget do app.
- **TV LG 50UT8050PSA** (`192.168.15.6`, MAC `00:a1:59:82:bb:08`, OUI LG): services SSAP `wss://3001`, Cast `8009`, AirPlay `7000`; **porta 3000 `ws://` recusa em TVs 2024+**. Client-key `f61bccaabd247d8ae1702672d3f9c4f5` em `scripts/keys/lgtv_50UT8050PSA.json` (gitignored). Controle via `lgtv` (lgtvremote-cli): power / WoL(`00:a1:59:82:bb:08`) / volume (regra: sempre 10, nunca max) / mute / nav / inputs (HDMI 1-3) / launch (netflix, amazon) / play-pause-ff-rewind-skip / apps (147).
- Scripts adicionados: `tv_control.py`, `tv_pair_prompt.py`, `device_probe.py`, `nvidia_quota_monitor.py`.
- **NVIDIA API:** key `nvapi-...` no env; endpoint `https://integrate.api.nvidia.com/v1/chat/completions`. Modelos OK: `minimaxai/minimax-m3`, `meta/llama-3.1-8b-instruct`, `nvidia/nemotron-3-ultra-550b-a55b`. Limites (doc `conhecimento/regras-provedores.md`): **40 RPM account-wide**, **5 in-flight**, 1000 créditos free, sem API de usage, sem aumento free; famílias exigem "Try API" no build.nvidia.com; 429 incluem `Retry-After`.
- **Fallback proativo** (`config/opencode.jsonc`): plugin `@razroo/opencode-model-fallback` v0.3.2 (instalado via npm — criou `package.json`/`package-lock.json`/`node_modules/`); `retry_on_errors:[429,500,502,503,504]`, patterns `["rate limit","quota exceeded","insufficient quota","too many requests","capacity exceeded"]`, `max_fallback_attempts:5`, `cooldown_seconds:2`, `timeout_seconds:15`, `notify_on_fallback:true`, 7 fallback_models FREE: `opencode/nemotron-3-ultra-free -> deepseek-v4-flash-free -> laguna-s-2.1-free -> ling-3.0-flash-free -> mimo-v2.5-free -> north-mini-code-free -> big-pickle`.
- **Quota monitor** (`scripts/nvidia_quota_monitor.py`): token bucket 40 RPM (refill 0.667/s), concurrency cap 5, classif de erro (429=rate_limit/desconta; 502/503/504=saturação/não desconta; 500=server_error), wrapper `nvidia_request_with_quota(model, messages, **kwargs)`, CLI `status|test`, persist `scripts/nvidia_quota_state.json`. Integrado no bridge: import + handler WS `{"tipo":"quota"}`.
- **Projetos irmãos** (`conhecimento/projetos-irmaos.json`): `SupermarketCalculator` (Android, funcional v1.2), `Mp3Player` (Android, dev), `BibliaEstudoCompleta` (Android, funcional) — em `C:\Users\David Jr\Documents\Default Project\` (nível pai), criados com auxílio do eco.
- **Prime Video:** exige perfil/login manual (usuário posiciona; Jarvis controla o player) — navegação cega SSAP não funciona (lição registrada).
- **Erro app Android "Erro: servidor OpenCode não está disponível":** porta 8766 presa em socket zumbi (PID 7848 morto, recusa HTTP); **8767 responde HTTP 200** (Basic `opencode:521cf1f4-e255-461a-947c-213703b55458`) — provável migração para 8767.
- OpenCode v1.18.10 global via npm. Modelo padrão `opencode/deepseek-v4-flash-free`. Provedores: opencode (free), nvidia (configurado), deepseek, openai.
- Tailscale: `desktop-ip8nvql` 100.91.141.101 (online), `redmi-note-11` 100.64.71.9 (online), `desktop-6i6nsfs` 100.120.67.64 (offline 1d).
- Scripts de teste em `C:\Users\David Jr\AppData\Local\Temp\opencode\` (rodar `.py`, não inline PowerShell).
- Última narração TTS falhou `[400] Provider returned error` (Upstream).

## Work State
### Completed
- Sync do eco pushado; 11 repos irmãos `0 ahead/0 behind`; branches default = trabalho.
- Cláusula pétrea áudio + instrução permanente de confirmação em áudio + feedback contínuo (02/08) em `JARVIS_SYSTEM.md` + `conhecimento/aprendizados/2026-08-01-*`.
- Pronúncia: mecanismo `fala` + autoevolução `_processar_pedido_pronuncia` (02/08) implementado no bridge; `pronuncias.json`.
- Reorg `mcp/` para habilidades por domínio (39) + `manifesto_geral.json`.
- TV LG: descoberta + pairing PROMPT wss://3001 + client-key + WoL + controle total testado (power, volume 10->15, mute, nav, HDMI, apps netflix/amazon, play/ff/rewind/skip).
- Criados: `device_probe.py` (canivete suíço), `tv_pair_prompt.py`, `nvidia_quota_monitor.py`; quota integrado ao bridge (handler `{"tipo":"quota"}`).
- Fallback proativo + 7 modelos FREE no `opencode.jsonc`.
- Docs: `conhecimento/regras-provedores.md`, `conhecimento/projetos-irmaos.json`, `conhecimento/aprendizados/2026-08-01-guia-controle-tv-lg-webos.md`, `2026-08-01-controle-total-tv-lg-webos.md`.
- Últimos commits pushados: `096fe8f` (bridge+quota), `872c25d` (regras provedores), `28b073b` (cadeia fallback), `84f57d1` (fallback config), `6a3a05f` (registry irmãos), `a9cc527` (lição navegação), `d375bc0` (guia TV LG), `b0a0aa2` (TV controle total).

### Active
- **Trabalho de widget Android** (VoxUmGrau): depuração/captura de tela do widget via `dbg_widget*`, `diag_canvas*`, `diag_pixel`, `diag_pyShot*`, `shot_*`, `widget_grafo.py`, `gen_test_plano.py`.
- Erro app Android "servidor OpenCode não está disponível": usar/validar porta 8767 (8766 zumbi).
- Working tree com pendências: `M scripts/dialogo.py` (push-to-talk Espaço->**Ctrl**, `0x11`; não commitado; commit só pós-teste 100% em terminal interativo), untracked `node_modules/`, `package-lock.json`, `package.json`, `scripts/nvidia_quota_monitor.py`.

### Blocked
- Porta 8766 socket zumbi (PID 7848 morto) — Windows não libera LISTENING órfão; precisa reiniciar serve ou usar 8767.
- App Android VoxUmGrau não conecta ao bridge (sem app/celular ativo via Tailscale nesta sessão).
- Cast `play_media` no LG falha ("no session is active") -> usar SSAP play/pause do app ativo.
- Teste push-to-talk Ctrl exige terminal interativo local.
- Gmail pausado por decisão do usuário (~229 não lidos pendentes).

## Next Move
1. Validar health do serve na 8767 (HTTP 200) e resolver o socket zumbi da 8766 para destravar o app Android.
2. Commitar `scripts/nvidia_quota_monitor.py` (decidir incluir/excluir `node_modules/`, `package.json`, `package-lock.json`) e `dialogo.py` (Ctrl, só após teste 100% de ouvir voz).
3. Aplicar o wrapper `nvidia_request_with_quota` no caminho NVIDIA do `jarvis_bridge.py` (quando pedir).
4. Retomar o trabalho de widget Android (captura de tela/depuração) conforme a sessão ativa.
5. (Quando pedir) Atualizar `projetos-irmaos.json` ao abrir sessões dos projetos irmãos; retomar exclusão dos ~229 e-mails Gmail.

## Relevant Files
- `scripts/jarvis_bridge.py` — bridge 8765; `_processar_pedido_pronuncia`; import quota + handler `{"tipo":"quota"}`
- `scripts/nvidia_quota_monitor.py` — UNTRACKED; token bucket 40 RPM + concurrency 5 + classif + wrapper + CLI
- `scripts/dialogo.py` — MODIFICADO (push-to-talk Espaço->Ctrl, não commitado)
- `scripts/JARVIS_SYSTEM.md` — cláusula pétrea áudio + TV (volume 10, `192.168.15.6`) + pronúncia `fala` + reorg mcp + projetos irmãos
- `scripts/pronuncias.json` — entradas `{palavra: {fala: "..."}}`
- `scripts/keys/lgtv_50UT8050PSA.json` — client-key TV (gitignored)
- `scripts/device_probe.py`, `scripts/tv_pair_prompt.py`, `scripts/tv_control.py` — TV + canivete suíço
- `config/opencode.jsonc` — fallback `@razroo/opencode-model-fallback` + 7 modelos FREE
- `mcp/` — reorg habilidades por domínio + `manifesto_geral.json`; `mcp/internet/habilidades/clima-api/geolocalizacao.py`
- `conhecimento/regras-provedores.md`, `conhecimento/projetos-irmaos.json`, `conhecimento/aprendizados/2026-08-01-guia-controle-tv-lg-webos.md`
- `scripts/vox_audio.py` — TTS `falar` + STT `ouvir`; última chamada falhou `[400]`