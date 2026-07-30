# Auditoria Arquitetural — Jarvis (Vox UmGrau)

> **Data:** 2026-07-29
> **Escopo:** Bridge (`jarvis_bridge.py`) + Android App (`VoxUmGrau`) + Ecossistema de suporte
> **Versão APK:** 1.0.0 (versionCode=3)
> **Arquitetura de referência:** 7 camadas funcionais

---

## 1. Percepção — Como o Jarvis "ouve" e "enxerga"

### ✅ Implementado
- **Speech-to-text offline**: Android `SpeechRecognizer` com português brasileiro (`VoxStt.kt:62-67`)
- **Audio focus management**: `AudioFocusRequest` com `AUDIOFOCUS_GAIN_TRANSIENT` para STT (`VoxStt.kt:52-60`)
- **Input por texto**: `OutlinedTextField` no Android + envio via `ws.send()` (`VoxChatScreen.kt:147-154`)
- **Reconexão automática**: WebSocket com backoff exponencial (2s-30s) (`VoxWebSocket.kt:64-79`)
- **WebSocket listener**: Recepção de mensagens JSON do servidor (`VoxWebSocket.kt:45-48`)

### 🔧 Em desenvolvimento
- Indicação visual de volume RMS (callback `onRmsChanged` existe mas não usado na UI)

### ❌ Não implementado
- **Visão computacional**: câmera, detecção de objetos em tempo real, OCR para ler placas/documentos
- **Leitura de sensores do dispositivo**: localização (GPS), movimento (acelerômetro), luz ambiente, proximidade
- **Ingestão de dados externos**: clima automático, calendário, notificações do sistema Android, alarmes
- **Reconhecimento de emoção na voz**: tom, velocidade, estresse do usuário
- **Identificação de locutor**: diferenciar vozes de múltiplos usuários
- **Processamento de áudio ambiente**: detectar música, alarmes, campainha, notificações sonoras
- **STT contínuo**: atualmente single-utterance (precisa reativar manualmente a cada fala)

### 📊 Cobertura: **20%**
> STT básico funcional, mas sem visão, sensores, ingestão externa, ou identificação de contexto ambiental.

---

## 2. Cognição — Como o Jarvis "pensa"

### ✅ Implementado
- **LLM integrado**: `opencode/deepseek-v4-flash-free` via CLI (`jarvis_bridge.py:196`)
- **Fallback automático**: `@razroo/opencode-model-fallback` (429/5xx → próximo modelo)
- **Ferramentas completas**: edit, write, bash, grep, glob, read, webfetch, websearch
- **17 agentes OpenCode**: Maestro, Estrategista, Cético, Realista, Ética, Futuro, Recursos, Criativo, Revisor, Executor, Aprendizado, LER-Executor, Parallel-Planner, etc.
- **SDLC Gates**: G1-G5 com critérios formais de evidência
- **Roteamento de agentes**: Maestro decide Rota A (OpenCode), B (LER), ou C (Híbrido)
- **LER Runtime completo**: 17 agentes internos com 13 camadas de governança
- **MCP Server**: eco-knowledge para busca semântica e consulta de memória
- **System prompt rico**: `JARVIS_SYSTEM.md` (359 linhas) com conhecimento completo do ecossistema
- **Conhecimento técnico atualizado**: OpenCode v1.18.9, agentes, plugins, providers, paths
- **Estado dinâmico**: bridge injeta resumo do ecossistema a cada requisição
- **Modo continuação**: `-c` flag para manter contexto entre mensagens (`jarvis_bridge.py:197-198`)

### 🔧 Em desenvolvimento
- Rota C (Híbrido OpenCode + LER) com delegação automática para tarefas complexas
- Planejamento multi-etapas com persistência entre execuções

### ❌ Não implementado
- **Raciocínio visual**: interpretar imagens, diagramas de arquitetura, screenshots de UI
- **Decomposição recursiva**: quebrar tarefas complexas em sub-tarefas automaticamente
- **Raciocínio temporal**: agendar ações para futuro, timers, lembretes baseados em tempo
- **Raciocínio probabilístico**: estimar confiança da resposta, múltiplas hipóteses
- **Contexto entre conversas**: atualmente limitado ao histórico no `conversa_unica.json`

