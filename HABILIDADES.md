# Mapa-Mestre de Habilidades — Jarvis / EcoSystemUmGrau

> **Fonte única da verdade sobre o que o Jarvis sabe fazer.**
> Atualizado em: 2026-08-02 · Catálogo em `Habilidades/manifesto_geral.json`

Toda habilidade abaixo é acionável pelo Jarvis. A ortografia dos nomes dos arquivos é preservada (skill.md, SKILL.md, readme.md).

---

## 1. Habilidades de Voz e Conversa

**Fonte:** `scripts/JARVIS_SYSTEM.md`

| Habilidade | Descrição |
|---|---|
| Reconhecimento de fala | STT via SpeechRecognizer do Android (português) |
| Síntese de voz | TTS edge-tts `pt-BR-AntonioNeural` (voz atual) |
| Pontuação automática | `fix_punctuation()` detecta pergunta/afirmação e pontua |
| Melhoria de fala | `melhorar_fala()` ajusta entoação e capitalização |
| Correção de pronúncia | SSML `<phoneme>` com IPA via `pronuncias.json` |
| Histórico unificado | `conversa_unica.json` (max 50 pares, app + CLI) |
| Saudações variadas | Saudações únicas e criativas, sem repetição |
| Fala em PT-BR | Exclusivamente português brasileiro, com gramática correta |

---

## 2. Habilidades Técnicas (37)

**Fonte:** `Habilidades/tecnicas/*/` (SKILL.md ou skill.md)

### Android e Mobile
| Habilidade | Entrypoint |
|---|---|
| `android-diagnostics` | skill.md — Diagnóstico remoto automático do VoxUmGrau |
| `android-pure-sdk` | SKILL.md — Build Android puro (aapt, javac, d8, apksigner) |
| `mp3player-metadata-rescue` | SKILL.md — Metadata rescue e build intelligence do MP3Player |
| `mobile-specific-patterns` | skill.md — Padrões específicos de desenvolvimento mobile |

### Clima e Geolocalização
| Habilidade | Entrypoint |
|---|---|
| `clima-api` | skill.md + clima_api.py — Clima atual e previsão via Open-Meteo |
| `endereco-geo` | skill.md + endereco.py — Endereço por geolocalização reversa (Nominatim) |

### LER e Autonomia
| Habilidade | Entrypoint |
|---|---|
| `ler` | SKILL.md — Loop Engineering Runtime |
| `autonomous-loops` | skill.md — Loops autônomos planejar-executar-verificar-corrigir |
| `state-machine-patterns` | skill.md — Máquinas de estado |
| `graphify` | SKILL.md — Grafos de conhecimento |

### Backend, Frontend e Arquitetura
| Habilidade | Entrypoint |
|---|---|
| `api-design` | skill.md — Design de APIs |
| `backend-patterns` | skill.md — Padrões de backend |
| `frontend-patterns` | skill.md — Padrões de frontend |
| `golang-patterns` | skill.md — Padrões Go |
| `python-patterns` | skill.md — Padrões Python |
| `database-migrations` | skill.md — Migrações de banco |
| `deployment-patterns` | skill.md — Padrões de deploy |
| `docker-patterns` | skill.md — Padrões Docker |
| `local-first-architecture` | skill.md — Arquitetura local-first |
| `edge-compute-patterns` | skill.md — Computação de borda |
| `concurrent-computation-patterns` | skill.md — Computação concorrente |
| `resilience-engineering` | skill.md — Engenharia de resiliência |
| `observability-stack` | skill.md — Observabilidade |
| `migration-playbooks` | skill.md — Playbooks de migração |

### Segurança e Privacidade
| Habilidade | Entrypoint |
|---|---|
| `authz-authn-matrix` | skill.md — Matriz de autorização/autenticação |
| `data-privacy-by-design` | skill.md — Privacidade por design |
| `security-review` | skill.md — Revisão de segurança |

### Testes e Qualidade
| Habilidade | Entrypoint |
|---|---|
| `tdd-workflow` | skill.md — Workflow TDD |
| `e2e-testing` | skill.md — Testes ponta a ponta |
| `error-message-design` | skill.md — Design de mensagens de erro |
| `developer-experience-dx` | skill.md — Experiência do desenvolvedor |
| `semantic-release-automation` | skill.md — Versionamento semântico automático |

### IA, Busca e Custos
| Habilidade | Entrypoint |
|---|---|
| `cost-aware-llm-pipeline` | skill.md — Pipelines de LLM conscientes de custo |
| `multi-modal-ai` | skill.md — IA multimodal |
| `search-first` | skill.md — Busca em primeiro lugar |
| `cache-strategy-selector` | skill.md — Seleção de estratégia de cache |

