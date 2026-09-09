# conhecimento/web — Mapa de Competências

**Categoria:** padrao
**Fonte:** Missão permanente do ecossistema (Constituição)
**Projeto:** EcoSystemUmGrau
**Dominio:** Engenharia Web

## Propósito

Mapa de competências de engenharia web do ecossistema. Cada bloco (A–L) registra status honesto e nível de evidência. Nada aqui é declarado MASTERED sem prova. Este arquivo é o índice da pasta `conhecimento/web`.

## Estrutura

```
conhecimento/web/
├── README.md               <- este arquivo (índice + mapa)
├── adrs/                   <- decisões de arquitetura relativas a web
├── labs/                   <- micro-labs executados e validados (evidências)
├── padroes/                <- padrões consolidados (formato template-padrao)
├── falhas/                 <- falhas encontradas em labs (formato template-bug)
└── benchmarks/             <- métricas medidas (CWV, latência, throughput)
```

Convenção de nomenclatura de subpastas em pt-BR: fundamentos, frontend, backend, bancos, ui-ux, animacao, graficos, ia, seguranca, performance, devops, arquitetura, padroes, labs, benchmarks, falhas, deprecados — criadas somente quando houver conteúdo real (evita estrutura ornamental).

## Escala de status

UNKNOWN (nunca tocado) → DISCOVERED (auditado/existe acervo, não validado) → STUDYING (em estudo) → IMPLEMENTED (implementado sem teste) → TESTED (testado) → UNDERSTOOD (entendido com fundamento) → VALIDATED (evidência real) → MASTERED (evidência + integração + 20 demonstrações) → DEPRECATED.

Nível: 0–8. MASTERED exige nível 8 com evidência documentada.

## Blocos de competência (missão: engenharia web)

| Bloco | Competência | Status | Nível | Evidência |
|---|---|---|---|---|
| A | Fundamentos (HTML, CSS, HTTP, JSON, DOM, acessibilidade) | VALIDATED | 3 | www/ estático + micro-lab Ciclo 1 validado (labs/ciclo-1-fundamentos) |
| B | Frontend React/Next/PWA | DISCOVERED | 1 | Projetos/Rob-Trader usa React 19+Vite 7+TS 5.9; Node ausente (bloqueio) |
| C | TypeScript | DISCOVERED | 1 | Padrões TS no vault; runtime Node ausente |
| D | UI/UX (usabilidade, sistemas de design) | DISCOVERED | 1 | EcoDashboard, WindowGUI, www/; sem labs |
| E | Animação/Gráficos WebGL/Three.js/WebGPU | DISCOVERED | 1 | docs/grafo.html existe; WebGPU não testado |
| F | Backend Web (servidores, rotas, APIs) | VALIDATED | 3 | micro-lab Ciclo 2 validado (14 checks OK, labs/ciclo-2-backend-estruturado); ADR-003; micro-lab Ciclo 3 WS (6 checks OK, labs/ciclo-3-websocket); ADR-004; Ciclo 1 (servidor stdlib + JSON) validado |
| G | Banco (PostgreSQL/Redis) | UNKNOWN | 0 | Não verificado; sqlite3 disponível via stdlib |
| H | IA/LLM/RAG aplicada em web | VALIDATED | 3 | Ecossistema usa IA real (cognitive_core, agents, MCP); realtime web com estado do runtime validado (Ciclo 3, /estado); chat web ligado ao cognitive_core validado (Ciclo 4, 11 checks OK, labs/ciclo-4-ia-chat); timeout da busca MCP corrigido (09/09, -32603 eliminado; add-memory 120s, get-memory-context 30s, lock 120s); RAG segue como trabalho em aberto, sem blocker técnico |
| I | Segurança OWASP | UNDERSTOOD | 2 | Skills mcp-desenvolvimento (secure-coding, threat-modeling, security-review); sem labs |
| J | Performance / Core Web Vitals | DISCOVERED | 1 | Skill performance-testing existe; nenhuma métrica medida |
| K | DevOps (deploy, CI/CD, Docker) | UNDERSTOOD | 2 | Docker ausente; CI via GitHub Actions em uso; skill ci-cd-pipeline |
| L | Arquitetura (SOLID, Clean, event-driven) | UNDERSTOOD | 3 | ADRs prévios da missão (ADR-001..010 planejados); decisões web pendentes |

## Regras de atualização

1. Todo item só sobe de status/nível com evidência em `conhecimento/web/labs/`.
2. Toda decisão de arquitetura vira ADR em `conhecimento/web/adrs/` (formato template-decisao).
3. Status revertido para DISCOVERED se evidência ficar obsoleta (runtime removido, stack trocada).
4. GitHub permanece como rede de segurança; persistência via gate `persistencia.ps1`.

## Pendências conhecidas

- Node.js/npm ausentes — bloqueia B, C, Next, runtimes TS (decisão externa ao ecossistema).
- FastAPI/Flask não instalados — F usa stdlib+websockets por ora (ADR-003/004); uvicorn puro adiado para Ciclos 5+.
- Docker ausente — K por ora via GitHub Actions.
- Busca MCP mcp-memoria com timeout (-32603) em `mcp-memoria buscar`; usar read direto. (CORRIGIDO 09/09: timeouts realinhados e lock concorrente de memória com espera 120s; add-memory validado ao vivo — memoria 98318.)
- software de memoria `memory_engine.py add` com hang latente (>120s) — registrar via arquivos.