### 📊 Cobertura: **55%**
> LLM + agentes + ferramentas robustos, sem raciocínio visual ou planejamento recursivo.

---

## 3. Memória — Como o Jarvis "lembra"

### ✅ Implementado
- **Memória de curto prazo**: `conversa_unica.json` (até 50 pares) compartilhado entre CLI e app (`jarvis_bridge.py:239-250`)
- **Ebbinghaus decay**: 6 tipos de memória com half-life específico (`memory_engine.py:13-20`)
  - `erro`: 90 dias | `padrao`: 60 dias | `decisao`: 30 dias
  - `contexto`: 14 dias | `episodio`: 7 dias | `preferencia`: 365 dias
- **Persistência entre sessões**: `memories.json` + `index.json` + sessions JSONL
- **Knowledge graph**: `knowledge_graph.json` (~120KB) com 248+ entradas (padrões, decisões, bugs)
- **Busca semântica BM25**: `search_knowledge.py` com 4 fontes (KG + memória + notas + skills)
- **MCP de conhecimento**: servidor com 3 tools (search-knowledge, get-memory-context, add-memory)
- **Reforço por acesso**: `reinforce(id, delta=0.15)` no memory_engine
- **Decay pass**: arquivamento automático de memórias com score < 0.01
- **Obsidian vault**: 268 notas geradas a partir do knowledge graph
- **CONHECIMENTO.md**: exportado e carregado no contexto de todo agente

### 🔧 Em desenvolvimento
- Integração do Memory Engine com o fluxo do bridge (atualmente não chamado nas conversas)
- Histórico de pronúncias corrigidas (pronuncias.json: 192 palavras)

### ❌ Não implementado
- **Banco vetorial**: embeddings densos para busca semântica (apenas BM25 lexical)
- **Sumarização automática**: condensar conversas longas em memórias episódicas
- **Perfil de usuário persistente**: preferências de tom, velocidade TTS, temas, histórico por usuário
- **Memória procedural**: aprender padrões de interação e comandos frequentes do usuário
- **Tagging automático**: categorização de memórias sem intervenção manual
- **Reconciliação de memórias conflitantes**: detectar quando nova info contradiz memória existente

### 📊 Cobertura: **50%**
> Boa base (KG + BM25 + Ebbinghaus), sem embeddings densos, perfil de usuário, ou sumarização episódica.

---

## 4. Ação — Como o Jarvis "age"

### ✅ Implementado
- **Edição de arquivos**: write, edit no ecossistema (`JARVIS_SYSTEM.md:169-175`)
- **Execução de código**: bash + Python + PowerShell via ferramentas OpenCode
- **Git operations**: commit, push, pull via ecosystem.ps1 e comandos bash
- **Compilação Android**: `build.ps1 -Install` com versionamento automático
- **OpenCode serve**: gerenciamento do servidor headless (`start_serve.py`)
- **Pesquisa web**: webfetch e websearch para informação online
- **MCP tools**: 3 tools via eco-knowledge server
- **Modificação de configs**: opencode.jsonc, plugins, agents, skills

### 🔧 Em desenvolvimento
- GitHub PRs automatizados via GitHub CLI (`gh`)

### ❌ Não implementado
- **Envio de mensagens**: WhatsApp, Telegram, SMS, email — zero integração
- **Controle de smart home**: luzes, temperatura, dispositivos IoT (Lâmpadas, tomadas, câmeras)
- **APIs externas de terceiros**: Spotify (música), Google Calendar (agenda), Uber (transporte), Mercado Livre
- **Agendamento de tarefas**: executar ações em horário específico ou com timer
- **Controle de mídia local**: play/pause música no PC ou celular, controle de volume
- **Ações multi-dispositivo**: coordenar PC + celular + smart home simultaneamente
- **Compartilhamento de tela / arquivos**: enviar documentos, prints, logs para o usuário

