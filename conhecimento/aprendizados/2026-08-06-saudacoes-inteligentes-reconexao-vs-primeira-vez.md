---
tipo: padrao
tags: [bridge, saudacao, jarvis, reconexao, estado-persistente, primeira-conexao]
data: 2026-08-06
contexto: "O bridge Jarvis (jarvis_bridge.py) cumprimentava toda conexao com o mesmo molde, sem distinguir a PRIMEIRA vez da RECONEXAO. O usuario queria que a retomada de conversa fosse reconhecida e curta, sem repetir briefing."
decisao: "Persistir estado de saudacoes em saudacao_estado.json e classificar cada conexao como primeira-vez ou reconexao usando 3 fontes independentes. Em reconexao, o LLM recebe prompt de retomada curta (sem briefing) com a lista de saudacoes ja usadas para nao repetir."
impacto: "Reconexoes geram retomadas curtas e variadas ('De volta, senhor. Continuando de onde paramos.'), sem re-briefing e sem repetir saudacoes no mesmo dia."
---

# Saudacoes inteligentes: reconexao vs primeira vez

## Problema
Toda conexao recebia a mesma saudacao com briefing completo. Reconectar em segundos
era tratado como primeira visita, gerando repeticao e 'como posso ajudar' a cada vez.

## Solucao — estado persistente + classificacao em 3 fontes

### Estado `saudacao_estado.json`
- `conexoes`: contador total de conexoes.
- `saudacoes_hoje`: lista das saudacoes ja usadas hoje (max 10) — evita repeticao.
- `ultima_saudacao` / `ultima_saudacao_ts`: referencia da ultima.

### `_classificar_conexao()` — 3 fontes independentes
1. **Estado de saudacoes**: ja saudou hoje? (persistido).
2. **Atividade persistida via `_marcar_atividade()`**: atualizada a cada mensagem
   real — cobre o caminho rapido (reconexao sem nova saudacao registrada).
3. **mtime do `conversa_unica.json`**: historico de uso recente.

Qualquer sinal de atividade recente => RECONEXAO. Ausencia total => PRIMEIRA VEZ.

### Prompt do LLM diferenciado
- **Reconexao**: retomada curta de conversa — sem briefing, sem 'como posso ajudar',
  com a lista de saudacoes ja usadas para nao repetir.
- **Primeira vez**: molde antigo com briefing completo.

### Fallback variado
- Reconexao usa frases de retomada alternadas: "De volta, senhor. Continuando de onde
  paramos.", "Voltou. Sistemas seguem quentes, é só falar." — sem depender do LLM.

### Timeout
- Saudacao: 25s -> 90s (evita timeout no cold start do modelo na primeira conexao).

## Validacao
- 3 conexoes seguidas => 3 saudacoes distintas.
- Reconexao retornou: "De volta, senhor. Continuando de onde paramos." e
  "Voltou. Sistemas seguem quentes, é só falar." — reconhecendo retomada.

## Monitoramento
- Estado: `scripts/saudacao_estado.json`.
- Log: `scripts/bridge_log.txt` (heartbeats do celular a cada ~15s).

## Memorias relacionadas
- #131 (padrao): Saudacoes inteligentes (reconexao vs primeira vez).
- #129 (decisao): Clausula petrea — protecao do desktop e resiliencia da bridge.
