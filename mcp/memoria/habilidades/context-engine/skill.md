---
name: context-engine
description: Motor de contexto do coordenador — unifica busca semantica, orquestracao paralela de agentes, memoria episodica persistente e deteccao de drift. Ativa quando o agente precisa decidir "o que ja sabemos sobre X", "o que decidimos na ultima vez que mexemos em X", quando varias frentes precisam ser investigadas em paralelo, ou quando suspeita que a realidade divergiu da especificacao. Trigger keywords: "contexto", "o que sabemos", "ultima vez", "paralelo", "drift", "impacto em cascata", "memoria episodica", "context-engine", "sintese proativa".
---

# context-engine — Motor de Contexto do Coordenador

## Objetivo

Dar ao agente a visão unificada do ecossistema antes de decidir: **o que já sabemos**,
**o que decidimos**, **onde a realidade divergiu da especificação** e **quem é afetado
em cascata** quando algo muda. Substitui o uso ad-hoc de `grep`/`glob` por consultas
estruturadas sobre conhecimento + memória + histórico.

## Modos de operação

### 1. Contexto semântico unificado
```powershell
python mcp/memoria/habilidades/context-engine/context_engine.py --buscar "o que sabemos sobre Android SDK"
```
Faz fusão **BM25 + grafo de conhecimento + memórias + notas + decisões** e retorna os
top hits com fonte (kg:/mem:/nota:/decisao:). Reutiliza `search_knowledge.py`.

### 2. Orquestração paralela de agentes
```powershell
python mcp/memoria/habilidades/context-engine/context_engine.py --paralelo "tarefa1|tarefa2|tarefa3"
```
Despacha múltiplas subtarefas via `parallel_dispatcher.py` (pool de 4 workers + locks de
arquivo) e agrega os resultados em um único relatório. Use quando precisar investigar
várias frentes simultaneamente (ex.: auditar 3 módulos de uma vez).

### 3. Memória episódica persistente
```powershell
python mcp/memoria/habilidades/context-engine/context_engine.py --gravar "decisao sobre X" "contexto e raciocinio"
python mcp/memoria/habilidades/context-engine/context_engine.py --episodio "X"
```
Grava decisões contextuais ("o que decidimos na última vez que mexemos em X") em
`conhecimento/episodios.json` e permite consultá-las por assunto — sem depender do
`conversa_unica.json` bruto.

### 4. Detecção de drift
```powershell
python mcp/memoria/habilidades/context-engine/context_engine.py --drift
```
Compara o estado atual do repo (estruturas, scripts citados, manifestos) contra as
especificações `SYSTEM_SPEC.md`/`CONHECIMENTO.md` e alerta sobre desvios:
arquivos que deveriam existir e sumiram, caminhos que mudaram, manifestos desatualizados.

### 5. Síntese proativa (impacto em cascata)
```powershell
python mcp/memoria/habilidades/context-engine/context_engine.py --impacto "arquivo_que_mudou.md"
```
Detecta quem referencia o alvo (imports, wikilinks, scripts) e sugere documentação
afetada em cascata. Ex.: "notei que X mudou, isso afeta Y e Z; quer que eu atualize a doc?"

## Regras de ouro
- **Não repita trabalho**: sempre consulte o contexto antes de propor solução.
- **Memória episódica antes de decisão**: se houver episódio sobre o assunto, cite-o.
- **Drift sinaliza, não corrige**: alerta desvios; a correção é decisão do agente.
- **Paralelizar quando independente**: subtarefas sem dependência entre si vão ao pool.

## Arquivos
- `context_engine.py` — implementação (CLI por modos).
- `skill.md` — este arquivo (definição declarativa).
- Saídas: `conhecimento/episodios.json` (memória episódica).