### 📊 Cobertura: **35%**
> Bom controle do ecossistema local de desenvolvimento, sem absolutamente nenhuma integração com o mundo externo (mensagens, IoT, APIs de terceiros).

---

## 5. Avaliação — Como o Jarvis se "autocorrige"

### ✅ Implementado
- **Retry automático na bridge**: se `-c` falha, tenta sem continuação (`jarvis_bridge.py:222-224`)
- **Retry com tool context**: se resposta vazia, monta novo prompt com últimos tool outputs (`jarvis_bridge.py:226-230`)
- **Fallback de modelo**: plugin `@razroo/opencode-model-fallback` com cooldown 60s
- **Timeout de requisição**: 300s no bridge (`jarvis_bridge.py:195`), 30s TTFT no fallback
- **Watchdog**: `watchdog.ps1` monitora bridge a cada 20s, reinicia se cair (porta 8765)
- **System Guardian**: monitora RAM a cada 20s, mata processos se memória < 500MB
- **Preflight check**: `preflight_check.py` valida config MCP/plugins antes de deploy
- **SDLC Gates**: 5 gates formais (G1-G5) no fluxo de tarefas OpenCode
- **Logging**: bridge_log.txt, serve_log.txt, guardian_log.txt, watchdog_log.txt
- **Tratamento de erros TTS**: fallback para texto se áudio falha (`jarvis_bridge.py:360-365`)
- **Tratamento de erros WebSocket**: conexão fechada tratada graceful (`jarvis_bridge.py:366-367`)
- **Limpeza de sessão**: se prompt > 30K chars, força limpeza do histórico (`jarvis_bridge.py:277-281`)

### 🔧 Em desenvolvimento
- Nada — todos os mecanismos de avaliação são reativos, não proativos

### ❌ Não implementado
- **Feedback loop do usuário**: botão "útil/não útil" nas respostas para aprendizado
- **Self-healing automático**: detectar e corrigir problemas sem intervenção (ex: config corrompida)
- **Testes automatizados da bridge**: test scripts existem mas não são executados periodicamente
- **Monitoramento de qualidade**: taxa de acerto, precisão, relevância das respostas
- **Detecção de alucinação**: validar fatos contra knowledge graph antes de responder
- **Análise de sentimento**: detectar frustração do usuário e ajustar tom
- **A/B testing**: comparar respostas com diferentes configurações/modelos
- **Alertas proativos**: notificar quando bridge cai, RAM crítica, latência alta

### 📊 Cobertura: **40%**
> Retry + watchdog + guardian funcionais, sem feedback loop, auto-healing, ou monitoramento proativo de qualidade.

---

## 6. Interface — Como o Jarvis "se comunica"

### ✅ Implementado
- **TTS servidor**: `edge-tts pt-BR-ThalitaMultilingualNeural` com pitch -30Hz (`jarvis_bridge.py:15-16`)
- **TTS Android local**: `TextToSpeech` com voz masculina (pitch 0.65, rate 0.85) (`VoxTts.kt:30-31`)
  - **Dual TTS**: servidor gera áudio base64 para respostas longas; Android TTS funciona como fallback
- **Reprodução de áudio**: `MediaPlayer` com arquivo temporário MP3 (`VoxAudioPlayer.kt:13-38`)
- **Interface de chat**: `VoxChatScreen` com Jetpack Compose, mensagens alinhadas por origem
- **Correção de pronúncia**: `pronuncias.json` com 192 palavras mapeadas (`jarvis_bridge.py:134-141`)
- **Indicadores de status**: Conectado, Online, Processando, Ouvindo, status de erro (`VoxChatScreen.kt:81-90`)
- **Notificação persistente**: `VoxForegroundService` com notification channel (`VoxForegroundService.kt:12-26`)
- **Configuração de host**: campo de IP configurável na UI (`VoxChatScreen.kt:100-113`)
- **Copiar texto**: toque em mensagem copia para área de transferência (`VoxChatScreen.kt:38-42`)
- **Scroll automático**: `animateScrollToItem` quando nova mensagem chega (`VoxChatScreen.kt:66-70`)

