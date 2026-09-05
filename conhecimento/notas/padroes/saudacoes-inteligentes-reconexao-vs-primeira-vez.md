---
tags: [ajudar, nova, opencodeopencode, padrao, registrada, repeticao]
aliases: [Saudacoes inteligentes: reconexao vs primeira vez]
date: 2026-08-06
---

# Saudacoes inteligentes: reconexao vs primeira vez

**Fonte:** opencode+opencode

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
- **Reconexao**: retomada curta de conversa — sem briefing, sem 'como posso ajuda
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[fase2-limpeza-git-artefatos-rastreados]]
- [[padrao-hub-padroes]]