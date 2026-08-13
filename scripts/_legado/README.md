# _legado — Scripts órfãos

Scripts e artefatos sem referência externa (0 usos reais) no momento da triagem de
2026-08-13. Movidos aqui para tirá-los do radar do boot/preflight mantendo-os
recuperáveis. Nada aqui é carregado pelo runtime.

## Motivos da movimentação

| Arquivo | Motivo |
|---|---|
| test_cache2.py, test_final.py, test_jarvis.py, test_latency.py, test_mci.py, test_serve.py | Testes únicos superados por test_vox.py / test_widget_live.py |
| debug_widget.py, modificar_widget.py | Sem docstring, sem uso |
| mcp_benchmark.py | Sem docstring, sem uso |
| create_skill_vault_map.py | Sem docstring, sem uso |
| clean_sessions.py | Sem docstring, sem uso |
| criar_atalho.py | Sem docstring, sem uso |
| scan_connections.py | Docstring diz "será chamado pelo bootloader", mas runtime_boot.py nunca o importa/chama (intenção antiga nunca implementada) |
| controle.vbs | Nenhuma referência (nem controle.bat usa) |
| start_widget.bat | Atalho real aponta para grafico_widget.bat |
| hotkey_pause.py, hotkey_pause_win32.py | Duplicados entre si, sem uso |
| preditor_uso.py, previsor_gargalos.py + JSONs | Duplicados entre si, sem uso real |
| jarvis_voice_cmd.py + log | Só self-referência, sem uso |
| scan_log.txt | Log órfão |
| rebuild_widget.py | Wrapper legado de generate-graph-html.py |
| bridge_out.txt, serve_sync_out.txt, serve_sync_err.txt, bridge_err.txt, bridge_historico.json | Lixo de redirecionamento/runtime não rastreado |

## Regra

Antes de ressuscitar qualquer arquivo daqui, confirme que o equivalente ativo
(generate-graph-html.py, test_vox.py, etc.) não cobre o caso. Se cobrir, apague
em vez de manter duplicado.
