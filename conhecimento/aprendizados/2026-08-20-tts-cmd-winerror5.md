---
tipo: erro
tags: [tts, winerror, lock, escrita-atomica, voz]
data: 2026-08-20
contexto: O usuário reportou uma mensagem de erro no widget em quadro vermelho mostrando "falha de voz: [WinError 5] Acesso negado" na renomeação de runtime/tts_cmd.tmp para runtime/tts_cmd.json. O quadro vermelho do widget exibe erros reais lidos dos logs (função _ler_recent_errors).
decisao: Adicionar retry na escrita atômica do tts_cmd.json nos três pontos que escrevem: _enviar_tts_cmd (novo helper) em narrador_desktop.py e widget_controle_jarvis.py, e retry no _atomic_write de unified_bridge.py. No Windows, Path.replace falha com WinError 5 quando o destino está aberto por outro processo (ex: tts_service lendo ou escritores concorrentes); o retry curto resolve o conflito temporário.
impacto: Escrita de comandos de voz fica resiliente a locks concorrentes; erros "falha de voz" transitórios deixam de aparecer no widget. Aplicado o princípio da escrita atômica com recuperação, sem mudar o protocolo de arquivo.