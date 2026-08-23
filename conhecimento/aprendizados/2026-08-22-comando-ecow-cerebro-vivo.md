---
tipo: padrao
tags: [widget, cerebro-vivo, opencode, comando, foco-janela, ecow]
data: 2026-08-22
contexto: Usuário pediu comando /ecow e @ecow para abrir o widget Cérebro Vivo; se já aberto, trazer a janela para frente em vez de duplicar.
---

# @ecow e /ecow — abrir/focar o Cerebro Vivo

## Decisão
Três camadas enxutas, sem duplicar lógica de foco fora do widget:

1. **scripts/widget_grafo.py** — quando `instancia_unica()` detecta instância
   já rodando, a nova instância usa ctypes (`FindWindowW(None, "Cerebro Vivo")`
   → `ShowWindow(hwnd, 9)` SW_RESTORE → `SetForegroundWindow(hwnd)`) e sai.
   O comportamento "abrir ou focar" vive DENTRO do widget: qualquer launcher se beneficia.
2. **scripts/ecow.bat** — launcher fino no padrão do controle.bat (pythonw, sem console).
3. **Comando `ecow` no config/opencode.jsonc** (repo + deployed, com backup .bak)
   + agente `config/agents/ecow.md` (mode: subagent) para o gatilho @ecow.

## Impacto
- `/ecow` executa via LLM curta (agente ecow); comportamento garantido pelo bat.
- Futuras notas/memórias continuam pulsando em amarelo por 12h (recurso anterior intacto).
- Nenhum processo duplicado nos testes; foco confirmado com hwnd válido.

## Aprendizados
- `Get-Process pythonw` não mostra MainWindowTitle da janela do widget porque ela é
  frameless/criada via webview — para validar janela usar EnumWindows ou FindWindowW pelo título.
- Preflight: MCP mcp-desenvolvimento pode dar timeout transitório de 5s na primeira
  execução (cold start); re-rodar antes de considerar falha real.
- Deploy cirúrgico do jsonc (injetar só o bloco novo após backup) evita divergência
  entre template com {{USERPROFILE}} e deployed com paths absolutos.

## Conexoes

- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]