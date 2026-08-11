---
tipo: aprendizado
tags: [jarvis-bridge, voz, widget, grafo, pywebview, comando-voz, cerebro-vivo]
data: 2026-08-04
contexto: Usuario pediu o 'foco vocal via Jarvis' — comando de voz orienta o grafo do conhecimento (cerebro vivo). Bridge Jarvis roda na porta 8765 (processo separado) e o widget do grafo (pywebview) e outro processo; sem API entre eles.
decisao: Usar o filesystem como canal entre processos (o widget ja vigia arquivos do vault). (1) jarvis_bridge._comando_grafo(t) em caminho_rapido reconhece o comando e grava docs/comando_grafo.json {filtro,valor,cor,nome,ts}. (2) widget_grafo.Bridge.comando_grafo(ultimo_ts) le o json e so retorna quando ts e mais recente (dedup por ts). (3) WIDGET_JS_EXTRA ganha polling buscarComandoVoz (2.5s) que chama pywebview.api.comando_grafo e dispara destacar(filtro,valor,cor) — funcao já global do grafo. Sem round-trip ao LLM (Política de Resposta Rápida).
impacto: Voce agrega o visual do grafo: falar 'mostre bugs/abra android/centro no ecossistema' orienta a malha viva. Dedup por timestamp evita reaplicar. Preflight 100% PASS. Memory #83.
---

# 2026-08-04: Foco vocal via Jarvis — voz orienta o grafo do conhecimento

## Arquitetura (2 processos, sem API própria)
- Bridge de voz: `scripts/jarvis_bridge.py`, WS na porta 8765.
- Widget do grafo: `scripts/widget_grafo.py` (pywebview) — outro processo.
- Canal: **filesystem** via `docs/comando_grafo.json` (o widget já monitora arquivos).

## Fluxo
1. Usuário fala "mostre bugs" / "abra android" / "centro no ecossistema".
2. `caminho_rapido(msg)` (0 round-trip ao LLM) chama `_comando_grafo(t)`.
3. `_comando_grafo` casa palavra-chave (categoria/cluster) + verbo de intenção
   (mostre/mostra/foca/foque/abra/abrir/centro/ver/...). Grava o json e responde
   "Ok, mostrando <nome> no grafo do conhecimento."
4. Widget: `setInterval(buscarComandoVoz, 2500)` → `pywebview.api.comando_grafo(ts)`.
5. Python lê o json; só retorna se `ts > ultimo_ts` processado (dedup).
6. JS dispara `destacar(cmd.filtro, cmd.valor, cmd.cor)` → destaca na malha viva.

## Detalhes técnicos validados
- `destacar` é função global do `<script>` principal do grafo; `WIDGET_JS_EXTRA` é
  injetado depois (no `</body>`), então acessa sem problema.
- Cores mapeadas às constantes do grafo (CATEGORIA_COR e CLUSTER_COR).
- `re.escape(kw)` com `r'\b...\b'` (cuidado: `\\b` em string raw é barra literal,
  quebra o casamento — usar `\b`).
- Comando com acento: `_sem_acentos` normaliza antes, então palavras com acento
  precisam também de forma sem acento no mapa ou vira `None`.

## Cuidados / lições
- Ao editar via tool, preservar docstrings e indentação (houve <def perdido> por
  edição parcial; corrigido restaurando o docstring e o corpo).
- Testar com função isolada antes de confiar no fluxo completo.
- Sempre rodar `py_compile` + `node --check` (em JS puro, sem tag `<script>`) +
  `preflight_check.py` (cláusula pétrea).
