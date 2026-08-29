---
tags: [decisao, depends, files, flag, opencode, task]
aliases: [context-engine + manifesto + domínios multimídia/comportamen]
date: 2026-08-05
---

# context-engine + manifesto + domínios multimídia/comportamentais

**Fonte:** opencode

---
tipo: decisao
tags: [context-engine, manifesto, mcp, habilidades, multimidia, comportamentais, coordenador]
data: 2026-08-04
contexto: Plano de lacunas do EcoSystemUmGrau. Auditoria mostrou que a reorg Habilidades/ ja foi feita (agora mcp/<dominio>/habilidades). Usuario optou por implementar apenas gaps reais.
decisao: Implementar context-engine (prioridade maxima), manifesto_geral.json e preencher dominios multimidia/comportamentais.
impacto: Agente coordenador tem motor de contexto unificado; catalogo de habilidades (48) com contrato manifesto; 2 novos dominios MCP registrados.
---

# context-engine + manifesto + domínios multimídia/comportamentais

## Auditoria do estado real
- Plano listava HABILIDADES/ e scripts/ como se a reorg nao tivesse acontecido — mas ela
  ja foi feita: skills vivem em `mcp/<dominio>/habilidades/` (40 skills em 4 dominios:
  android, desenvolvimento, internet, memoria).
- Gap real: context-engine (coordenador), manifesto_geral.json, multimidia/ e
  comportamentais/ (so README, sem server.py nem skills).

## O que foi implementado
### context-engine (mcp/memoria/habilidades/context-engine/)
- `skill.md` declarativa + `context_engine.py` com 5 modos:
  - `--buscar`: BM25 unificado sobre grafo de conhecimento + memorias + notas (reuso search_knowledge.py)
  - `--paralelo`: orquestracao de subtarefas via parallel_dispatcher.py (JSON de tasks)
  - `--gravar`/`--episodio`: memoria episodica em conhecimento/episodios.json
  - `--drift`: compara estado vs SYSTEM_SPEC.md/CONHECIMENTO.md
  - `--impacto`: quem referencia um alvo (cascata)
- Exposto automaticamente pelo server MCP generico de memoria (skill-context-engine).

### manifesto_geral.json + gerador
- `scripts/generate-manifesto.py` escaneia mcp/*/habilidades/, extrai frontmatter e gera
  o manifesto. Auto-sustentavel: rodar sempre que skills mudarem. 48 habilidades catalogadas.

### Dominios novos
- `mcp/multimidia/server.py` + 4 skills: audio-processing, video-processing, image-processing, streaming.
- `mcp/comportamentais/server.py` + 4 skills: code-reviewer, conservador, pensador-critico, ponytail.
- Registrados `mcp-multimidia` e `mcp-comportamentais` no opencode.jsonc (backup + preflight PASS).

## Licoes tecnicas
1. **parallel_dispatcher.py espera um JSON de tasks como argv[1]** (`[{name,command,cwd,read_files,write_files,depends_on}]`), NAO uma flag `--task`. Orquestracao = montar JSON + subprocess.
2. **Resolucao de BASE em scripts dentro de mcp/**: sobe ate achar `ler-runtime/` (nao parent fixo — o depth muda).
3. **Server MCP generico por dominio**: copy identico (hash MD5 igual) entre dominios; auto-descoberta de habilidades/. Registrar dominio no config = novo bloco mcp.

## Validacao
- preflight_check.py: TODOS TESTES PASSARAM (template 12 MCP, deployed 10 MCP).
- MCP test: initialize + tools/list + tools/call OK nos 3 servers (multimidia, comportamentais, memoria).
- context-engine: buscar/gravar/episodio/drift/impacto testados; paralelo faz dispatch+agregacao.
- .gitignore: adicionado context/tarefas_paralelas.json (efemero).
- Memory #88.

## Conexoes

- [[correcao-de-diagnostico-do-knowledge-graph-e-criacao-do-regi]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]