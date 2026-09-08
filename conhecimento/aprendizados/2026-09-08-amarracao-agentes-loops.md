---
tipo: padrao
tags: [amarração, loops, autonomo, mission_loop, cognitive_core, agentes]
data: 2026-09-08
contexto: Amarração dos agentes do EcoSystemUmGrau aos scripts de loop autônomo internos (authorizado pelo usuário: "vamos ligar as lacunas... fazer toda a amarração necessária").
decisao: Ligar 00-Maestro, 09-Executor, 11-LER-Executor e 12-Parallel-Planner aos scripts internos (mission_loop, council_orchestrator, autonomous_loop, parallel_dispatcher, tool_orchestrator) com critério de parada por evidência e fallback interno.
impacto: Agentes passam a executar missões em loop com verificação real de saída, em vez de depender só de delegação externa (LER) ou da palavra do modelo.
---

# Amarração dos agentes aos loops autônomos internos

## Bugs corrigidos

1. **import scripts.X quebrava como script direto** em cognitive_core.py e mission_loop.py.
   Causa: `sys.path` só continha o diretório `scripts/`, mas `import scripts.llm_router`
   exige a raiz do projeto no path. Correção: adicionar também o diretório pai (`os.path.dirname(_SCRIPT_DIR)`)
   ao sys.path. Agora `python scripts/mission_loop.py` funciona.

2. **parallel_dispatcher quebra com UTF-8 BOM** no tasks.json. O PowerShell grava BOM
   por padrão e o `json.load` falha. Documentado no 12-parallel-planner: gravar sem BOM.

## Amarrações realizadas

- **09-Executor:** nova seção "LOOP E VERIFICAÇÃO" — loop até verificação real passar,
  orçamento de passos, detecção de repetição, comandos mission_loop/tool_orchestrator/
  parallel_dispatcher, e verificação adversarial.
- **00-Maestro:** nova seção "ORQUESTRAÇÃO INTERNA" — council_orchestrator para
  deliberação, delegation ao mission_loop via executor, autonomous_loop --ciclo para
  melhoria contínua, e critério de parada obrigatório por evidência (nunca pela palavra).
- **11-LER-Executor:** novo "FALLBACK INTERNO" — quando `ler` indisponível, usar
  mission_loop interno com estados observáveis (COMPLETED/FAILED/BLOCKED) e exigir
  COMPLETED com evidência.
- **12-Parallel-Planner:** nota de encoding UTF-8 sem BOM; restante já amarrado.

## Lições

- Rodar scripts internos a partir da RAIZ do projeto.
- "Concluído" exige evidência de verificação (build/teste/lint), não a palavra do modelo.
- Exigir estado observável de saída (COMPLETED) em vez de aceitar "funcionou".

## Bug latente detectado (não corrigido — escopo separado)

`python scripts/memory_engine.py add ...` trava (timeout >120s) mesmo com
`--no-reindex` e com numpy já importado. Numpy 2.5.1 demora ~30-40s no primeiro
import (Windows + antivírus escaneando binários BLAS). O hang adicional na linha
`add` está no caminho de dedup `_buscar_similar` → `memory_semantic.search` e/ou
`_enrich_source_refs` → `source_registry`. Isso impede a persistência automática
de memória via script/CLI (a ferramenta MCP de memória também tinha timeout de
15s). Recomenda-se: investigar `memory_semantic.search` (carregamento do índice
TF-IDF) e `source_registry.get_relevant_sources` por falta de timeout; considerar
`validado=True` + escrita atômica direta em memórias.json só via gate. Este é um
bug pré-existente e independente da amarração dos agentes.