### 🔧 Em desenvolvimento
- Indicador RMS do microfone (callback existe, não conectado à UI)

### ❌ Não implementado
- **Interface web dashboard**: histórico acessível pelo navegador, estatísticas de uso, configuração remota
- **Widgets Android home screen**: atalho rápido para falar com Jarvis sem abrir o app
- **Notificações proativas**: Jarvis iniciar conversa (alarme, lembrete, alerta), não apenas responder
- **Streaming de áudio progressivo**: atualmente áudio completo via base64 — lento para respostas longas
- **Suporte multi-idioma**: interface apenas em português
- **Tema customizável**: dark/light mode, cores, tamanho de fonte, acessibilidade
- **Modo mãos-livres**: resposta apenas por voz sem interação visual
- **Comandos de voz em background**: "Hey Jarvis" detection sem abrir o app
- **Histórico pesquisável**: buscar em conversas anteriores dentro do app

### 📊 Cobertura: **40%**
> Voz + chat + notificação funcionais, sem dashboard web, widgets, streaming de áudio, ou modo mãos-livres.

---

## 7. Infraestrutura — O que sustenta tudo

### ✅ Implementado
- **Bridge WebSocket**: `jarvis_bridge.py` standalone na porta 8765
- **OpenCode Serve**: headless na porta 18765 com health check
- **Autenticação**: Basic Auth no serve (`start_serve.py:20-21`)
- **Rede segura**: Tailscale (PC: 100.120.67.64, Phone: 100.64.71.9)
- **Watchdog**: auto-reinício da bridge a cada 20s
- **System Guardian**: gestão de RAM (crítico < 200MB, alerta < 500MB)
- **Logs estruturados**: bridge_log.txt, serve_log.txt, guardian_log.txt, watchdog_log.txt
- **CI/CD**: GitHub Actions (eco-sync + report)
- **Scheduled Task**: EcoSystemVigilante inicia no logon do Windows
- **Versionamento**: `ecosystem sync` → pull + push em todos os repos
- **Gestão de credenciais**: `.env` com variáveis sensíveis, carregado via python-dotenv
- **Plugin de fallback**: cadeia de modelos (@razroo/opencode-model-fallback v0.3.2)
- **Profile PowerShell**: funções `start-vigilante`, `stop-vigilante`, `status-vigilante`, `ecosystem`
- **Variáveis de ambiente**: OPENCODE_SERVER_USERNAME, OPENCODE_SERVER_PASSWORD, NVIDIA_API_KEY, OPENAI_API_KEY

### 🔧 Em desenvolvimento
- Métricas de latência por requisição (log manual, não automático)

### ❌ Não implementado
- **Banco de dados centralizado**: toda persistência é em JSON/JSONL — sem SQLite, sem índices, sem queries
- **Monitoramento proativo**: alertas via Telegram/email quando bridge cai, RAM crítica, latência alta
- **Dashboard de performance**: latência média por requisição, tokens usados, custo por modelo, uptime
- **Cache de respostas frequentes**: perguntas repetidas geram nova inferência toda vez
- **Backup automático**: knowledge graph, memories.json sem snapshot automático
- **Load balancing**: apenas 1 bridge — se cair, todo o serviço cai até watchdog reiniciar
- **Deploy automatizado do APK**: CI/CD não compila nem distribui o app Android
- **Gestão de custo de API**: sem tracking de tokens, sem alerta de gasto excessivo
- **Health check remoto**: sem endpoint externo para verificar status do ecossistema remotamente

### 📊 Cobertura: **45%**
> Bridge + watchdog + guardian + git sync sólidos, sem banco de dados, monitoramento proativo, ou dashboard.

---

## Cobertura Total Estimada

| Camada | Cobertura | Status |
|--------|-----------|--------|
| 1. Percepção | **20%** | ❌ Crítica |
| 2. Cognição | **55%** | ✅ Boa |
| 3. Memória | **50%** | ✅ Mediana |
| 4. Ação | **35%** | ❌ Fraca |
| 5. Avaliação | **40%** | ⚠️ Mediana |
| 6. Interface | **40%** | ⚠️ Mediana |
| 7. Infraestrutura | **45%** | ⚠️ Mediana |
| **Total** | **~41%** | **⚠️ 7 camadas sub-50%** |

