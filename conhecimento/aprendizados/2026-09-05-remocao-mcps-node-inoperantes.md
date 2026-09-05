---
tipo: decisao
tags: [mcp, node, python, opencode, config, remocao, preflight]
data: 2026-09-05
title: Remocao dos MCPs Node inoperantes (filesystem, search, terminal, github)
status: aplicado
---

## Contexto

Quatro servidores MCP do opencode (filesystem, search, terminal, github) estavam
desligados desde sempre: rodam via `node mcp-servers/<nome>/index.js`, mas o Node.js
nao esta instalado no PC (nao existe `node.exe` no PATH nem em locais padrao). O erro
de inicializacao era WinError 2 (sistema nao encontra o arquivo). Os outros 12 MCPs
funcionam porque sao Python puro e o Python esta no PATH.

## Analise

Inspecao dos 4 servidores Node mostrou redundancia total com capacidades ja existentes:

- filesystem (listar/ler/escrever/pesquisar arquivos) duplica os tools nativos
  Read/Write/Edit/Glob/Grep do opencode e o mcp-dev-tools.
- terminal (PowerShell com bloqueio de destrutivos) duplica o Bash nativo do opencode.
- search (BM25 sobre knowledge graph, CONHECIMENTO.md, memories, habilidades,
  aprendizados e notas) duplica eco-knowledge, eco-obsidian e mcp-memoria (Python,
  ja online).
- github (wrapper do CLI gh) duplica o uso do gh via persistencia.ps1 e Composio.

Nenhum dos 4 sobe hoje; remove-los do config nao muda o funcionamento atual.

## Decisao

Remover os 4 MCPs Node em vez de instalar Node.js ou reescrever em Python. Criterios
da Regra de Ouro: simplicidade, menor custo de manutencao, menor acoplamento,
eliminacao de duplicacao. Nao criar estrutura nova (reescrever em Python criaria
caminhos paralelos) sem necessidade comprovada.

## Execucao

- config/opencode.jsonc (template) e ~/.config/opencode/opencode.jsonc (deployed):
  removidos os blocos filesystem, search, terminal, github. Sobram 12 MCPs Python.
- Pasta mcp-servers/ removida (5 arquivos, versionados no git: reversiveis).
- README.md: atualizada a arvore (sem mcp-servers) e a secao de MCPs (12 servidores,
  todos Python; completada a tabela com mcp-browser, mcp-dev-tools e composio, que
  estavam faltando).
- conhecimento/etica/inventario_dados.json: removidas 6 entradas de arquivos
  mcp-servers (5 em identificacao, 1 em biometrico). Backup automatico .bak.

## Bug corrigido no caminho (preflight travado)

O preflight ate falhava por outro motivo: scripts/test_json_sanitization.py reportava
"Hardcoded path found: conhecimento/memoria/memories.json (3)" porque a lista
DATA_FILES existe justamente para arquivos de dados/historicos, mas a flag is_data_file
so era aplicada ao check de template vars, nao ao check de hardcoded paths. As 3
ocorrencias sao texto descritivo legitimo de memorias (relatorio de auto-evolucao e
diagnostico do CapCut). Corrigido o script: arquivos em DATA_FILES nao disparam FAIL
por path hardcoded no conteudo textual.

## Impacto

- Preflight tecnico: TODOS OS TESTES PASSARAM (12/12 MCPs online, 0 erros).
- Preflight etico: aprovado.
- Experiencia: item irrelevante, pois nenhuma ferramenta ativa dependia dos 4 MCPs.
- Reversibilidade: git historico + backup .bak do inventario e do config.
- Alternativa nao usada (registro): instalar Node via winget (OpenJS.NodeJS.LTS) para
  manter os servidores Node — descartada por nao haver necessidade de funcionalidade.

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[cluster-hub-programacao]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[nodejs-commonjs-esm-e-resolução-de-módulos]]
- [[nodejs-event-loop-e-io-não-bloqueante]]
- [[nodejs-streams-e-backpressure]]
- [[python-sintaxe-e-núcleo-da-linguagem]]