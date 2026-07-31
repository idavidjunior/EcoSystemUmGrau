# EcoSystemUmGrau

> **Ecossistema autônomo** LER + OpenCode + Obsidian + Ponytail — um cérebro distribuído
> que aprende, lembra e evolui sozinho a cada sessão.

![Estágio](https://img.shields.io/badge/est%C3%A1gio-3%20%7C%20Orquestrado-%236c5ce7)
![Agents](https://img.shields.io/badge/agents-15-%236c5ce7)
![Skills](https://img.shields.io/badge/skills-34-%236c5ce7)
![Status](https://img.shields.io/badge/status-ativo-brightgreen)

## O que é

Um ecossistema de desenvolvimento pessoal que une **4 ferramentas** em um único
fluxo autônomo de trabalho, memória e conhecimento:

| Ferramenta | Papel |
|---|---|
| **OpenCode** | Orquestrador principal — 15 agents com gates SDLC (G1–G5) |
| **LER** (Loop Engineering Runtime) | Loops autônomos Python para tarefas complexas |
| **Obsidian** | Vault inteligente — 228+ notas, 8 MOCs, templates, Dataview |
| **Ponytail** | Plugin que mantém o estado/forma de trabalho entre sessões |

## Arquitetura (3 cérebros)

```
Usuário → Maestro → classifica rota (A/B/C)
  → G1 PLAN → G2 IMPLEMENT → G3 VERIFY → G4 REVIEW → G5 MERGE
  → registra aprendizado → sincroniza (Vigilante)
```

1. **Knowledge Graph** — conhecimento explícito consolidado em `knowledge_graph.json`
   e exportado para `CONHECIMENTO.md` (carregado no contexto de todo agente).
2. **Memory Engine** — memória de sessão com **decay de Ebbinghaus**
   (`score = strength * 0.5^(days/half_life)`), reforço por acesso frequente.
3. **Semantic Search** — busca **BM25 fusion** em 4 fontes (KG + memória + notas + skills).

### Maestro — Matriz de Decisão

| Rota | Quando |
|---|---|
| **A (OpenCode)** | Tarefa simples, 1–3 arquivos, resultado óbvio |
| **B (LER)** | Multi-passo, exploração, loop, 4+ arquivos, >15 min |
| **C (Híbrida)** | Começa em A, vira B se o contexto crescer |

## Regras de Ouro

1. **FONTE ÚNICA** — toda config, agente e skill vive neste repo. Nada duplicado fora dele.
2. **ABASTECER, NÃO CRIAR ESTRUTURA NOVA** — todo projeto abastece as estruturas
   existentes (decisões, padrões, bugs, heurísticas, frameworks, padrões cognitivos, missões).
3. **TESTAR SEMPRE** — toda alteração em `opencode.jsonc`, plugins, agents ou skills
   é validada com `opencode debug config`.
4. **REGISTRAR APRENDIZADO** — ao fim de toda tarefa, registra-se em `conhecimento/aprendizados/`.
5. **SINCRONIZAR SEMPRE** — tudo é comitado e sincronizado (local + GitHub). O GitHub é a
   rede de segurança do ecossistema.

## Setup — Plug & Play

```bash
git clone https://github.com/idavidjunior/EcoSystemUmGrau.git
cd EcoSystemUmGrau
setup.bat
```

O `setup.bat` faz tudo automaticamente em uma máquina nova: instala o OpenCode, gera
as configs a partir dos templates, configura o LER, pergunta as API keys.

## Comandos

| Comando | Função |
|---|---|
| `start-vigilante` | Inicia watcher + git sync em background |
| `stop-vigilante` | Para o processo |
| `status-vigilante` | Status do vigilante |
| `ecosystem sync` | Pull + push forçado (Eco + LER + todos os projetos) |
| `ecosystem scan` | Varre projetos e extrai padrões |
| `ecosystem status` | Status completo do ecossistema |
| `ecosystem repair` | Reconstrói o knowledge graph dos aprendizados crus |
| `ecosystem help` | Ajuda detalhada |

## Estrutura do Repo

```
EcoSystemUmGrau/
├── .github/workflows/   # CI/CD: eco-sync + knowledge-report
├── .obsidian/           # Vault Obsidian (config, plugins, workspace)
├── ai-agents/           # Claude Code extra agents
├── Android/             # Projetos Android monitorados pelo vigilante
├── config/              # Templates de config (opencode.jsonc, agents, plugins)
├── conhecimento/        # Aprendizados, memória, notas, templates
├── docs/                # Documentação
├── ferramentas/         # Ferramentas (Flutter, etc.)
├── ler/                 # Documentação do LER
├── ler-runtime/         # Runtime do LER (junction em ~/.ler/)
├── mcp-servers/         # Servidores MCP
├── plugins/             # Plugins (ponytail)
├── scripts/             # Vigilante, ecosystem, memory_engine, jarvis_bridge...
├── skills/              # 34 skills unificadas (SKILL.md)
├── estado_atual.md      # Snapshot completo do ecossistema
├── INDEX.md             # Mapa vivo do conhecimento (Obsidian)
├── MOC - *.md           # 8 Mapas de Conteúdo
└── setup.bat            # Setup plug & play
```

## Vigilante

`scripts/vigilante.ps1` — **FileSystemWatcher em tempo real** (sem polling):

- Detecta novos aprendizados → registra no consolidator → exporta `CONHECIMENTO.md`
- Detecta alterações em projetos Android → sync imediato
- Timer de 30s: git sync de todos os repos (Eco + LER + projetos)
- Auto-descoberta de projetos via pastas com `git remote`
- Scheduled task `EcoSystemVigilante` inicia no logon

## MCP Servers

| Servidor | Função |
|---|---|
| **knowledge** | Acesso ao knowledge graph |
| **filesystem** | Acesso ao filesystem |
| **github** | Integração com GitHub |

## CI/CD (GitHub Actions)

- **eco-sync** — a cada 6h valida knowledge graph, `CONHECIMENTO.md` e integridade
- **knowledge-report** — relatório de métricas de conhecimento

## Variáveis de Ambiente

| Variável | Uso |
|---|---|
| `NVIDIA_API_KEY` | Provider NVIDIA (fallback automático) |
| `OPENAI_API_KEY` | Provider OpenAI |
| `VAULT_PATH` | Caminho do vault Obsidian (raiz do ecossistema) |

## Runtime

OpenCode 1.18.x · Node.js 25.x · Python 3.12 · Git 2.55 · Bun 1.3.x · Windows (PowerShell)

## Repositório de Segurança

Este repo é a **fonte única** e a **rede de segurança** de todo o ecossistema.
Tudo que importa está versionado aqui — config, agents, skills, conhecimento e memória.
