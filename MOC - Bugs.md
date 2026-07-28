# Mapa de Conteúdo — Bugs Corrigidos

## Mp3Player (Player + Metadata)

| Bug | Causa | Correção |
|-----|-------|----------|
| Audio stops / EQ not audible | `queueInput()` sem `position(limit())` + `isActive()` não dinâmico | position(limit) + isActive=true com flag interna |
| Preset não persiste entre sessões | Preamp baked nos gains | `currentGains[]` RAW separado de `currentPreamp` |
| Preamp volume irreversível e cumulativo | `showVolumeDialog()` somava em gains já baked | Preamp separado, `showVolumeDialog` só atualiza preamp |
| Preamp inaudível | `syncSoftwareEq()` passava preamp=0 | Agora passa `currentPreamp` |
| EQ distorce em boost alto | `coerceIn(-1f, 1f)` causa hard clipping | `Math.tanh(sample)` soft-clipping |
| Preset corrompido em pt_BR | `",".format()` produz vírgula decimal | Separador `\n` |
| EQ distorce ainda em boost alto | tanh sozinho insuficiente | Peak limiter + attack/release smoothing |
| EQ só aplica após abrir fragment | Gains nunca carregados no processor até fragment abrir | `EqStateLoader.restoreTo()` chamado em `playSongFromList()` |
| EQ desativa ao trocar música | `AudioProcessor.reset()` setava `isActiveState=false` | `updateActiveState()` recalculado em `configure()`/`reset()` |
| Duplicate mini-player | `openNowPlaying()` chamado múltiplas vezes | Guard: if backstack top is "now_playing", return |
| Artist "Desconhecido" | YouTube MP3 sem ID3 | Extrair artist do filename |
| Search retorna artista errado | iTunes BR resultados irrelevantes | Scoring thresholds NORMAL/RELAXED |
| Album art não encontrado | Cover Art Archive redirect loop | Loop explícito + iTunes US fallback |
| Logs não aparecem | MIUI logcat filtering | Toast como feedback visual |
| AcoustID sempre falha | API key inválida | Aceito como não-crítico, fallback automático |
| Nenhuma música mais tocada | Sem mecanismo de contagem | `PlayCountManager` + SortMode.PLAY_COUNT |
| Botões de filtro sem texto visível | MaterialButton corrompe background | TextView > Button |

## LER (Engine)

| Bug | Causa | Correção |
|-----|-------|----------|
| Hard stop por max_iterations | Loop usava `iteration<100` como critério | Detecção de estagnação (30 sem progresso) |
| Score<threshold mas ia para SUCCESS | `_phase_success_eval` ignorava score | Score<threshold → REPLANNING |
| Executor não validava resultado real | Retornava string fixa sem verificar git diff | Verifica `git diff --stat` + `git status` |
| Sem feedback loop do usuário | COMPLETED → `_finalize` direto | `_ask_user_feedback()` adicionado |
| Persistência sem atomicidade | `json.dump` direto sem tmp | `atomic_write_json()` com tmp+os.replace |
| Logs sem rotação | Sempre no mesmo arquivo | `_rotate_log()` em 5 níveis ao atingir 512KB |
| Memória crescia indefinidamente | `results` dict sem limite | MAX_RESULTS=50 |
| Code duplication checkpoint/persistence | 200 linhas duplicadas | Unificado via `atomic_write_json/read_json` |

## Infraestrutura

| Bug | Causa | Correção |
|-----|-------|----------|
| OpenCode Go provider crash | `messages[-1]` tratado como dict, mas pode ser string | `isinstance(last, dict)` check |
| MCP server não respondia | Faltava handler `initialize` | `_handle_initialize()` adicionado |
| auth.json com chaves NVIDIA disfarçadas | Entradas nvapi-... mascaradas | Removidas entradas inválidas |
| MCP server Failed to get tools | Server respondia a notifications | `handle_request()` retorna None se req_id=None |
| MCP server não respondia tools/call | Method não no dispatch | Adicionado `_handle_tools_call()` |

---
\`\`\`dataview
TABLE file.cday as "Data"
FROM "conhecimento/aprendizados"
WHERE contains(file.name, "fix") OR contains(file.name, "correcao")
SORT file.cday DESC
\`\`\`
