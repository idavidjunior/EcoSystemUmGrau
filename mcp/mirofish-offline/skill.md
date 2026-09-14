# MiroFish-Offline — Simulação Multi-Agente Local (Neo4j + Ollama)

## Objetivo
Integrar o MiroFish-Offline (fork 100% local do MiroFish) ao ecossistema como skill/MCP para simulação de cenários sociais, opinião pública, mercado e políticas via multi-agente com GraphRAG em Neo4j + LLM local via Ollama.

## Stack
- **Neo4j Community Edition 5.15** — Grafo de conhecimento (entidades, relacionamentos, memórias individuais/coletivas)
- **Ollama** — LLM local (qwen2.5:7b para raciocínio, nomic-embed-text para embeddings)
- **OASIS (CAMEL-AI)** — Motor de simulação multi-agente
- **Python/Flask** — Backend API

## Estrutura do Projeto (fork offline)
```
mirofish-offline/
├── backend/
│   ├── app.py                 # Flask app
│   ├── graph_storage.py       # Neo4j GraphStorage (interface abstrata)
│   ├── neo4j_storage.py       # Implementação Neo4j
│   ├── simulation/
│   │   ├── engine.py          # Motor OASIS
│   │   ├── agent.py           # Persona, memória, comportamento
│   │   └── platforms.py       # Plataformas sociais simuladas
│   ├── report_agent.py        # ReportAgent com ferramentas
│   └── tools/
│       ├── insight_forge.py   # Extração de insights
│       ├── panorama.py        # Visão macro
│       └── agent_interview.py # Entrevista agentes
├── frontend/                  # React (traduzido EN)
├── docker-compose.yml         # Neo4j + Ollama + Backend
└── requirements.txt
```

## Integração com Ecossistema (MCP)

### Tools expostas via MCP `mirofish-offline`:

1. **`build_scenario`** — Cria cenário a partir de documento (PDF/MD/TXT)
   - Extrai entidades/relacionamentos (NER/RE via LLM local)
   - Constrói GraphRAG no Neo4j
   - Gera personas (centenas de agentes com personalidade, viés, influência)

2. **`run_simulation`** — Executa simulação multi-agente
   - Parâmetros: rounds, plataformas, variáveis injetadas ("visão de Deus")
   - Retorna: evolução de sentimento, propagação de tópicos, dinâmica de influência

3. **`generate_report`** — Gera relatório estruturado pós-simulação
   - ReportAgent analisa ambiente, entrevista agentes, busca no grafo
   - Retorna: sumário executivo, métricas, alertas, branch points

4. **`interact_agent`** — Chat com agente específico pós-simulação
   - Memória e personalidade preservadas
   - Perguntas: "por que postou isso?", "o que mudaria sua opinião?"

5. **`query_graph`** — Consulta direta no GraphRAG (Cypher/híbrido)
   - Busca vetorial (0.7) + BM25 (0.3)
   - Filtros: entidade, tempo, cluster

5. **`inject_variable`** — Injeta variável dinâmica na simulação rodando
   - Ex: "nova notícia sai às 14h", "regulador anuncia multa"

## Configuração Necessária

### Ollama (já instalado em C:\Users\David Jr\AppData\Local\Programs\Ollama)
- Modelos necessários:
  - `qwen2.5:7b` — LLM principal (raciocínio, personas, relatórios)
  - `nomic-embed-text` — Embeddings (GraphRAG híbrido 0.7 vetor + 0.3 BM25)
  - Opcional: `llama3:8b` — alternativa LLM

### Neo4j Community Edition 5.15
- Porta bolt: 7687, HTTP: 7474
- Auth: neo4j/password (configurável)
- Plugins: APOC (para procedures), Graph Data Science (opcional)

### Variáveis de Ambiente (.env)
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mirofish123
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b
EMBED_MODEL=nomic-embed-text
SIMULATION_ROUNDS=3
AGENT_COUNT=200
```

## Uso via Agente `@executor` ou `@compreender`

```bash
# Via executor governado
/executor "Simule a reação pública a uma alta de juros de 0.5% usando MiroFish-Offline"

# Via compreender
@compreender "Quero testar cenário de crise de PR: vazamento de dados de 1M usuários"
```

## Integração com Executor Governado

### Fase 0 — Conselheiros analisam
- **Estrategista**: Define objetivo da simulação
- **Cético**: Identifica vieses nos seed documents
- **Realista**: Estima custo computacional (200 agentes × 3 rounds)
- **Ético**: Verifica LGPD nos seed documents
- **Recursos**: Verifica modelos Ollama + Neo4j disponíveis

### Fase 1-5 — Executor Governado orquestra
- Delega build_scenario → run_simulation → generate_report
- Validações: preflight_check.py (Neo4j up, Ollama models loaded)
- Checklist entrega: relatório + grafo exportado + logs de simulação

## Próximos Passos
1. ✅ Ollama instalado + modelos (qwen2.5:7b baixando, nomic-embed-text OK)
2. ⏳ Neo4j CE 5.15 baixando (zip 300MB+)
3. ⬜ Extrair Neo4j, configurar como serviço Windows
3. ⬜ Clonar MiroFish-Offline (fork nikmcfly/Boromoi)
4. ⬜ Configurar .env, rodar docker-compose ou backend direto
5. ⬜ Criar MCP server wrapper (stdio JSON-RPC)
6. ⬜ Registrar no opencode.jsonc
7. ⬜ Testes: build_scenario → run_simulation → generate_report
6. ⬜ Registrar skill em mcp/mirofish-offline/skill.md
7. ⬜ Persistir via gate