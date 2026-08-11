---
tipo: padrao
tags: [jarvis, voz, controle, palavra-gatilho, eco, narracao, runtime]
data: 2026-08-10
contexto: "Usuário pediu uma palavra simples para ativar/desativar a narração: 'Eco' liga e 'D Eco' desliga. Harmoniza com a cláusula da Constituição (Eco ativa voz, Desativar Eco desativa)."
decisao: "Criado scripts/jarvis_audio.py on|off|status: grava runtime/narracao_estado.json ({"ativo": bool}); o narrador (narrador_desktop.py) lê o controle a cada loop e pausa sem ser encerrado (avançando a posição para não acumular backlog). on também garante o processo rodando via PID file + tasklist. Palavras-gatilho: 'Eco' -> on; 'D Eco'/'Desativar Eco' -> off. Detalhe Windows: os.kill(pid,0) não serve para checar processo; usar tasklist."
impacto: "Toggle simples e robusto de narração sem matar/recriar processo. Validado: ciclo status->on->off->status com processo permanecendo vivo e log de estados. Narração reativada após o teste."
---

# Aprendizado: Controle Eco / D Eco da narração

## Resumo

Palavras-gatilho para ligar/pausar a narração do Jarvis no desktop, sem derrubar
o processo.

## Mecanismo

- `scripts/jarvis_audio.py on|off|status` — grava `runtime/narracao_estado.json`.
- `narrador_desktop.py` lê o controle a cada loop: `{"ativo": false}` pausa
  (avança a posição para não narrar backlog quando voltar).
- `on` garante o processo rodando (PID em `runtime/narrador.pid`, checado via
  `tasklist /FI "PID eq X"`).

## Lições

- Controle por arquivo de estado é mais robusto que matar o processo.
- No Windows, `os.kill(pid, 0)` não é confiável para checar existência (usa
  TerminateProcess para sinais não-CTRL); `tasklist` resolve.

## Conexoes

- [[cluster-hub-programacao]]