### Navegação e Automação
| Habilidade | Entrypoint |
|---|---|
| `navegacao-perita` | skill.md — Perícia em navegar/clicar/ver tela (Playwright, FlaUI/UIA, ADB) |

---

## 3. Habilidades Ponte (2)

**Fonte:** `Habilidades/pontes/*/`

| Habilidade | Entrypoint | Descrição |
|---|---|---|
| `busca-web` | skill.md | Busca agêntica na web |
| `busca-conhecimento` | search_knowledge.py | Busca semântica (BM25 + grafos) no knowledge graph, notas e memória |

---

## 4. Habilidades Comportamentais (1)

**Fonte:** `Habilidades/comportamentais/ponytail/`

| Habilidade | Entrypoint | Descrição |
|---|---|---|
| `ponytail` | README.md | Personalidade lazy senior dev — pendente de conteúdo real |

---

## 5. Multimídia (reservado)

**Fonte:** `Habilidades/multimidia/`

Reservado para futuras habilidades de áudio, imagem e vídeo.

---

## 6. Agentes OpenCode (16)

**Fonte:** `config/agents/*.md`

| Agente | Papel |
|---|---|
| `00-system-rules` | Regras do sistema |
| `00-maestro` | Orquestração e roteamento |
| `00-agent-template` | Template para criação de novos agentes |
| `01-estrategista` | Estratégia |
| `02-cetico` | Ceticismo e crítica |
| `03-realista` | Realismo |
| `04-etica` | Ética |
| `05-futuro` | Visão de futuro |
| `06-recursos` | Recursos |
| `07-criativo` | Criatividade |
| `08-revisor` | Revisão |
| `09-executor` | Execução |
| `10-aprendizado` | Aprendizado e consolidação de conhecimento |
| `11-ler-executor` | Execução de missões LER |
| `12-parallel-planner` | Planejamento paralelo |
| `99-gerador-de-agentes` | Geração de novos agentes |

---

## 7. Scripts de Operação (scripts/)

| Script | Função |
|---|---|
| `jarvis_bridge.py` | Bridge principal (WebSocket porta 8765) |
| `run_bridge.py` / `run_serve.py` | Launchers da bridge e do serve |
| `watchdog.ps1` | Monitora bridge e serve a cada 20s, reinicia se cair |
| `ecosystem.ps1` | Gerenciamento do ecossistema |
| `bootstrap.ps1` | Inicialização do ambiente |
| `vigilante.ps1` | Monitoramento git |
| `memory_engine.py` | Motor de memória e persistência |
| `mcp-knowledge-server.py` | Servidor MCP de conhecimento |
| `parallel_dispatcher.py` | Despachante paralelo de tarefas |
| `preflight_check.py` | Verificação pré-execução |
| `search_knowledge.py` | Busca na base de conhecimento |
| `generate-obsidian-notes.py` | Geração de notas Obsidian |
| `deploy-config.ps1` | Deploy de configuração |
| `debug_mcp.py` | Debug de MCP |
| `test-ecosystem.ps1` / `test_vox.py` | Suites de teste |
| `geolocalizacao.py` / `clima_api.py` | Geolocalização e clima |

---

## 8. Servidores MCP (config/opencode.jsonc)

| Servidor | Tipo | Status |
|---|---|---|
| `eco-knowledge` | local (python) | habilitado |
| `filesystem` | local (node) | habilitado |
| `search` | local (node) | habilitado |
| `terminal` | local (node) | habilitado |
| `github` | local (node) | desabilitado |

---

## 9. Conhecimento (memória de longo prazo)

| Fonte | Local |
|---|---|
| Knowledge Graph | `ler-runtime/knowledge/knowledge_graph.json` |
| Conhecimento exportado | `ler-runtime/CONHECIMENTO.md` |
| Aprendizados | `conhecimento/aprendizados/` |
| Memória de sessão | `conhecimento/memoria/` |
| Templates | `conhecimento/templates/` (aprendizado, bug, decisão, padrão) |
| Vault Obsidian | raiz do ecossistema (`C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau`) |

---

## Fluxo de acionamento

1. **Pergunta chega** pela bridge (app Android) ou pelo CLI
2. **Mapa localiza** a habilidade certa por categoria e trigger
3. **Manifesto** `manifesto_geral.json` confirma id, entrypoint, parâmetros e dependências
4. **Conhecimento** da base (KG + notas + memória) complementa o contexto
5. **Ação** é executada e o aprendizado volta para `conhecimento/aprendizados/`

*Fim do mapa-mestre.*