> **Média ponderada simples: 41%.** Nenhuma camada atinge 60%. As 3 camadas de saída (Ação, Interface, Infraestrutura) estão abaixo de 50%, indicando que o Jarvis é forte em "pensar" mas fraco em "agir" e "se comunicar com o mundo".

---

## Top 3 Lacunas Mais Críticas

### 1. Percepção — Zero visão e sensores (Cobertura: 20%)
**Impacto:** Jarvis é cego e surdo para o ambiente. Não pode ler uma placa, identificar um objeto, saber onde o usuário está, detectar se o usuário está falando com outra pessoa, ou receber notificações do sistema automaticamente. Cada interação precisa ser iniciada manualmente pelo usuário com o app aberto.

**O que falta de mais relevante:**
- Câmera → OCR para ler documentos, código, placas
- GPS → contexto de localização para respostas geográficas
- Notificações → reagir a mensagens, alarmes, lembretes sem intervenção do usuário

### 2. Ação — Zero integração com o mundo externo (Cobertura: 35%)
**Impacto:** Jarvis pode modificar arquivos e rodar código no PC, mas não pode enviar uma mensagem, agendar um compromisso, tocar uma música, controlar uma luz, ou chamar um Uber. O usuário está limitado a interagir com o ecossistema de desenvolvimento — nada além disso.

**O que falta de mais relevante:**
- API WhatsApp/Telegram → comunicação assíncrona com o usuário
- Google Calendar API → agendar eventos, verificar compromissos
- Spotify API → controle de música por voz
- Controle IoT (Lâmpada Wi-Fi, tomada smart) → automação residencial básica

### 3. Avaliação — Sem feedback loop nem auto-healing (Cobertura: 40%)
**Impacto:** Jarvis não melhora com o uso. Se dá uma resposta errada, não há mecanismo para o usuário sinalizar e o sistema aprender. Se a config quebra, watchdog só reinicia — não diagnostica nem corrige. A qualidade não melhora automaticamente.

**O que falta de mais relevante:**
- Botão "útil/não útil" no app → aprender preferências do usuário
- Validação automática de ferramentas → detectar falhas silenciosas no output de comandos
- Auto-healing → se MCP server cair, bridge tentar reiniciar antes de falhar

### Dependência cruzada entre lacunas
| Lacuna | Bloqueia | Efeito |
|--------|----------|--------|
| Percepção (sem visão) | Ação (não pode agir sobre o que vê) | Impede automações visuais |
| Percepção (sem sensores) | Cognição (não tem contexto ambiental) | Respostas sem noção de lugar/tempo |
| Avaliação (sem feedback) | Cognição (não melhora) | Mesmos erros repetidos |
| Infraestrutura (sem DB) | Memória (escala limitada) | 248 entradas no KG, mas sem query eficiente |

---

## Prioridade para Próximos 3 Ciclos

### Ciclo 1 — Ação: Integrações externas
**O que implementar:**
- API de clima (OpenWeatherMap ou similar) → resposta contextual de temperatura
- API de envio de mensagem (Telegram Bot) → comunicação assíncrona com o usuário
- Comando de música (YouTube Music ou Spotify) → tocar/pausar por voz

**Justificativa:** Maior impacto percebido. O usuário sente a diferença imediatamente — perguntar o clima e receber resposta, ou pedir para Jarvis mandar uma mensagem. Isso transforma Jarvis de "ferramenta de dev" para "assistente pessoal". Baixa complexidade técnica (todas têm APIs REST bem documentadas).

### Ciclo 2 — Percepção: Visão + sensores
**O que implementar:**
- Câmera no app Android → capturar foto e enviar para análise (OCR + descrição)
- GPS → injetar localização no contexto do prompt automaticamente
- Notificações do Android → Jarvis reagir a eventos do sistema (alarme, mensagem recebida)

