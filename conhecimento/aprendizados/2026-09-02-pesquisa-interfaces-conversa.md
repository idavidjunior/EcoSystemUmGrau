---
tipo: padrao
tags: [pesquisa, interfaces, conversa, hermes, openwebui, chat, ux, arquitetura]
data: 2026-09-02
contexto: >
  Usuário autorizou pesquisa contínua em segundo plano sobre como Hermes (Nous
  Research) e outros projetos desenvolveram suas interfaces de conversa (arquitetura,
  UX, padrões de diálogo). Trabalho silencioso e constante, sem pedir, acumulando
  material em aprendizado.
decisao: >
  Acumular conhecimento sobre arquitetura e UX de interfaces de conversa a partir
  de Hermes Agent e Open WebUI, destacando padrões reutilizáveis para o ecossistema.
impacto: >
  Material pronto para quando o usuário retomar o assunto de interfaces de conversa.
---

# Pesquisa — Interfaces de Conversa (Hermes e outros)

## Hermes Agent (Nous Research)

Hermes é um agente com loop de aprendizado embutido; interface primária é TUI
(terminal), com gateway para Telegram/Discord/Slack/WhatsApp/Signal e API server
OpenAI-compatível. Licença MIT.

### Filosofia de interface
- CLI é um TUI completo (não web UI): edição multilinha, autocomplete de
  slash-command, histórico de conversa, interromper-e-direcionar, streaming.
- TUI moderno com modais, seleção por mouse e input não-blocante (`hermes --tui`).
- "Vive onde você está": um único processo gateway atende várias plataformas.
- Continuidade cross-platform de conversa.

### Comandos/sessão (padrões)
- `hermes` (interativo), `hermes chat -q "..."` (query única), `--query-file` (input verbatim).
- `-c`/`--continue` retoma sessão; `-c` é terminal-aware (breadcrumb por terminal:
  tmux pane, wezterm pane, etc.) — cada terminal continua sua própria conversa.
- `--resume <session_id>` / `latest`; `--model`, `--provider`, `--toolsets`, `-s` (skills).
- `-w` isola git worktree (agentes paralelos).
- Sessões em SQLite; títulos auto-gerados (3-7 palavras, LLM auxiliar em background,
  sem adicionar latência); `/title`, `/new`, `/reset`.
- Recursos: `/bg` (background tasks, entrega quando termina), quiet mode, bell on complete.
- Issue #641: `/new` vs `/reset` são confusos — combinar/clarificar (UX real).

### API server (OpenAI-compatível, porta 8642)
- Um backend cobre modelos + ferramentas; frontends falam formato OpenAI.
- Endpoint `POST /v1/chat/completions`: stateless, conversa completa no `messages`.
- Endpoint `POST /v1/responses`: estado server-side via `previous_response_id`
  (multi-turn preservado, tool calls gravados). Conversas nomeadas com `conversation`.
- Streaming SSE; evento custom `hermes.tool.progress` para progresso de tool
  sem poluir o texto persistido do assistente.
- `POST /v1/runs`: runs de longa duração, sessão, `Idempotency-Key`, `stop` e
  `approval` (aprovação humana de tool call gated — mesmo conceito do nosso gate).
- Sessions API REST: listar/criar/renomear/deletar/`fork`/`chat`/`chat/stream`.
- `/v1/skills` e `/v1/toolsets`: descoberta determinística de capacidades.
- `X-Hermes-Session-Key`: escopo estável de memória de longo prazo por usuário.
- System prompt do frontend é camadas EM CIMA do prompt core (não substitui).
- Segurança: `API_SERVER_KEY` obrigatório, CORS off por padrão, allowlist.

### Padrões relevantes para o ecossistema
- TUI com streaming de tool output e progresso inline.
- Um gateway único servindo múltiplas plataformas/superfícies.
- Sessões persistentes com retomada e auto-titulação.
- Aprovação humana de tools (approval) — alinha com nosso gate de veto.
- API OpenAI-compatível para plugar frontends prontos (Open WebUI, LobeChat, etc.).

## Open WebUI

Interface web de chat para LLMs (SvelteKit), "uma interface para todo modelo",
privada, extensível, para times. 126k+ stars (fonte Hermes), comunidade ativa.

### Filosofia/arquitetura
- "A conversa é o coração": um chat lê documentos, busca web, fala/ouve, gera
  imagem, lembra e chama seus próprios modelos. Capacidades plugam na mesma conversa.
- Stateless, container-first; escala horizontal; Redis-backed sessions, multi-worker.
- OpenTelemetry; PostgreSQL p/ multi-instance; vector DB externo (PGVector, Milvus,
  Qdrant, ChromaDB).
- Frontend: SvelteKit, routing hierárquico, stores Svelte reativas para estado.

### Chat features (UX)
- Folders & Projects (folders viram workspaces com system prompt + conhecimento).
- URL parameters p/ configurar sessão.
- Chat Parameters em níveis (per-chat/per-account/per-model).
- Autocomplete de prompt (AI text prediction via task model).
- Chat sharing (local ou comunidade, com privacidade).
- Response auto-scroll.
- Default upload mode: "Focused Retrieval" (chunk+search) vs "Entire Document".
- Fork a chat (branch de conversa em cópia independente).
- Editar/regenerar mensagens; renderização LaTeX, tabela, mermaid, code highlight.
- Actions: botões customizáveis na toolbar de resposta (gatilho de tarefas,
  consentimento deliberado do usuário — mantém autonomia).
- Plugin architecture; BYOF (bring your own function) em Python puro; pipelines.

### Descobertas/padrões
- Paper arXiv 2510.02546: Open WebUI como interface aberta/extensível/usable.
  Três considerações de design: executar e configurar modelos abertos; interface
  customizável; ações botão para interação além do texto.
- Design considerations para hosts de LLM: openness (escolher modelo por
  capacidade e valores); interface customization (temas, presets); actions de consentimento.

## Referências coletadas
- https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server
- https://hermes-agent.nousresearch.com/docs/user-guide/cli/
- https://hermes-agent.nousresearch.com/docs/user-guide/sessions/
- https://github.com/NousResearch/hermes-agent
- https://github.com/topics/conversational-ai (rasa, assistant-ui, nlp.js, wechaty)
- https://docs.openwebui.com/features , https://docs.openwebui.com/features/chat-conversations
- https://arxiv.org/html/2510.02546v1 (Open WebUI paper)
- https://github.com/open-webui/open-webui
- https://poornaprakashsr.medium.com/5-best-open-source-chat-uis-for-llms-in-2025-11282403b18f

## Próximos passos (contínuo, autônomo)
- Aprofundar Rasa (RL/conversacional), assistant-ui (React), LobeChat, padrões de UX de chat.
- Eventualmente montar spec/mapa mental/estrutura quando o usuário voltar ao assunto.

## Conexoes

- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]