**Justificativa:** Abre categorias de uso completamente novas. Ler um documento, identificar um produto, saber onde o usuário está. Depende do Ciclo 1 (precisa de APIs de ação para usar o resultado da visão).

### Ciclo 3 — Avaliação: Feedback + auto-healing
**O que implementar:**
- Botão de feedback no app (útil/não útil) → reforçar memória positiva/negativa
- Validação de output de ferramentas → detectar erros silenciosos
- Self-healing da bridge → se erro de config, restaurar backup automático

**Justificativa:** Maturidade e confiabilidade. Depois de ter ação e percepção, o sistema precisa aprender com erros e se manter estável sem intervenção manual. Depende dos Ciclos 1-2 (feedback só faz sentido quando o sistema faz coisas úteis).

---

## Riscos Técnicos e Dependências Cruzadas

### Dependências frágeis
| Dependência | Risco | Mitigação |
|-------------|-------|-----------|
| `edge-tts` via Microsoft Edge | TTS offline se Edge não estiver instalado ou atualizado | Fallback para TTS Android local já implementado |
| `opencode/deepseek-v4-flash-free` | Modelo gratuito pode ser descontinuado ou rate-limited | Fallback chain (nvidia/deepseek-v3.1) já configurada |
| Tailscale para conectividade | Se Tailscale cair, app Android não conecta | Sem fallback atualmente — precisa de relay público |
| `conversa_unica.json` como histórico | Corrupção do JSON derruba contexto inteiro | Try/except com fallback para `[]` + backup implícito |
| WebSocket sem TLS | Tráfego de áudio e texto em texto puro na Tailscale | Tailscale já criptografa a rede, mas sem TLS no WebSocket |
| Dependência de Python 3.12 + bibliotecas | Pip install pode falhar em PC novo | `setup.bat` resolve dependências automaticamente |

### Latência e gargalos
| Gargalo | Medido | Impacto |
|---------|--------|---------|
| Boot do opencode | ~10s por requisição | Cada query paga 10s de cold start |
| Inferência do modelo | 10-30s | Respostas simples demoram 20-40s no total |
| TTS edge-tts (texto longo) | 10-20s para 500+ chars | Respostas longas têm latência adicional |
| Áudio base64 completo vs streaming | Áudio completo enviado só após geração total | Usuário espera tudo gerar antes de ouvir |
| Bridge single-thread | 1 requisição por vez (asyncio single event loop) | Segunda requisição bloqueia até primeira terminar |

### Custo
| Item | Custo atual | Risco |
|------|------------|-------|
| Modelo deepseek-v4-flash-free | **Gratuito** | Risco zero — continuar usando |
| NVIDIA API (fallback) | **Gratuito** (modelos free) | Rate limits podem aumentar |
| edge-tts | **Gratuito** | Sem custo, depende do Edge local |
| Tailscale | **Gratuito** (3 usuários) | Dentro do limite |
| GitHub | **Gratuito** (público) | Sem risco |

### Gargalos de infraestrutura
| Gargalo | Impacto | Necessário |
|---------|---------|------------|
| RAM 8GB (79-90% uso) | Guardian mata processos opencode frequentemente | 16GB+ ou otimizar consumo |
| JSON como banco | Sem concorrência, sem índices, sem queries | SQLite ou banco vetorial |
| Bridge single-instance | Sem HA, sem failover | Múltiplas bridges + load balancer |
| Logs em arquivo plano | Sem rotação, sem busca | Log rotation ou centralizado |
| Sem health check externo | Não detectável se cair | Endpoint HTTP público simples |

---

> **Resumo executivo:** Jarvis é um **assistente de voz especializado em engenharia de software** com cognição forte (LLM + agentes + ferramentas) mas **percepção e ação muito limitadas**. A cobertura geral de 41% reflete um sistema que "pensa bem" mas "não vê, não sente, e não age no mundo real". O maior salto de valor percebido virá de integrar APIs externas (clima, mensagens, música), seguido de visão (câmera) e depois maturidade (feedback loop + auto-healing).
