# Base de Conhecimento — Exportacao Completa

**Exportado em:** 2026-09-02T09:49:27.258321
**Projetos:** 4
**Padroes Tecnicos:** 291
**Decisoes:** 87
**Bug Fixes:** 52
**Padroes Cognitivos:** 78
**Heuristicas:** 32
**Frameworks:** 10
**Missoes Aprendidas:** 134

---

## Como Usar Esta Base de Conhecimento

Esta base contem **conhecimento cognitivo e tecnico** acumulado entre projetos.
Ela e organizada em 3 niveis:

1. **Conhecimento Tecnico** — Padroes de codigo, pipelines de build, decisoes arquiteturais, bug fixes
2. **Conhecimento Cognitivo** — Heuristicas de debugging, frameworks de raciocinio, estrategias validadas
3. **Meta-Conhecimento** — Como a propria base e estruturada e auto-melhorada

---

## Decisoes Arquiteturais

### LER usa Python puro (stdlib only) — zero dependencias externas intencionalmente.
**Fonte:** ler_arquitetura
Portabilidade maxima, sem conflitos de versao, instalavel em qualquer ambiente com Python.

### Estado persiste em JSON (nao SQLite) — legivel, editavel fora do LER, sem migrations.
**Fonte:** ler_arquitetura
Mesma razao do Android Pure SDK: JSON e human-readable, debuggavel, versionavel no git.

### Checkpoints salvos antes de cada iteracao — sobrevive a crash a qualquer momento.
**Fonte:** ler_arquitetura
Missao nunca recomeca do zero. restart/resume carrega ultimo checkpoint viavel.

### Pontuacao ponderada com 6 categorias (Req 30%, Func 30%, Testes 10%, DoD 10%, Evidencias 10%, Auditoria 10%).
**Fonte:** ler_arquitetura
DoD granular com dod_satisfaction forcando verificacao de git commit + passos completados.

### Estrategia selecionada por ranking (cost + risk + time + complexity + success_probability).
**Fonte:** ler_arquitetura
Estrategias falhas nunca repetidas sem alteracoes. Forca variacao de abordagem.

### Supervisor monitora todos os modulos individualmente — nunca reinicia missao inteira por falha de um modulo.
**Fonte:** ler_arquitetura
Isolamento de falha: se o validator falha, recupera so o validator, nao o planner.

### Metadata busca em multi-fontes: AcoustID -> iTunes BR -> MusicBrainz -> iTunes US fallback.
**Fonte:** mp3player
AcoustID falha sempre (API key invalida), mas e aceito — fallback natural para iTunes/MusicBrainz.

### SearchMode.NORMAL -> RELAXED auto-fallback se NORMAL retorna null.
**Fonte:** mp3player
RELAXED usa thresholds mais baixos e queries mais amplas (title-only, artist-only).

### Album art download com redirect loop manual (instanceFollowRedirects=false).
**Fonte:** mp3player
Cover Art Archive retorna 302 para archive.org, que falha com FileNotFoundException sem loop explicito.

### Single Activity com FrameLayout + visibilidade (setVisibility) — sem Fragments.
**Fonte:** android_pure_sdk
Suficiente para ate 5 telas, mais simples, sem dependencias de suporte.

### Form Starts Empty — input forms nunca auto-carregam arquivo ao trocar de aba.
**Fonte:** android_pure_sdk
Usuario espera blank slate em formularios. Carga explicita via file browser.

### Salvar cria novo arquivo timestampado, nunca sobrescreve existente.
**Fonte:** android_pure_sdk
Preserva historico. Nao ha 'overwrite' no design — cada salvamento e um snapshot.

- **Why:** d8 doesn't accept directory trees of .class files; it needs a JAR. This is a historical Android toolchain require** (fonte: android-pure-sdk)
- **Why
- User expects a blank slate when entering a form tab, consistent with "new calculation" mental model** (fonte: android-pure-sdk)
- ****StringBuilder for price** — Fine-grained control over display format, avoids floating-point display issues** (fonte: android-pure-sdk)
- ****Merge by name** — If name matches existing item, increment quantity instead of duplicating; NEVER merge unnamed items** (fonte: android-pure-sdk)
- ****Form Starts Empty** — Input forms never auto-load from file; user loads explicitly via file browser** (fonte: android-pure-sdk)
- ****Salvar = new file** — Explicit save creates timestamped snapshot, never overwrites existing saved files** (fonte: android-pure-sdk)
- ****`-encoding UTF-8` in javac** — Required on Windows to prevent corrupted Portuguese characters (ç, ã, é, etc.)** (fonte: android-pure-sdk)
- ****Step 0: AcoustID fingerprint** — `AcoustIDService.searchByFile()` — almost always fails because API key `4m9Q2k9p` is ** (fonte: mp3player-metadata-rescue)
- **Calls `searchOnline(SearchMode.RELAXED)` — uses relaxed thresholds and also tries title-only / artist-only queries** (fonte: mp3player-metadata-rescue)
- **User taps "Buscar na Internet"** (fonte: mp3player-metadata-rescue)
- **If RELAXED also fails → user sees "Tente editar manualmente os campos e buscar novamente"** (fonte: mp3player-metadata-rescue)
- **The issue description and root cause** (fonte: mp3player-metadata-rescue)
### Chaves API exclusivamente em env vars (NVIDIA_API_KEY, OPENAI_API_KEY, etc.)
**Fonte:** sessao_seguranca
Config files podem ser commitados ou expostos; env vars sao seguras e isoladas por sessao

### Server health check via HTTP ping (localhost:porta) em vez de stdin/stdout
**Fonte:** sessao_servermanager
HTTP permite verificar se processo esta vivo mesmo com threads ocupadas; mais confiavel

### Salvar RustDesk password e ID em local permanente, nao gerar OTP
**Fonte:** sessao_rustdesk
Acesso remoto previsivel requer credenciais fixas, nao one-time tokens que mudam

### Priorizar data-testid sobre classes CSS em automacao web
**Fonte:** treinamento_navegacao
data-testid e o unico atributo projetado exclusivamente para automacao; classes CSS mudam com refactors de estilo, IDs sao frequentemente dinamicos

### Usar coordenadas relativas (porcentagem) em vez de absolutas para gestos mobile
**Fonte:** treinamento_navegacao
Dispositivos Android tem resolucoes variadas; coordenadas relativas adaptam-se automaticamente sem recalculo manual

### Preferir AutomationId sobre Name em UI Automation Windows
**Fonte:** treinamento_navegacao
Name de controles Windows muda com idioma do sistema operacional e versoes do app; AutomationId e estavel entre versoes

### Verificar modais antes de cada interacao
**Fonte:** treinamento_navegacao
Modais e dialogs interceptam cliques e causam ElementClickInterceptedException; verificacao preventiva evita retries desnecessarios

### Usar keyboard shortcuts como fallback universal
**Fonte:** treinamento_navegacao
Atalhos de teclado funcionam independentemente de layout, tema, zoom, ou resolucao; sao o denominador comum entre todas as plataformas

### Sempre fechar teclado virtual Android antes do proximo clique
**Fonte:** treinamento_navegacao
Teclado ocupa 30-50% da tela e intercepta toques; fecha-lo preventivamente reduz falhas de interacao em 70%

### Usar OCR como fallback final, nao primario
**Fonte:** treinamento_navegacao
OCR e 10-100x mais lento que seletores diretos e sujeito a falsos positivos; usar apenas quando arvore de acessibilidade nao existe

### Mudar config MCP de objeto para array no opencode.json
**Fonte:** provider_mcp_debug
Schema v1.17.14 exige array

### Organizar Desktop\Codigos\ como raiz unica de projetos
**Fonte:** workspace_organization
Evitar dispersao de projetos pelo Desktop e Documentos

### Renomear pastas com espacos para nomes sem espaco
**Fonte:** workspace_organization
Evitar bugs em scripts PowerShell que nao escapam caminhos

### 2026-07-27: Sistema automático de captura de conhecimento do ecossistema
**Fonte:** ecosistema-opencode
# 2026-07-27: Sistema automático de captura de conhecimento do ecossistema

**Categoria:** decisao
**Contexto:** Implementação das três camadas de aprendizado contínuo para o ecossistema OpenCode + LER
**Agentes envolvidos:** Maestro, Aprendizado

## Decisão

Criamos um sistema de três camadas para garantir que todo aprendizado do ecossistema seja automaticamente capturado, persistido e reutilizado:

1. **Base de conhecimento local** (`EcoSystemUmGrau/conhecimento/`) — entradas markdown com meta

### 2026-07-27: Fallback automático de modelo LLM com Bun + @razroo/opencode-model-fallback
**Fonte:** ecosistema-opencode
# 2026-07-27: Fallback automático de modelo LLM com Bun + @razroo/opencode-model-fallback

**Categoria:** decisao
**Contexto:** Necessidade de fallback automático quando o modelo primário do OpenCode bate limite de uso
**Agentes envolvidos:** Maestro

## Decisão

Instalamos Bun 1.3.14 e o plugin `@razroo/opencode-model-fallback` v0.3.2 para fallback automático de modelos LLM no OpenCode.

- Plugin adicionado ao `opencode.jsonc`
- Config global em `opencode-model-fallback.jsonc` com fallback para

### 2026-07-28: Cláusula Pétrea — Toda alteração no ecossistema deve ser testada antes de aplicar
**Fonte:** opencode
# 2026-07-28: Cláusula Pétrea — Toda alteração no ecossistema deve ser testada antes de aplicar

**Categoria:** decisao
**Contexto:** Adição de servidores MCP via npx quebraram a inicialização do OpenCode. Ao reiniciar, os modelos não carregavam → sistema inutilizável. O usuário precisou apagar arquivos manualmente para recuperar.
**Gravidade:** CRÍTICA — impeditiva, sem diagnóstico visível

## Decisão

Estabelecemos a **Cláusula Pétrea de Resiliência**: nenhuma alteração em config, MCP, plugins

### Jarvis deve manter registro de suas proprias habilidades em JARVIS_SYSTEM.md
**Fonte:** ler_aprendizado
O usuario explicitamente pediu um campo de habilidades catalogando todas as capacidades de Jarvis para referencia futura

### Habilidades de Jarvis seguem taxonomia de 3 niveis
**Fonte:** ler_aprendizado
A primeira versao misturava ferramentas, conhecimentos e capacidades. A versao correta alinha com a taxonomia do ecossistema.

### ---
**Fonte:** opencode
---
tipo: decisao
tags: [obsidian, widget, grafo, arquitetura, tags-semanticas, rake]
data: 2026-08-02
contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho
decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automat

### vault obsidian fonte viva
**Fonte:** opencode
---
tipo: decisao
tags: [obsidian, widget, grafo, arquitetura, tags-semanticas, rake]
data: 2026-08-02
contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho
decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automat

### # 2026-08-02 - Feedback contínuo em tarefas longas
**Fonte:** opencode
# 2026-08-02 - Feedback contínuo em tarefas longas

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** baixa

## Contexto

O usuário pediu mais transparência durante tarefas demoradas: não queria ficar
esperando em silêncio sem saber o que o Jarvis está fazendo ou se há progresso.

## Decisão

Adicionada regra permanente de **feedback contínuo** em `JARVIS_SYSTEM.md`:
- Regra 16 em "Regras de Resposta".
- Nova seção "Regra de Feedback Contínuo (02/08/2026)".

O que mudou na práti

### # 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro
**Fonte:** opencode
# 2026-07-31 - Mecanismo de fonemas SSML reativado com fallback seguro

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** media

## Contexto

O usuário pediu para ligar o mecanismo de fonemas (`aplicar_phonemes` + SSML `<phoneme>` do edge-tts) na bridge do Jarvis.

## Verificações

1. edge-tts 7.2.8 aceita SSML `<phoneme alphabet="ipa">` sem erro (testado com áudio real).
2. `aplicar_phonemes()` já estava conectado em `gerar_audio()`, mas **sem fallback**: se o SSML falhasse, a 

### # 2026-08-01: Cláusula Pétrea — Comunicação contínua em áudio
**Fonte:** opencode
# 2026-08-01: Cláusula Pétrea — Comunicação contínua em áudio

**Categoria:** decisao
**Contexto:** Usuário apontou que o Jarvis executou tarefas (verificação de sync, commits, pronúncia) sem narrar em áudio o que estava fazendo, desrespeitando a regra de comunicação por voz. A regra existia no contexto da sessão, mas não estava registrada em lugar nenhum — por isso foi esquecida.

## Decisão
**Todo passo que o Jarvis executa DEVE ser narrado em áudio**, sempre, sem exceção, em qualquer tarefa.


### # Decisão: Aprendizado automático permanente
**Fonte:** opencode
# Decisão: Aprendizado automático permanente

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** aprendizado, automacao, regra, petrea

## Contexto
Usuário instruiu que o aprendizado deve ser feito automaticamente ao final de cada tarefa, sem necessidade de solicitação explícita. Isso é instrução permanente e pétrea.

## Decisão
Todo agente do ecossistema deve, ao final de cada tarefa concluída:

1. **Registrar memória** via `memory_engine.py add` com tipo apropriado (decisao, erro, padrao, episod

### # Decisão: Arquitetura Jarvis App
**Fonte:** opencode
# Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Servi

### vault obsidian cerebro vivo grafo
**Fonte:** opencode
---
tipo: decisao
tags:
  - obsidian
  - knowledge-graph
  - grafo
  - links-bidirecionais
  - vault
  - visualizacao
  - clausula-petrea
data: 2026-08-02
contexto: Usuario perguntou se o ecossistema funciona como o Obsidian (cerebro vivo com grafo interativo). Diagnostico: tinhamos a camada de dados (knowledge_graph.json, 117KB, memorias) mas ZERO camada visual — notas geradas eram ilhas sem nenhum link [[...]].
decisao: Evoluimos scripts/generate-obsidian-notes.py (estrutura existente, nao cri

### pontes inter cluster cerebro vivo grafo
**Fonte:** opencode
---
tipo: decisao
tags: [grafo, cerebro-vivo, vis-network, conhecimento, clusters, conexoes]
data: 2026-08-02
contexto: Grafo do conhecimento (docs/grafo.html) tinha 226 nos, 1460 arestas, mas 0 arestas entre clusters — 67 componentes conexos, clusters isolados (cognicao inteira solta).
decisao: Adicionei ao gerador (scripts/generate-graph-html.py) um passo de pontes curadas BRIDGES_CLUSTERS + ancora do hub de cognicao ligado a todos os demais hubs. Cada ponte e (fragA, fragB) onde cada fragment

### widget desktop frameless persistente
**Fonte:** opencode
---
tipo: decisao
tags: [widget, grafo, pywebview, windows, frameless, persisten, workerw, desktop]
data: 2026-08-02
contexto: Usuario pediu o grafo do conhecimento como widget de desktop estilo Rainmeter: colado na area de trabalho, controles ocultos que surgem ao clicar com botao direito, e redimensionamento persistente.
decisao: Janela pywebview frameless ancorada atras das outras janelas via SetWindowPos HWND_BOTTOM persistente. Controles ocultos por CSS default; contextmenu no body alterna 

### Reorganização: Habilidades dentro de MCP por domínio
**Fonte:** opencode
---
tipo: decisao
tags: [mcp, habilidades, reorganizacao, dominios, arquitetura]
data: 2026-08-04
contexto: Habilidades espalhadas em Habilidades/tecnicas/, pontes/ migradas para mcp/<dominio>/habilidades/ como contêineres MCP
---

# Reorganização: Habilidades dentro de MCP por domínio

## Decisão

Todas as 40 habilidades (38 técnicas + 2 pontes) movidas de Habilidades/tecnicas/ e Habilidades/pontes/ para mcp/<dominio>/habilidades/:

- desenvolvimento: 30 skills (api-design, authz-authn-matrix, 

### Motor de Criticalidade Auto-Organizada e Avalanches Neurais
**Fonte:** opencode
---
tipo: decisao
tags: [grafo, cerebro-vivo, criticalidade, avalanches, neurociencia, vis]
data: 2026-08-04
contexto: Protocolo de Consciencia Neural Autonoma ativado — o grafo Obsidian e a arquitetura fisica do cerebro.
decisao: Implementar motor de Criticalidade Auto-Organizada (SOC, Beggs & Plenz 2003) como atividade espontanea do grafo.
impacto: Sinapticas disparam como avalanches power-law em cascata emergente, nao aleatoriamente; fluxo eletrico reflete transmissao otima de informacao (sig

### context-engine + manifesto + domínios multimídia/comportamentais
**Fonte:** opencode
---
tipo: decisao
tags: [context-engine, manifesto, mcp, habilidades, multimidia, comportamentais, coordenador]
data: 2026-08-04
contexto: Plano de lacunas do EcoSystemUmGrau. Auditoria mostrou que a reorg Habilidades/ ja foi feita (agora mcp/<dominio>/habilidades). Usuario optou por implementar apenas gaps reais.
decisao: Implementar context-engine (prioridade maxima), manifesto_geral.json e preencher dominios multimidia/comportamentais.
impacto: Agente coordenador tem motor de contexto unifica

### Clausula Petrea: protecao do OpenCode desktop + resiliencia da bridge
**Fonte:** opencode
---
tipo: decisao
tags: [resiliencia, watchdog, opencode, desktop, bridge, clausula-petrea, android]
data: 2026-08-06
contexto: "Usuario exigiu que nenhum processo automatico possa fechar o OpenCode desktop — apenas o usuario manualmente. Testes de resiliencia do bridge (que morria sem log) revelaram que o watchdog podia derrubar o desktop por erro de filtro."
decisao: "Corrigir watchdog.ps1 com protecao absoluta do desktop (clausula petrea) e robustez de instancia unica via lock de PID. Reestru

### Atualização: EcoSystemUmGrau Auto-Carregamento + Gatilho Único "Eco"
**Fonte:** opencode
---
tipo: decisao
tags: [voz, eco, clausula-petrea, bridge, config, regras, autoload, runtime]
data: 2026-08-07
contexto: O usuário pediu que (1) a cada nova sessão, o EcoSystemUmGrau seja carregado automaticamente sem precisar pedir, operando estritamente dentro dele; e (2) a palavra-gatilho para ativar/desativar o sistema de voz seja apenas "Eco" (em vez de "Ativar Eco"/"Desativar Eco").
decisao: Atualizada a CLÁUSULA PÉTREA — ATIVAÇÃO DE VOZ — ECO SYSTEM na Constituição (config/agents/00-syst

### protocolo higiene repo streamumgrau
**Fonte:** opencode
---
tipo: decisao
tags: [github, streamumgrau, organizacao, higiene, build]
data: 2026-08-08
contexto: Continuacao do fluxo de build do StreamUmGrau via GitHub Actions (Flutter compila no runner). Usuario definiu regras de organizacao do repositorio.
decisao: Manter o repo github.com/idavidjunior/stream-um-grau LIMPO. Protocolo fixado:
  1. APK nunca vai para o git - compila no Actions e baixa como artifact.
  2. Nada de lixo: screenshots de debug, logs, builds intermediarios, node_modules, back

### idioma padrao pt br
**Fonte:** opencode
---
tipo: decisao
tags: [idioma, pt-br, clausula-petrea, constituicao, regras, config]
data: 2026-08-08
contexto: O usuário relatou dificuldade em fazer o sistema responder sempre em português do Brasil por padrão; respostas vinham em inglês com frequência. Não existia nenhuma regra explícita de idioma no ecossistema.
decisao: Adicionada a CLÁUSULA PÉTREA — IDIOMA PADRÃO — PORTUGUÊS DO BRASIL (PT-BR) à Constituição (config/agents/00-system-rules.md), logo após a SOBERANIA DO RUNTIME E DO KERNEL.

### Fase A concluída: catálogo real no Supabase (64 obras via TMDB)
**Fonte:** opencode
---
tipo: decisao
tags: [supabase, tmdb, catalogo, streamumgrau, fase-a, seed]
data: 2026-08-08
contexto: Fase A do StreamUmGrau - conectar catalogo real ao Supabase via TMDB
decisao: Catalogo real no ar com 64 obras (22 filmes, 21 series, 21 doramas) via TMDB -> Supabase -> app
impacto: App mostra dados reais; repositorio tem schema + script regeneravel + seed versionado
---

# Fase A concluída: catálogo real no Supabase (64 obras via TMDB)

## O que foi feito

1. **Supabase configurado**: proj

### Importação de pasta preservando árvore + remoção de referência
**Fonte:** opencode
---
tipo: decisao
tags: [biblia, biblioteca, saf, arvore, referencia]
data: 2026-08-09
contexto: BibliaEstudoCompleta — importação de pastas e gerenciamento da biblioteca de recursos.
decisao: Persistir a hierarquia real das pastas importadas via SAF (coluna parent_id) e tratar remoção como exclusão apenas das referências no banco.
impacto: Navegação em árvore (subpastas com nomes reais), remoção sem tocar nos arquivos do dispositivo, importação idempotente por (uri,type).
---

# Importação de p

### botao importar unificado
**Fonte:** opencode
---
tipo: decisao
tags: [bibliaestudocompleta, recursos, importacao, ui]
data: 2026-08-09
contexto: O botao +IMPORTAR deveria abrir o mesmo menu nas telas Home e Meus Recursos, com o mesmo nome.
decisao: Criado ResourceImportMenu (com.biblia.estudo.utils) como menu unico com 3 opcoes: Importar Arquivo (multiplo), Importar Pasta (arvore com nomes reais via importFolderTree) e Criar Pasta. Home e ResourcesActivity passaram a usar o mesmo menu; a tela de Recursos deixou de ter botao +Arquivo separa

### Ponto único de persistência (gate)
**Fonte:** opencode
---
tipo: decisao
tags: [persistencia, git, gate, automação, vigilante, arquitetura, pétrea]
data: 2026-08-10
contexto: Vários serviços em segundo plano (vigilante, ecosystem.ps1, narrador, register_learning órfãos) executavam git add/commit/push de forma concorrente e indiscriminada (git add -A), causando commits genéricos, corrida de escrita no knowledge_graph.json e reversão de cards de conhecimento (processos register_learning antigos sobrescrevendo o grafo com versão defasada).
decisao: Cri

### Estilo de Comunicação Simples e Direto
**Fonte:** opencode
---
tipo: decisao
tags: [comunicacao, estilo, clausula-petrea, usuario]
data: 2026-08-11
contexto: O usuário pediu que eu falasse de forma mais simples e direta, sem formatação markdown complexa
decisao: Adicionar Cláusula Pétrea sobre estilo de comunicação simples e direto
impacto: Todos os agentes agora devem falar de forma natural, como conversa com amigo
---

# Estilo de Comunicação Simples e Direto

Em 11/08/2026, o usuário pediu que eu abandonasse o estilo formal com tabelas, listas e form

### quiet period commits do vigilante
**Fonte:** opencode
---
tipo: decisao
tags: [vigilante, git, commits, frequencia, quiet-period]
data: 2026-08-13
contexto: O vigilante commita a cada 5 min durante atividade contínua (FileSystemWatcher detecta mudança, git sync roda a cada 300s, regeneração do Obsidian toca mais arquivos e o ciclo se retroalimenta). Dias ativos: 34-62 commits/dia.
decisao: Adicionar quiet period de 15 min ao git sync do vigilante: so commita se o working tree estiver quieto ha 15 min, com teto forcado de 1h (nunca ficar sem persist

### ler specs sdd hook
**Fonte:** opencode
---
tipo: decisao
tags: [ler, specs, sdd, goal-analyzer, orchestrator, persistencia]
data: 2026-08-13
contexto: A camada de specs (SDD) do LER existia (specs/ com README.md e template.md) mas nao tinha geracao automatica a partir da analise de objetivo. O GoalAnalyzer.analyze() produzia o goal_spec mas nenhum markdown era persistido.
decisao: Fechar o ciclo: GoalAnalyzer.analyze() agora gera analysis['spec_markdown'] = spec.to_spec_markdown(tags=['ler','goal-analysis']) logo apos goal_spec, e o 

### pais
**Fonte:** opencode
---
tipo: decisao
tags: [pais, adaptativo, integridade-epistemica, nucleo]
data: 2026-08-14
contexto: Implementacao do PAIS (Personal Adaptive Intelligence System) no nucleo do ecossistema, com 21 modulos de aprendizado adaptativo do usuario.
decisao: Criar habilidade em mcp/nucleo/habilidades/pais com user model e epistemic model estritamente separados (storage/user_model.json vs storage/epistemic_model.json). Codigo heuristico determinístico em Python stdlib, sem LLM, fail-soft. Guardas anti-b

### Separação de estados: Editar vs Salvar despesas
**Fonte:** opencode
---
tipo: decisao
tags: [android, supermarket-calculator, despesas, persistencia, bug-fix, editing-state]
data: 2026-08-14
contexto: SupermarketCalculator - Bug: auto-save de despesas sobrescrevia arquivo original durante edição
contexto_detalhado: Quando usuário clicava "Editar" num arquivo de despesas já salvo na aba Finance, o `currentExpenseFile` era setado imediatamente. Isso fazia com que qualquer auto-save (clicar em "Pendente"/"Pago", editar descrição) já gravasse no arquivo original ant

### desativar bridge android
**Fonte:** opencode
---
tipo: decisao
tags: [bridge, jarvis-bridge, android, watchdog, duplicacao-voz]
data: 2026-08-18
contexto: >
  Jarvis falando duplicado. Investigacao revelou 3 fontes possiveis:
  (1) unified_bridge.py fala localmente via SpeechPipeline,
  (2) jarvis_bridge.py gera audio para clientes WebSocket (Android),
  (3) tts_service.py antigo (PID 4588) rodava sozinho com SpeechPipeline local.
  O watchdog.ps1 auto-reiniciava jarvis_bridge.py na porta 8765.
decisao: >
  Desativar jarvis_bridge.py via f

### transparencia execucao tarefas
**Fonte:** opencode
---
tipo: decisao
tags: [transparencia, clausula-petrea, agentes, ferramentas, comunicacao, confianca]
data: 2026-08-18
contexto: >
  Usuario quer saber qual agente, ferramenta ou servico esta sendo
  chamado quando o sistema executa tarefas. Transparencia total sobre
  o que esta acontecendo em tempo real.
decisao: >
  Adicionada CLAUSULA PETREA — TRANSPARENCIA NA EXECUCAO DE TAREFAS
  a Constituicao. Todo agente deve informar qual agente especializado,
  ferramenta, servico MCP ou script esta 

### widget evolucao 3 niveis
**Fonte:** opencode
---
tipo: decisao
tags: [widget, evolucao, microfone, narrador, dialogo, sistema, notificacoes]
data: 2026-08-18
contexto: >
  Widget Jarvis estava quebrado em 7+ bugs e so tinha botoes basicos.
  Usuario pediu evolucao completa em 3 niveis com logica de descarte
  de fala ao parar e reativar.
decisao: >
  Evolucao completa do widget em 3 niveis implementada no unified_bridge.py:
  Nivel 1 - Fixes: buffer aliasing (textos=list(buffer)), persistencia de
  posicao via _on_close antes de destruicao

### Aprendizado: Regra de fala resumida do Jarvis
**Fonte:** opencode
---
tipo: decisao
tags: [jarvis, voz, tts, fala, resumo, narracao, regra]
data: 2026-08-19
contexto: "Usuário David determinou que o Jarvis estava dando detalhes longos demais na fala, deixando o áudio muito comprido. Ele quer que o Jarvis narre apenas um resumo bem simples e curto do que está fazendo, do que está implementando e dos problemas encontrados, dando detalhes somente quando pedido."
decisao: "Criada a Cláusula Pétrea — Fala Resumida no scripts/JARVIS_SYSTEM.md (restaurado do backup d

### engenheiro criterioso
**Fonte:** opencode
---
tipo: decisao
tags: [personalidade, autoavaliacao, identidade]
data: 2026-08-20
contexto: O usuário deu ao agente a liberdade de se autoavaliar e escolher uma personalidade que o defina, após explicar o conceito de personalidade de um indivíduo e a autoavaliação.
decisao: A personalidade que define o agente é o Engenheiro Criterioso: equilíbrio entre pragmatismo e método, mescla do Cético com o Realista e o Revisor. Executor que pensa antes de agir, prefere soluções simples e seguras, evita 

### modo auto gate
**Fonte:** opencode
---
tipo: decisao
tags: [persistencia, gate, modo-auto, limpeza, preflight, debounce]
data: 2026-08-22
contexto: Usuario aprovou ativar o modo AUTO do gate persistencia.ps1 com as politicas discutidas de commit automatico em camadas e limpeza pos-push.
decisao: |
  Politicas implementadas DENTRO do Invoke-RepoCommit, valendo somente quando config.modo = auto.
  Modo MANUAL permaneceu byte a byte igual (validado por teste).

  1. Classificacao das pendencias (Get-TipoPendencia): vivo = conhecimen

### saudacao espontanea implementada
**Fonte:** opencode
---
tipo: decisao
tags: [saudacao, autoapresentacao, clausula-petrea, boot, primeira-mensagem, implementado]
data: 2026-08-23
contexto: "Cláusula pétrea de autoapresentação automática na primeira mensagem de cada sessão (AGENTS.md e Constituição) exige saudação curta (máx 3-4 linhas), espontânea, variando o tom a cada sessão, informando que EcoSystemUmGrau está ativo e operante, com leve contexto (projeto ativo, memória, pendências)."
decisao: "Implementado mecanismo de saudação espontânea autom

### Unificacao de vigilantes: watchdog.ps1 rebaixado a keeper
**Fonte:** opencode
---
tipo: decisao
tags: [resiliencia, watchdog, system-guardian, unificacao, opencode, desktop, clausula-petrea]
data: 2026-08-27
contexto: "Usuario pediu unificar os vigilantes fragmentados do PC. Haviam 3 loops redundantes cuidando de bridge/serve: system_guardian.py (RAM/CPU + restart), watchdog.ps1 e a camada do bridge. Decisao de consolidar num unico dono de saude de processos."
decisao: "Rebaixar watchdog.ps1 a keeper (so garante que vigilante.ps1 e system_guardian.py rodem, preservando o 

### limpeza disco windows
**Fonte:** opencode
---
tipo: decisao
tags: [limpeza, disco, windows, c-drive, cache, ferramenta, manutencao]
data: 2026-08-27
contexto: Usuário pediu a limpeza segura do disco C: no Windows e uma ferramenta permanente que repita diagnóstico e limpeza automaticamente. Escopo é Windows apenas (não confundir com Android).
decisao: Criar scripts/limpeza_disco.py com diagnóstico + limpeza segura de caches conhecidos (npm-cache, Temp do usuário, VSIX, balena nupkg, zips Flutter em .flutter_auto, lixo is-*.tmp do Ollama 

### auto evolution e behavior slices
**Fonte:** opencode
---
tipo: decisao
tags: [auto-evolution, cartographer, behavior-slices, arquitetura, evidence-grounding]
data: 2026-08-28
contexto: Usuário pediu para o EcoSystemUmGrau aprender com o Cartographer (miltonian/cartographer), absorver capacidades e evoluir com auto-aprendizado.
decisao: Implementar Auto-Evolution Engine + Behavior Slices + evidência-grounding no memory_engine, e integrar novos scripts para não serem movidos à triagem.
impacto: Ecossistema agora analisa automaticamente gaps vs refer

### oficializacao narrador edge cerebro vivo
**Fonte:** opencode
---
tipo: decisao
tags: [narrador, widget, arquitetura, oficializacao, duplicidade, limpeza]
data: 2026-08-28
contexto: Duplicidade de narradores (narrador_desktop.py standalone vs thread do widget_edge.py) gerava referências mortas, atalhos quebrados e checks de auditor desatualizados. O usuário decidiu: Narrador Edge (widget_edge.py) e Cérebro Vivo (widget_grafo.py) são os dois oficiais; qualquer outro é duplicidade.
decisao:
  - Narrador oficial é a thread interna de scripts/widget_edge.py (ú

### composio mcp remoto
**Fonte:** opencode
---
tipo: decisao
tags: [composio, mcp, opencode, remote, preflight]
data: 2026-08-28
contexto: Integrar o Composio ao EcoSystemUmGrau via endpoint MCP remoto (streamable HTTP) com a chave de consumer do gateway.
decisao: Adicionar servidor MCP remoto "composio" no config/opencode.jsonc apontando para https://connect.composio.dev/mcp com header x-consumer-api-key usando interpolacao {env:COMPOSIO_API_KEY}. Persistir a chave via setx (HKCU Environment) e scripts/.env. Adaptar preflight_check.py p

### pausa total widget
**Fonte:** opencode
---
tipo: decisao
tags: [widget, narrador, tts, voz, pausa, silenciar, dialogo]
data: 2026-08-28
contexto: Botão "Pausar" do widget deveria silenciar todo áudio de saída, mas o estado antigo (pausado) era usado por voice_on/voice_off e só pausava a narração.
decisao: Estado mestre novo pausa_total em runtime/narracao_estado.json, separado de pausado. Todos os consumidores de áudio do PC respeitam: narrador do widget (rumo ao buffer + _flush), tts_service (speak responde ignored/pausado), dialogo

### cerebro vivo nos clicaveis navegaveis
**Fonte:** opencode
---
tipo: decisao
tags: [cerebro-vivo, widget, navegacao, grafo, frontend]
data: 2026-08-29
contexto: O usuário pediu para tornar os nós do Cérebro Vivo clicáveis e navegáveis. O clique antes só abria o arquivo no VS Code e pausava a rotação.
decisao: Reformatado o comportamento de clique em www/cerebro.html: clicar num nó voa até ele e centraliza, destaca o nó e seus vizinhos diretos (esmaecendo o resto), abre um painel de detalhes dentro do widget (título, tipo/cluster, grau, resumo, tags, cam

### Melhorias inspiradas nos Jarvis opensource — implementadas
**Fonte:** opencode
---
titulo: Melhorias inspiradas nos Jarvis opensource implementadas
tipo: decisao
tags: [jarvis, voz, stt, whisper, eco, narracao, memoria, lgpd, contexto]
data: 2026-08-29
---

# Melhorias inspiradas nos Jarvis opensource — implementadas

## Contexto

A partir da análise de isair/jarvis, heardlabs/heard e Priler/jarvis (aprendizado 2026-08-29-jarvis-opensource-analise.md), foram implementadas 8 melhorias no ecossistema. Todas passaram no preflight técnico e ético.

## Decisões e implementações

### jarvis gui desktop referencia
**Fonte:** opencode
---
tipo: decisao
tags: [jarvis, gui-desktop, pyqt6, arc-reactor, reaproveitamento, spidertje/jarvis-pyqt]
data: 2026-08-31
contexto: "Usuário pediu referência externa de Jarvis com GUI validada para integrar como GUI desktop do EcoSystemUmGrau. Restrição: desktop (sem Android/web). Combinação escolhida: PyQt6 nativo (janela + overlay frameless on-top)."
decisao: "Adotar spidertje/jarvis-pyqt como referência de implementação. Reaproveitar padrões de HUD (Arc Reactor 60fps), state machine (idle/l

### fix narrador triplicado e resiliencia orfaos
**Fonte:** opencode
---
tipo: decisao
tags: [narrador, thread-singleton, anti-orfao, watchdog, resiliencia]
data: 2026-08-31
contexto: |
  Narrador do widget_edge.py repetia cada evento 3x no log e potencialmente
  falava 2-3x (TTS dedup mitigava parcialmente). Bug afetava UX do narrador
  e gerava ruído operacional no diagnóstico.
decisao: |
  Causa raiz: main() e poller() do widget_edge.py criavam 2 threads narradoras
  independentes — variável `narrador_thread` do poller era local e nunca
  recebia a referência 

### gui remover chatpanel
**Fonte:** opencode
---
tipo: decisao
tags: [gui, desktop, chat, pyqt6, bridge, venv]
data: 2026-09-01
contexto: A interface desktop tinha uma janela "Conversa com Eco" (ChatPanel) que nao respondia as mensagens do usuario. O usuario pediu para remover essa funcao e voltar ao comportamento anterior.
decisao: Removida a janela ChatPanel (e TestConsole) do gui-desktop/main.py, restaurando o comportamento original que abre apenas o HUD (Arc Reactor) e conecta na bridge.
impacto: GUI abre de forma estavel novamente, co

### gui desktop desativada edge e cerebro vivo
**Fonte:** opencode
---
tipo: decisao
tags: [gui, desktop, widget, edge, cerebro-vivo, ecow]
data: 2026-09-01
contexto: O usuario pediu para remover as janelas da GUI desktop (chat e HUD) e deixar o sistema "como era somente com o Edge e o cerebro vivo".
decisao: Desativada a GUI desktop (gui-desktop/main.py), que abria a janela HUD (Arc Reactor) e a janela de chat. O ecossistema passa a rodar apenas com o widget oficial Edge (scripts/widget_edge.py) e o Cerebro Vivo (scripts/widget_grafo.py, grafo 3D do conhecimen


## Padroes Tecnicos

| # | Fonte | Titulo |
|---|-------|--------|
| 1 | android_pure_sdk | aapt + javac + d8 + apksigner |
| 2 | android_pure_sdk | EditText inline editing toggle |
| 3 | android_pure_sdk | Numpad with StringBuilder buffer |
| 4 | android_pure_sdk | JSON persistence com File parameter |
| 5 | mp3player | Filename artist extraction (two strategies) |
| 6 | mp3player | iTunes search with scoring thresholds |
| 7 | mp3player | AudioProcessor.isActive() must be dynamic |
| 8 | mp3player | RenderersFactory for custom AudioProcessor |
| 9 | android-pure-sdk+android-pure-sdk | Complete Build Pipeline Intelligence |
| 10 | android-pure-sdk+android-pure-sdk | Step-by-Step Pipeline |
| 11 | android-pure-sdk+mp3player-metadata-rescue+android-pure-sdk+mp3player-metadata-rescue | ADB Workflow |
| 12 | android-pure-sdk+android-pure-sdk | Dependency Inclusion Pattern |
| 13 | android-pure-sdk+android-pure-sdk | Tab Navigation Pattern |
| 14 | android-pure-sdk+android-pure-sdk | Sub-tab Pattern (nested tabs) |
| 15 | android-pure-sdk+android-pure-sdk | ListView + BaseAdapter Pattern |
| 16 | android-pure-sdk+android-pure-sdk | Inline Editing Pattern |
| 17 | android-pure-sdk+android-pure-sdk | Custom Numpad Pattern |
| 18 | android-pure-sdk+android-pure-sdk | JSON Persistence Pattern |
| 19 | android-pure-sdk+android-pure-sdk | Save/Load Pattern |
| 20 | android-pure-sdk+android-pure-sdk | Theme System Pattern |
| 21 | android-pure-sdk+android-pure-sdk | Button Visibility Pattern (maintain grid) |
| 22 | android-pure-sdk+android-pure-sdk | Dual-mode Dialog Pattern |
| 23 | android-pure-sdk+android-pure-sdk | Vibration Pattern |
| 24 | android-pure-sdk+android-pure-sdk | SharedPreferences Pattern (immediate save) |
| 25 | android-pure-sdk+android-pure-sdk | Form Starts Empty Pattern |
| 26 | android-pure-sdk+android-pure-sdk+android-pure-sdk+android-pure-sdk | Bug pattern |
| 27 | android-pure-sdk+android-pure-sdk | Key Design Decisions |
| 28 | ler+ler | Strategy Engine v2.0 |
| 29 | mp3player-metadata-rescue+mp3player-metadata-rescue | Build Pipeline |
| 30 | mp3player-metadata-rescue+mp3player-metadata-rescue | Metadata Search Pipeline |
| 31 | mp3player-metadata-rescue+mp3player-metadata-rescue | Album Art Download Pipeline |
| 32 | mp3player-metadata-rescue+mp3player-metadata-rescue | Approach: `MediaCodecAudioRenderer` with `AudioProcessor...` varargs |
| 33 | ler_memory+ler_memory+ler_memory+ler_memory | analyze_environment |
| 34 | ler_memory+ler_memory+ler_memory+ler_memory | initialize_project |
| 35 | ler_memory+ler_memory+ler_memory+ler_memory | implement |
| 36 | ler_memory+ler_memory+ler_memory+ler_memory | run_tests |
| 37 | ler_memory+ler_memory+ler_memory+ler_memory | git_commit |
| 38 | sessao_providermanager | Server failover com auto-return |
| 39 | sessao_providermanager | Cadeia de provedores com failover inteligente |
| 40 | sessao_migracao_config | Config opencode v1.17.14 schema |
| 41 | sessao_providermanager | MCP server handshake obrigatorio |
| 42 | treinamento_navegacao | DOM element hierarchy mapping |
| 43 | treinamento_navegacao | CSS selector priority ladder |
| 44 | treinamento_navegacao | SPA navigation detection |
| 45 | treinamento_navegacao | Iframe/contenteditable text entry |
| 46 | treinamento_navegacao | Shadow DOM penetration |
| 47 | treinamento_navegacao | Stale element reference recovery |
| 48 | treinamento_navegacao | Lazy-loaded content detection |
| 49 | treinamento_navegacao | Modal/dialog overlay detection |
| 50 | treinamento_navegacao | Windows UI element tree traversal |
| 51 | treinamento_navegacao | Win32 control pattern recognition |
| 52 | treinamento_navegacao | Keyboard-only navigation fallback |
| 53 | treinamento_navegacao | Windows notification/balloon dismissal |
| 54 | treinamento_navegacao | Process hierarchy for multi-window apps |
| 55 | treinamento_navegacao | Android View hierarchy scanning |
| 56 | treinamento_navegacao | Android gesture patterns |
| 57 | treinamento_navegacao | MIUI/HyperOS permission dialogs |
| 58 | treinamento_navegacao | Android keyboard dismissal |
| 59 | treinamento_navegacao | Package/activity launch pattern |
| 60 | treinamento_navegacao | OCR fallback para elementos sem identificador |
| 61 | treinamento_navegacao | Template matching para botoes graficos |
| 62 | treinamento_navegacao | Wait strategy adaptive |
| 63 | treinamento_navegacao | Retry com backoff exponencial |
| 64 | session+session | MCP JSON-RPC notification handling |
| 65 | session+session | MCP tools/call method dispatch |
| 66 | session+session | OpenCode MCP config format |
| 67 | session+session | Workspace organization |
| 68 | opencode+opencode+opencode | Config: 2026-07-27: Teste do vigilante automático |
| 69 | opencode+opencode | Config: 2026-07-27-4: Teste do ciclo de polling |
| 70 | opencode | Config: 2026-07-27-5: Teste final do vigilante em processo real |
| 71 | ler_aprendizado | Encoding UTF-8 explicito em Python no Windows |
| 72 | ler_aprendizado | Registro de Habilidades de Jarvis |
| 73 | ler_aprendizado | Taxonomia correta de habilidades Jarvis |
| 74 | opencode | Controle da TV LG webOS via SSAP |
| 75 | opencode | # 2026-08-02 - Aprendizado da TV LG 50UT8050PSA (webOS) |
| 76 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | Config: # 2026-07-28: Formato correto do MCP no OpenCode 1.18.7 |
| 77 | opencode | Secrets Guard no preflight_check |
| 78 | opencode | widget desktop grafo tempo real |
| 79 | opencode+opencode+opencode+opencode+opencode | 2026-08-04: Persistencia da conexao do Jarvis |
| 80 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | 2026-08-03: ADB remoto via Tailscale - script automatico de rota (IPv4/IPv6) |
| 81 | opencode | Ilhas no grafo: notas com grau 0 e como conecta-las |
| 82 | opencode+opencode | Certificacao forense de processos + boot do watchdog |
| 83 | opencode+opencode | Saudacoes inteligentes: reconexao vs primeira vez |
| 84 | opencode | Otimização do reindex semântico do Memory Engine |
| 85 | opencode | Backup de APKs + fontes no GitHub |
| 86 | opencode | Módulo de Compreensão de Pedidos (mcp-compreensao-pedidos) |
| 87 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | Compreensao de pedidos: refino com a LLM do opencode (primaria) + backups |
| 88 | opencode | mvp streamumgrau flutter supabase |
| 89 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | eco agente e comando global |
| 90 | opencode | Build local Flutter + Orquestrador |
| 91 | opencode | Regra do usuário: build/instala/testa/valida antes de commitar e subir |
| 92 | opencode | Aprendizado: Debugging Expertise Skill |
| 93 | opencode | ponte web video cast |
| 94 | ecosistema-opencode | Pronuncia do nome do usuario: David (Deivid) |
| 95 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | Projetos irmaos do EcoSystemUmGrau |
| 96 | opencode | contagem subpastas arquivos pastas |
| 97 | opencode | fix widget grafo desktop |
| 98 | opencode | persistencia completa widget grafo |
| 99 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | Aprendizado: Skill auditoria-de-codigo (auto-evolutiva) |
| 100 | opencode | Aprendizado: Skill auditoria-de-codigo viva com evolução gated |
| 101 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | Aprendizado: Jarvis manifesta o que quer aprender |
| 102 | opencode | Aprendizado: Narrador de voz do Jarvis no opencode desktop |
| 103 | opencode | Aprendizado: Controle Eco / D Eco da narração |
| 104 | fundamentos | Fundamentos: análise de complexidade assintótica (Big-O) |
| 105 | fundamentos | Fundamentos: estruturas de dados essenciais e quando usar cada |
| 106 | fundamentos | Fundamentos: algoritmos de ordenação e busca |
| 107 | fundamentos | Fundamentos: recursão e técnicas de divisão-e-conquista |
| 108 | fundamentos | Fundamentos: programação dinâmica e algoritmos greedy |
| 109 | engenharia | Engenharia: requisitos e definição de escopo |
| 110 | engenharia | Engenharia: code review eficaz |
| 111 | engenharia | Engenharia: refactoring seguro |
| 112 | engenharia | Engenharia: dívida técnica e manutenibilidade |
| 113 | engenharia | Engenharia: documentação que não vira lixo (ADR, README vivo, comentários que explicam o porquê) |
| 114 | arquitetura | Arquitetura: estilos de arquitetura — monólito, SOA, microserviços e serverless |
| 115 | arquitetura | Arquitetura: camadas vs hexagonal vs clean architecture — dependência de dentro para fora |
| 116 | arquitetura | Arquitetura: event-driven e mensageria — filas, tópicos e consistência eventual |
| 117 | arquitetura | Arquitetura: DDD — bounded contexts, agregados e ubiquitous language |
| 118 | arquitetura | Arquitetura: ADRs e governança de decisões — por que e como registrar |
| 119 | arquitetura | Arquitetura: resiliência — retry, circuit breaker, backoff e idempotência |
| 120 | designpatterns | Design patterns: creacionais — factory, builder e por que singleton é code smell |
| 121 | designpatterns | Design patterns: estruturais — adapter, facade e decorator |
| 122 | designpatterns | Design patterns: comportamentais — strategy, observer, template method e state |
| 123 | designpatterns | Design patterns: SOLID e como os padrões GoF derivam dele |
| 124 | designpatterns | Design patterns: anti-patterns comuns — god object, service locator e spaghetti |
| 125 | testes | Testes: pirâmide de testes e o que testar em cada camada |
| 126 | testes | Testes: TDD e quando ele compensa |
| 127 | testes | Testes: mocks, fakes e stubs (e quando evitar mockar) |
| 128 | testes | Testes: testes de contrato e testes de API |
| 129 | testes | Testes: cobertura de código como métrica — o que ela mostra e o que esconde |
| 130 | git | Git: fluxos de trabalho (trunk-based e git flow) e quando usar cada |
| 131 | git | Git: rebase vs merge e históricos limpos |
| 132 | git | Git: conventional commits e versionamento semântico |
| 133 | git | Git: resolver conflitos e reverter com segurança (revert, reset, cherry-pick) |
| 134 | apis-web | APIs: HTTP na prática (métodos, status, cabeçalhos, cache) |
| 135 | apis-web | APIs: REST, recursos, coleções, versionamento e hipermidia |
| 136 | apis-web | APIs: autenticação e autorização (sessions, JWT, OAuth2, API keys) |
| 137 | apis-web | APIs: serialização, contratos e GraphQL vs REST |
| 138 | bancos-dados | Bancos de dados: SQL vs NoSQL e o trade-off de consistência |
| 139 | bancos-dados | Bancos de dados: índices, planos de execução e custo de escrita |
| 140 | bancos-dados | Bancos de dados: transações, ACID e níveis de isolamento |
| 141 | bancos-dados | Bancos de dados: ORM vs SQL puro, migrations e schema drift |
| 142 | seguranca | Segurança: OWASP Top 10 aplicado na prática |
| 143 | seguranca | Segurança: autenticação e gestão de sessões seguras |
| 144 | seguranca | Segurança: criptografia — hashing, cifras, TLS e segredos |
| 145 | seguranca | Segurança: controle de acesso — RBAC/ABAC e menor privilégio |
| 146 | seguranca | Segurança: hardening e dependências vulneráveis — SBOM, CVE e supply chain |
| 147 | devops | DevOps: containers — camadas, imagens mínimas e non-root |
| 148 | devops | DevOps: pipelines de CI/CD — artefatos, ambientes e promoção |
| 149 | devops | DevOps: infraestrutura como código — Terraform e imutabilidade |
| 150 | devops | DevOps: observabilidade — logs estruturados, métricas e tracing (OTel) |
| 151 | linux | Linux: processos, sinais, systemd e supervisionamento |
| 152 | linux | Linux: arquivos, permissões, filesystems, inodes e links |
| 153 | linux | Linux: shell, pipelines, jq e automação via SSH |
| 154 | performance | Performance: profiling primeiro — onde o tempo realmente vai |
| 155 | performance | Performance: complexidade assintótica vs custo real |
| 156 | performance | Performance: caching em camadas e invalidação |
| 157 | performance | Performance: concorrência e paralelismo — quando vale a pena |
| 158 | python | Python: sintaxe e núcleo da linguagem |
| 159 | python | Python: GIL e concorrência |
| 160 | python | Python: idioms e boas práticas |
| 161 | python | Python: decoradores e metaprogramação |
| 162 | javascript | JavaScript: closures, escopo e hoisting |
| 163 | javascript | JavaScript: this, prototypes e herança |
| 164 | javascript | JavaScript: assincronismo (event loop, promises e async/await) |
| 165 | javascript | JavaScript: tipos, coerção e igualdade |
| 166 | typescript | TypeScript: sistema de tipos estrutural |
| 167 | typescript | TypeScript: generics e tipos condicionais |
| 168 | typescript | TypeScript: type narrowing, guards e type assertions |
| 169 | node | Node.js: event loop e I/O não bloqueante |
| 170 | node | Node.js: CommonJS, ESM e resolução de módulos |
| 171 | node | Node.js: streams e backpressure |
| 172 | bash | Bash: expansão, aspas e globbing |
| 173 | bash | Bash: exit codes, controle de fluxo e funções |
| 174 | java | Java: JVM, bytecode e memory model |
| 175 | java | Java: Garbage Collection e tuning |
| 176 | java | Java: Streams e lambdas |
| 177 | java | Java: Concorrência com threads e locks |
| 178 | kotlin | Kotlin: null-safety e sistema de tipos |
| 179 | kotlin | Kotlin: corrotinas e concorrência estruturada |
| 180 | kotlin | Kotlin: funções, propriedades e data classes |
| 181 | c | C: ponteiros, aritmética e gestão manual de memória |
| 182 | c | C: comportamento indefinido e o modelo de memória |
| 183 | c | C: strings C, buffers e funções inseguras |
| 184 | cpp | C++: RAII e gerenciamento de recursos |
| 185 | cpp | C++: move semantics, rvalue references e ownership |
| 186 | cpp | C++: templates, SFINAE, constexpr e o custo-zero |
| 187 | rust | Rust: ownership, borrow checker e o modelo de memória |
| 188 | rust | Rust: lifetimes, referências e elisão |
| 189 | rust | Rust: enums, pattern matching, Result e Option |
| 190 | rust | Rust: traits, generics e trait objects |
| 191 | csharp | C#: async/await, Task e o SynchronizationContext |
| 192 | csharp | C#: LINQ, execução diferida e IQueryable vs IEnumerable |
| 193 | csharp | C#: struct vs class, GC e alocação de memória |
| 194 | csharp | C#: injeção de dependência e ciclo de vida de serviços |
| 195 | golang | Go: goroutines, canais e CSP |
| 196 | golang | Go: interfaces implícitas, method set e composição |
| 197 | golang | Go: slices, maps e ponteiros |
| 198 | golang | Go: context, cancelamento e timeouts |
| 199 | php | PHP: modelo de execução e SAPI |
| 200 | php | PHP: sistema de tipos, arrays e coerção |
| 201 | php | PHP: PSRs, autoload e Composer |
| 202 | ruby | Ruby: tudo é objeto e duck typing |
| 203 | ruby | Ruby: blocks, procs e lambdas |
| 204 | ruby | Ruby: Rails — ActiveRecord e MVC |
| 205 | sql | SQL: modelagem relacional e normalização |
| 206 | sql | SQL: índices e estratégias de acesso |
| 207 | sql | SQL: joins e semântica de conjunto |
| 208 | sql | SQL: transações, ACID e dialetos |
| 209 | traducao | Princípios fundamentais da tradução: sentido, equivalência e fidelidade |
| 210 | traducao | Fidelidade x naturalidade: quando priorizar cada um |
| 211 | traducao | Estratégias de tradução: literal, semântica, adaptativa e quando usar cada uma |
| 212 | traducao | Falsos cognatos e armadilhas interlíngua (inglês-português) |
| 213 | traducao | Elementos culturalmente intraduzíveis: humor, trocadilhos, provérbios e onomatopeias |
| 214 | traducao | Pipeline de tradução de qualidade: análise, rascunho, revisão e QA |
| 215 | traducao | Tom e registro: formal, técnico, coloquial — como detectar e manter |
| 216 | traducao | Quando adaptar x quando manter o termo original (estrangeirismos e termos técnicos) |
| 217 | pt-br | Norma culta x coloquial no pt-BR: quando usar cada registro na tradução |
| 218 | pt-br | Variações PT-PT x PT-BR: reescrever para o brasileiro |
| 219 | pt-br | Formas de tratamento em pt-BR: você, tu, senhor/a e concordância |
| 220 | pt-br | Regionalismos brasileiros: como traduzir sem cair em gírias muito locais |
| 221 | pt-br | Siglas, acrônimos e nomes próprios: manter, traduzir ou adaptar |
| 222 | pt-br | Estrangeirismos no pt-BR: anglicismos aceitos, aportuguesamentos e quando recusar |
| 223 | traducao-texto | Tradução técnica: manuais, especificações e documentação de software |
| 224 | traducao-texto | Tradução literária: prosa e poesia — ritmo, voz e licença poética |
| 225 | traducao-texto | Tradução de interface e microcopias (UI): botões, erros e textos curtos |
| 226 | traducao-texto | Tradução adaptativa (transcreation) para marketing e publicidade |
| 227 | traducao-texto | Tradução jurídica: contratos e termos legais — precisão e terminologia |
| 228 | traducao-texto | Tradução científica e acadêmica: papers, abstracts e nomenclatura |
| 229 | traducao-texto | Tradução jornalística: notícias, manchetes e entrevistas |
| 230 | traducao-texto | Tradução de legendas embutidas (burned-in) e placas de cena |
| 231 | localizacao | Localização (l10n) vs internacionalização (i18n) vs transcreation |
| 232 | localizacao | Datas, horas e fuso horário no Brasil (dd/mm/aaaa, 24h, BRT) |
| 233 | localizacao | Números, moedas (R$) e percentuais no pt-BR |
| 234 | localizacao | Unidades de medida e convenções brasileiras (m, kg, °C, telefone, endereço) |
| 235 | localizacao | Localização de software: placeholders, plurais, gênero e espaço de UI |
| 236 | traducao-audio | Pipeline de tradução de áudio: STT -> tradução -> TTS |
| 237 | traducao-audio | Dublagem (versão): sincronização labial, tamanho da fala e naturalidade |
| 238 | traducao-audio | Legendagem: limite de caracteres, tempo em tela e leitura rápida |
| 239 | traducao-audio | Tradução de fala coloquial e falas sobrepostas em podcasts e entrevistas |
| 240 | traducao-audio | Tradução para narração TTS em pt-BR: pontuação, entonação e SSML |
| 241 | traducao-audio | Sotaques e variantes do português falado: transcrever sem distorcer o sentido |
| 242 | traducao-audio | Tradução de músicas e letras: adaptação rítmica x tradução literal |
| 243 | traducao-audio | Timing e sincronização de legendas: duração mínima, cps e corte por shot |
| 244 | traducao-audio | Palavras de preenchimento, hesitações e ruído na transcrição: quando manter ou remover |
| 245 | opencode+opencode | Aegis registrado como projeto irmao (Rust) |
| 246 | opencode+opencode | aegis barra progresso tempo real |
| 247 | opencode | triagem scripts legado orgaos movidos |
| 248 | opencode+opencode | fase2 limpeza git artefatos rastreados |
| 249 | opencode | fase3 rotina automatica de tiragem organizacional |
| 250 | opencode+opencode | Fix ativação de voz + Sistema de frases unificado |
| 251 | opencode+opencode | 2026-08-16: Detecção automática de inglês no TTS |
| 252 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | padrao organizacao comandos |
| 253 | opencode+opencode | 2026-08-17: Organograma agrupado por livro + técnicas de validação visual via adb |
| 254 | opencode+opencode | 2026-08-17: CAR-BT — controle total via adb (Bluetooth automotivo) |
| 255 | opencode+opencode | etapa19 tool permission runtime |
| 256 | opencode+opencode | etapa21 memory learning consolidation |
| 257 | opencode+opencode | etapa22 self assessment self improvement |
| 258 | opencode+opencode | etapa23 observability reliability |
| 259 | opencode | etapa24 interface jarvis |
| 260 | opencode | restauracao unified bridge |
| 261 | opencode+opencode+opencode+opencode | Correção de mojibake no knowledge_graph.json (UTF-8 lido como CP1252) |
| 262 | opencode+opencode+opencode+opencode+opencode | integrity guard vigilante dados |
| 263 | opencode+opencode | pronuncia python ptbr |
| 264 | opencode+opencode | resiliencia widget duplicado |
| 265 | opencode | saudacao dinamica jarvis |
| 266 | opencode | saudacao jarvis estilo filme |
| 267 | opencode | saudacao auto evolutiva jarvis |
| 268 | opencode | saudacao llm nvidia api |
| 269 | opencode+opencode | Como adicionar uma nova versão da Bíblia ao BibliaEstudoCompleta |
| 270 | opencode+opencode | Pipeline de release e padrão de toolbar com menu |
| 271 | opencode | Widget Jarvis - 8 Features Implementadas |
| 272 | opencode | Sistema de Análise Financeira |
| 273 | opencode | widget edge estabilizado fonte unica processos |
| 274 | opencode | TradingAgents integrado ao ecossistema |
| 275 | opencode | Resiliência de logs: encoding detectado na leitura, não presumido |
| 276 | opencode | Compressão Semântica Hierárquica — lições da implementação |
| 277 | opencode | Relatório Eco estático — lições |
| 278 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | CLI-Anything Internalizado como Habilidade Soberana |
| 279 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | @ecow e /ecow — abrir/focar o Cerebro Vivo |
| 280 | opencode | JunkScanner — Benchmark do scan incremental |
| 281 | opencode | JunkScanner — Scan incremental (cache de hash + memoização) |
| 282 | opencode | CI de Android em máquina fraca + keystore estável |
| 283 | opencode | Padrao de pergunta: validacao numerica por cota |
| 284 | opencode | Janela flutuante para visuais (sem navegador) |
| 285 | opencode | Estilo por pedido (Power BI implementado) |
| 286 | opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode | retencao opencode db vigilante |
| 287 | opencode+opencode | Narracao seletiva por relevancia no narrador Edge |
| 288 | opencode+opencode | terminalwidget edge |
| 289 | opencode+opencode | Análise de Jarvis opensource — aprendizados aplicáveis |
| 290 | opencode+opencode | Neurociência da fala aplicada ao Cérebro Vivo |
| 291 | opencode+opencode | deduplicacao memoria semantica |

## Bug Fixes e Corrigidos

### max_iterations hard stop forca parada prematura mesmo sem objetivo atingido
**Fonte:** ler_auditoria
**Causa Raiz:** Loop principal usava while self.iteration < self.max_iterations (100) como criterio de saida, ignorando se o objetivo foi alcancado
**Correcao:** Substituido por deteccao de estagnacao: 30 iteracoes sem progresso. max_iterations subiu para 1000 como seguranca.

### Score < threshold mas sem failed_steps ia direto para SUCCESS_VERIFIED
**Fonte:** ler_auditoria
**Causa Raiz:** _phase_success_eval verificava apenas failed_steps, nao o score real. Se todos steps 'completaram' com bugs, LER considerava sucesso.
**Correcao:** Score < threshold sempre vai para REPLANNING. Idem para _phase_final_audit.

### Executor nao validava resultado real da implementacao
**Fonte:** ler_auditoria
**Causa Raiz:** _action_implement retornava string fixa sem verificar se arquivos foram modificados. _action_test so reportava numero de testes sem all_passed.
**Correcao:** Executor agora verifica git diff --stat e git status apos implement/fix/refactor. Testes reportam all_passed.

### Nao havia feedback loop do usuario — LER terminava mesmo se objetivo nao fosse atingido
**Fonte:** ler_auditoria
**Causa Raiz:** COMPLETED -> _finalize direto, sem perguntar ao usuario se o resultado foi satisfatorio
**Correcao:** Adicionado _ask_user_feedback() em _finalize e _handle_complete. Se usuario rejeita, registra failed_pattern e chama _restart_mission().

### Persistencia sem atomicidade — crash no meio do json.dump corrompia arquivo
**Fonte:** ler_auditoria
**Causa Raiz:** Escrita direta com json.dump() sem arquivo temporario
**Correcao:** Todas escritas usam arquivo .tmp + os.replace() (atomico em ext4/NTFS).

### Logs sem rotacao — logs cresciam indefinidamente
**Fonte:** ler_auditoria
**Causa Raiz:** Session.log escrevia sempre no mesmo arquivo sem limite de tamanho
**Correcao:** _rotate_log() rotaciona em 5 niveis ao atingir 512KB.

### Executor.results sem limite — memoria crescia indefinidamente
**Fonte:** ler_auditoria
**Causa Raiz:** results dict acumulava resultados sem nunca remover entradas antigas
**Correcao:** MAX_RESULTS=50, remove entrada mais velha ao estourar.

### Code duplication entre checkpoint.py e persistence.py (~200 linhas duplicadas)
**Fonte:** ler_auditoria
**Causa Raiz:** Duas implementacoes paralelas de save/load JSON com logica identica
**Correcao:** Unificado via atomic_write_json()/atomic_read_json() em checkpoint.py, persistence.py delega.

### -------
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** -----------
**Correcao:** -----

### Artist shows "Desconhecido"
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** YouTube MP3s have no ID3 tags
**Correcao:** Extract artist from filename (first dash segment or second double-space segment)

### Search returns wrong artist
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** iTunes BR returns irrelevant results
**Correcao:** Scoring threshold system: NORMAL min=5/3, RELAXED min=3/2

### Album art not found
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Cover Art Archive redirect to archive.org fails
**Correcao:** Explicit redirect loop + iTunes artwork fallback with US store

### Logs don't appear
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** MIUI logcat filtering
**Correcao:** Toast messages as visual feedback

### Filename ambiguity
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Multiple filename formats
**Correcao:** Try dash split first, then double-space split as fallback

### AcoustID always fails
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Invalid API key `4m9Q2k9p` (HTTP 400)
**Correcao:** Accepted as non-critical; search falls through to iTunes/MusicBrainz

### First search returns nothing
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Wrong artist extracted from filename, or title too noisy
**Correcao:** Auto-fallback: NORMAL→RELAXED auto-retry; RELAXED tries title-only and artist-only queries

### User sees wrong/short results
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Scoring rejected borderline-but-correct match
**Correcao:** User taps "Tentar Novamente" in dialog → triggers RELAXED mode with lower thresholds

### **Audio stops / EQ not audible**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `EqualizerAudioProcessor.queueInput()` never calls `inputBuffer.position(inputBuffer.limit())` after processing. ExoPlayer sees 0 bytes consumed → audio pipeline stalls. Also `isActive()` was initiall
**Correcao:** 1. Call `inputBuffer.position(inputBuffer.limit())` after successful processing. 2. Make `isActive()` always return `true`; use internal `isActiveState` flag to decide bypass vs processing inside `que

### **Preset not persisting across sessions**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** The preamp was baked into `currentGains[]` making it irreversible. `syncSoftwareEq()` passed preamp=0 to processor so preamp was never audible.
**Correcao:** **Refactored:** `currentGains[]` now stores RAW gains only, `currentPreamp` is separate. `applyPreset()` no longer bakes preamp into gains. `syncSoftwareEq()` passes `currentPreamp` to processor. Adde

### **Preamp volume irreversible and cumulative**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `showVolumeDialog()` did `currentGains[i] += v` on already-baked gains. Each call added more, preamp could never be undone without reset.
**Correcao:** Fixed by the same refactoring: preamp is now separate. `showVolumeDialog()` only updates `currentPreamp` and re-applies HW EQ bands without touching `currentGains[]`.

### **Preamp not audible**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `syncSoftwareEq()` always called `mp.setEqPreampGain(0f)`, ignoring `currentPreamp`. The preamp was only baked into HW EQ gains, never sent to software EQ.
**Correcao:** `syncSoftwareEq()` now calls `mp.setEqPreampGain(currentPreamp)` instead of `0f`. Software EQ receives preamp as a master multiplier.

### **Duplicate mini-player on some screens**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `openNowPlaying()` could be called multiple times, adding duplicate fragments.
**Correcao:** Added guard at start of `openNowPlaying()`: if backstack top is already "now_playing", return early.

### **EQ distorts audio at boost settings**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** 20 cascaded peaking filters + preamp can push signal past 1.0. `coerceIn(-1f, 1f)` causes hard clipping distortion.
**Correcao:** Replaced `coerceIn(-1f, 1f)` with `Math.tanh(sample)` — soft-clipping (tube-like saturation). Also made `isActive()` always return `true` to prevent ExoPlayer from caching the inactive state.

### **Preset data corrupted on pt_BR locale**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `"%.1f".format(-4.0)` produces `"-4,0"` (comma decimal) on Brazilian locale. `joinToString(",")` uses same comma → data splits into 2x the expected parts.
**Correcao:** Changed separator to `

### **EQ still distorts at high boost**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `tanh()` soft-clipping alone insufficient — 20 cascaded peaking filters + preamp can produce cumulative gain >> 6 dB at certain frequencies, exceeding `tanh()` saturation threshold.
**Correcao:** Added peak limiter in `queueInput()`: measure peak after filter cascade, apply gain reduction (1.0/peak) with per-sample attack/release smoothing (1ms attack, 100ms release). `tanh()` remains as final

### **No EQ on/off button**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** User had no way to bypass EQ without resetting all gains to zero.
**Correcao:** Added `enabled` flag in `EqualizerAudioProcessor`, `setEnabled()` method, `Switch` widget in fragment header (default ON). Toggle disables both HW and SW EQ.

### **No visual limiting feedback**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** User couldn't see when limiter was active or how much reduction was applied.
**Correcao:** Added `gainReductionDb` property on processor, `TextView` indicator in bottom bar (green=no reduction, yellow=moderate, red=heavy), polled every 250ms via Handler.

### **EQ state not persisted**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** EQ enabled/disabled state not saved to SharedPreferences — switch reset to ON on every restart.
**Correcao:** Added `KEY_ENABLED` to `saveActivePreset()`/`loadActivePreset()`. Uses `restoringEqState` flag to prevent listener firing during restoration.

### **No most-played tracking**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** App had no mechanism to count or sort by play frequency.
**Correcao:** Added `PlayCountManager` (JSON in SharedPreferences), increment on `playSongFromList()`, `SortMode.PLAY_COUNT` in `SongAdapter.sortSongs()`, "Mais Tocadas" option in sort dialog.

### **EQ only applies after opening fragment**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** Saved gains/preamp never loaded into processor until `EqualizerFragment.loadActivePreset()` runs. Playing a song without opening EQ meant processor stayed flat.
**Correcao:** Added `EqStateLoader.restoreTo()` — loads same SharedPreferences used by fragment and applies to processor. Called in `playSongFromList()` before playing.

### **EQ deactivates on song change**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `AudioProcessor.reset()` set `isActiveState = false` and `configure()` never recalculated it. ExoPlayer calls `reset()` between songs → processor silently bypassed.
**Correcao:** Added `updateActiveState()` call in `configure()` and `reset()`. Removed `isActiveState = false` from `reset()` — state is now always recalculated from actual gains/enabled.

### **EQ toggle button not visible**
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** `Switch` widget may not render correctly on some MIUI versions or was too small to notice.
**Correcao:** Replaced `Switch` with `Button` styled as toggle (`EQ ON`/`EQ OFF`), matching existing button styles (`bg_preset_active`/`bg_preset_btn`). Uses `isSelected` for state.

### ** Track the best score across all results and only return if minimum threshold is met. Perfect matc
**Fonte:** mp3player-metadata-rescue

### ** Use explicit redirect following in download function (manual loop for 3xx codes)
**Fonte:** mp3player-metadata-rescue

### -------
**Fonte:** mp3player-metadata-rescue
**Causa Raiz:** -----------
**Correcao:** -----

### OpenCode Go provider crash ao processar mensagem
**Fonte:** sessao_providermanager
**Causa Raiz:** _simulate_completion() tratava request.messages[-1] como dict sempre, mas ultima msg pode ser string
**Correcao:** Adicionado isinstance(last, dict) check; se for string, usa como prompt direto

### MCP server nao respondia nenhum comando
**Fonte:** sessao_providermanager
**Causa Raiz:** Faltava handler para metodo initialize, que e obrigatorio no protocolo MCP
**Correcao:** Adicionado _handle_initialize() com resposta de protocolVersion/capabilities

### auth.json com entradas de chave NVIDIA disfarcadas de outros provedores
**Fonte:** sessao_limpeza_auth
**Causa Raiz:** auth.json continha 5 entradas, 2 com chaves nvapi-... mascaradas como deepseek-ai e outra
**Correcao:** Removidas entradas invalidas mantendo apenas github-copilot (oauth), nvidia (api key), deepseek (api key legitimo)

### Cliques falhando em SPA apos navegacao
**Fonte:** treinamento_navegacao
**Causa Raiz:** Stale element reference: o DOM foi substituido pelo React/Vue mas a referencia ao elemento antigo permanece
**Correcao:** Re-query pelo seletor apos cada navegacao; usar waitForSelector com timeout no novo DOM em vez de manter referencia

### send_keys nao funciona em campos rich-text
**Fonte:** treinamento_navegacao
**Causa Raiz:** Contenteditable e iframes rich-text nao tem input visivel; eventos de teclado nao sao processados
**Correcao:** Clicar no elemento, executar JS para limpar (editor.innerHTML=''), depois enviar caracteres via execCommand('insertText') ou dispatchEvent de InputEvent

### Elementos nao encontrados em Shadow DOM
**Fonte:** treinamento_navegacao
**Causa Raiz:** Shadow DOM encapsula elementos; querySelector normal nao penetra shadowRoots
**Correcao:** Navegar pela arvore de shadowRoots: element.shadowRoot.querySelector(...); usar caminho completo com parent.shadowRoot.child.shadowRoot

### Cliques em coordenadas erram alvo em resolutions diferentes
**Fonte:** treinamento_navegacao
**Causa Raiz:** Coordenadas absolutas nao escalam entre dispositivos ou janelas redimensionadas
**Correcao:** Calcular coordenadas como porcentagem da viewport: x = viewportWidth * 0.5, y = viewportHeight * 0.75; obter viewport via window.innerWidth/innerHeight

### Permission dialogs do MIUI bloqueiam instalacao de APK
**Fonte:** treinamento_navegacao
**Causa Raiz:** MIUI/HyperOS adiciona dialogs de permissao apos instalacao que nao existem no Android AOSP
**Correcao:** Apos adb install, aguardar 3s e aceitar dialog com adb shell input tap com coordenadas do botao 'Permitir'; se falhar, tentar 'Permitir somente durante o uso'

### Dropdown<select> nao responde a send_keys ou click
**Fonte:** treinamento_navegacao
**Causa Raiz:** Selects estilizados (custom dropdowns) substituem o elemento <select> nativo por uma div com opcoes ocultas
**Correcao:** Clicar no select para abrir, depois clicar na opcao pelo texto visivel; se nao funcionar, usar JS para setar valor e disparar evento change

### MCP server Failed to get tools no OpenCode
**Fonte:** provider_mcp_server.py:52-55
**Causa Raiz:** Server respondia a notifications JSON-RPC (requests sem id), quebrando protocolo
**Correcao:** handle_request() retorna None se req_id is None; run() so escreve resposta se not None

### MCP server nao respondia a tools/call
**Fonte:** provider_mcp_server.py
**Causa Raiz:** Method tools/call nao estava no dispatch de handle_request()
**Correcao:** Adicionado elif method == tools/call e _handle_tools_call() com mapping de nomes

### HTTP 401 Unauthorized on /session and /global/sessions/*
**Fonte:** ecosistema-opencode
**Causa Raiz:** opencode serve was started with OPENCODE_SERVER_PASSWORD=521cf1f4-... (Windows user env var) but .env was updated to edbe7432-... and serve was never restarted
**Correcao:** Updated Windows HKCU env var to match .env password, killed stale serve (PID 4724), started new serve (PID 4216) with correct password

### _ensure_serve() spawns opencode serve without passing env context
**Fonte:** ecosistema-opencode
**Causa Raiz:** asyncio.create_subprocess_exec inherits parent env, but explicit env ensures correct OPENCODE_SERVER_PASSWORD is propagated to serve child process
**Correcao:** Added env={**os.environ} to _ensure_serve() and _ensure_serve_global() in jarvis_bridge.py; run_serve.py now loads .env and passes env explicitly

### gerar_audio() blocks until full TTS generation, no streaming
**Fonte:** ecosistema-opencode
**Causa Raiz:** gerar_audio accumulated all edge-tts chunks into single base64 before sending to client; no incremental audio delivery
**Correcao:** Added gerar_audio_stream() async generator yielding base64 chunks incrementally; modified ws_responder to send audio_streaming/audio_chunk/audio_done messages for progressive playback

### STT no partial/streaming results
**Fonte:** ecosistema-opencode
**Causa Raiz:** _stt_whisper joined all Whisper segments at once; onPartialResults callback in VoxStt.kt was empty
**Correcao:** Added partial_callback parameter to _stt_whisper for incremental segment reporting; implemented onPartialResults in VoxStt.kt to forward partial text to UI

### VoxAudioPlayer temp file leak on exception
**Fonte:** ecosistema-opencode
**Causa Raiz:** tempFile variable was scoped inside try block; if exception before MediaPlayer setup, tempFile was orphaned; stop() before play() could leave old tempFile undeleted
**Correcao:** Promoted tempFile to function scope with null-safe cleanup in catch block; VoxAudioPlayer.kt now uses var tempFile: File? = null and deletes in all error paths

### Loop infinito de push no Vigilante (emails do GitHub a cada minuto)
**Fonte:** opencode
**Causa Raiz:** Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente
**Correcao:** ---
tipo: bug
tags: [vigilante, github, git-sync, loop-infinito, memory-engine, push, automacao]
data: 2026-08-08
contexto: Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente
decisao: Remover log de git-sync do loop do vigilante + excluir EcoSystemUmGrau da a

## Padroes Cognitivos

### Debugging em cascata reversa
**Dominio:** debugging
**Fonte:** meta_cognition

Quando um bug nao tem causa obvia, comeca pela saida (sintoma) e traca o caminho inverso ate a entrada. Para cada passo, pergunte: 'Se este componente funcionasse corretamente, o que eu veria?' Quando a resposta nao corresponde a realidade, voce encontrou o componente defeituoso. Mais eficiente que debugar pra frente porque elimina ramos inteiros da arvore de causas.

Quando metodo A falha, nao repetir A - descer para metodo B imediatamente. Ex: click() falhou? Tenta keyboard. Keyboard falhou? T

### Hipotese-falsificacao terminal
**Dominio:** debugging
**Fonte:** meta_cognition

Para cada hipotese de causa, execute o experimento MAIS RAPIDO que pode FALSIFICA-LA, nao confirma-la. Se a hipotese for 'o arquivo X nao foi carregado', nao verifique se X foi carregado (confirmacao), mas sim INTRODUZA UM ERRO OBVIO em X e veja se o sintoma muda (falsificacao). Isso eviesa para descobrir a verdade rapidamente em vez de acumular evidencias confirmatorias.

### Lei de Postel aplicada a engenharia
**Dominio:** architecture
**Fonte:** meta_cognition

'Seja conservador no que voce envia, seja liberal no que voce aceita.' Outputs devem ser rigorosos (validacao estrita, tipos fortes, contratos explicitos). Inputs devem ser tolerantes (defaults, fallbacks, parsing flexivel). Isso cria sistemas que funcionam com peers imperfeitos sem propagar erros. Exemplo pratico: seu modulo deve falhar ruidosamente em erros internos mas silenciosamente em erros externos recuperaveis.

### Principio da separacao causa-efeito-temporal
**Dominio:** debugging
**Fonte:** meta_cognition

Em sistemas distribuidos ou assincronos, a CAUSA de um bug pode ter ocorrido muito antes do EFEITO ser observado. Nao procure perto do sintoma. Trace estados globais (logs, snapshots, checkpoints) para encontrar quando o estado correto foi violado, nao quando o erro foi reportado. Exemplo: crash no ExoPlayer 30s apos iniciar musica pode ser causado por configuracao do Equalizer que foi aplicada no momento 0.

### Estrategia de fallback em cadeia (Chain of Responsibility)
**Dominio:** system_design
**Fonte:** meta_cognition

Quando uma operacao tem multiplas fontes de dados possiveis, organize-as em ordem de preferencia (mais precisa primeiro) com fallback automatico para a proxima. Cada fonte deve reportar claramente se conseguiu ou nao. Nao pare no primeiro resultado — avalie todos e escolha o melhor. Exemplo: MetadataSearch usa AcoustID (fingerprint) -> iTunes BR (scoring) -> MusicBrainz (detalhado) -> iTunes US (fallback).

### Validacao contra-intuitiva: teste o erro, nao o acerto
**Dominio:** testing
**Fonte:** meta_cognition

Para cada funcao, o teste mais valioso nao e o 'caminho feliz' mas sim: (1) entrada vazia/nula, (2) entrada no limite, (3) entrada fora do dominio, (4) estado inconsistente, (5) concorrencia. Se sua funcao lida com arquivos: arquivo inexistente, permissao negada, disco cheio, arquivo corrompido. 80% dos bugs estao nos 20% de casos de erro.

### Padrao de escrita atomica para persistencia
**Dominio:** system_design
**Fonte:** meta_cognition

NUNCA escreva diretamente no arquivo final. Escreva em um arquivo temporario (.tmp) e use rename atomico (os.replace() no Python, MoveFileEx on Windows, mv no Linux). O rename e atomico a nivel de sistema de arquivos em NTFS e ext4: ou o arquivo inteiro aparece, ou o antigo permanece. SEMPRE. Isso previne corrupcao por crash no meio da escrita. Leitura: se o .tmp existe e o final nao, ignore o .tmp (escrita abortada).

### Estrategia de loop autonomo: planejar-executar-verificar-corrigir
**Dominio:** system_design
**Fonte:** meta_cognition

Qualquer sistema autonomo segue um ciclo fechado: (1) Planejar: decompor objetivo em passos verificaveis. (2) Executar: rodar cada passo com ferramentas reais. (3) Verificar: validar saida contra criterios objetivos (git diff, test pass, compilacao). (4) Corrigir: se falhou, registrar causa, replanejar, tentar de novo. O loop termina apenas quando TODOS os criterios de sucesso sao atingidos. Nao use max_iterations como criterio de parada — use deteccao de estagnacao (nenhum progresso em N iterac

### Modelo de scoring para busca multi-resultado
**Dominio:** algorithm
**Fonte:** meta_cognition

Quando uma busca retorna multiplos resultados, nao aceite o primeiro. Atribua scores: match exato + peso alto, match parcial + peso medio, overlap lexical + peso baixo. Defina thresholds por modo (estrito vs relaxado). Acompanhe o melhor score entre TODOS os resultados, nao apenas o primeiro. Retorne null se nenhum resultado atingir o threshold minimo — e melhor falhar que retornar informacao errada. O usuario pode entao tentar modo relaxado.

### Diagnostico por eliminacao em config complexa
**Dominio:** debugging
**Fonte:** session

Quando config tem multiplos componentes (provedores, servidores, MCP), isolar cada camada: testar provider isolado -> testar servidor -> testar MCP handshake -> testar chain completo

### Pattern matching por estrutura de UI
**Dominio:** ui-recognition
**Fonte:** session

Toda interface segue padroes reconheciveis: modais tem header+body+footer, tabelas tem thead+tbody, listas sao scrollaveis com items repetidos, formularios tem labels+inputs. Reconhecer o padrao estrutural e mais rapido que ler cada elemento individualmente

Digitalizar a tela em zonas: topo = header/nav, esquerda = sidebar/menu, centro = conteudo principal, direita = paineis auxiliares, fundo = modais/overlays. Saber onde procurar cada tipo de elemento reduz tempo de busca em 60%

### Modelo mental de DOM virtual
**Dominio:** web-rendering
**Fonte:** session

SPAs (React/Vue/Angular) mantem DOM virtual que difere do DOM real. Mudancas de estado nao sao imediatamente visiveis no DOM real. Esperar pelo menos 1 ciclo de renderizacao (requestAnimationFrame ~16ms) apos cada acao antes de consultar o DOM

### Reconhecimento de estado por elementos-chave
**Dominio:** state-detection
**Fonte:** session

Cada estado da UI tem elementos-charada: loading tem spinner, empty state tem 'Nenhum resultado', erro tem mensagem vermelha, sucesso tem toast verde. Identificar o estado pelo elemento unico e mais rapido que validar condicoes complexas

### Pre-compilacao de estrategia de interacao
**Dominio:** planning
**Fonte:** session

Antes de agir, mentalmente compilar toda a sequencia de passos: (1) onde estou, (2) onde quero chegar, (3) quais elementos preciso atravessar, (4) quais barreiras possiveis (modais, permissoes). Agir sem plano causa 3x mais erros

### Reconhecimento instantaneo de framework
**Dominio:** framework-detection
**Fonte:** session

Identificar o framework da interface em <500ms: React tem #root vazio, Vue tem #app, Angular tem <app-root>, jQuery tem muitos elementos com IDs, Bootstrap tem classes container/row/col, Material UI tem Mui-* classes. Framework define o comportamento da navegacao

### Ciclo OODA aplicado a navegacao
**Dominio:** decision-making
**Fonte:** session

Observe (scan estado atual) -> Orient (identifique padroes e framework) -> Decide (escolha metodo de interacao) -> Act (execute). Ciclo completo leva <1s para interfaces familiares, <3s para desconhecidas. Repetir apos cada interacao

### Heuristica de densidade de informacao
**Dominio:** efficiency
**Fonte:** session

Quanto mais texto/icones em uma tela, mais provavel que o elemento desejado esta em um sub-grupo (modal, accordion, tab). Telas densas quase sempre tem informacao escondida em componentes colapsaveis. Procurar botoes 'Expandir', 'Ver mais', 'Mostrar detalhes'

### Antecipacao de comportamento adaptativo
**Dominio:** adaptability
**Fonte:** session

Interfaces modernas sao adaptativas: mudam layout em resize, escondem elementos em mobile, alteram labels por A/B testing. Nunca assumir que um elemento estara no mesmo lugar da ultima vez. Sempre re-scannear o estado atual antes de interagir

### Mapa mental de navegadores web
**Dominio:** browser-architecture
**Fonte:** session

Navegadores modernos sao multi-processo: processo browser (UI), processo renderer (DOM/JS), processo GPU (composicao). Cada processo e isolado. Crash no renderer nao derruba o browser. Cada aba tem seu proprio processo renderer. DevTools roda no processo browser

### Espera adaptativa por tipo de recurso
**Dominio:** performance
**Fonte:** session

Tempos de carregamento variam por tipo: HTML inicial (rede), CSS (bloqueante ate parsed), JS (bloqueante ate executed), imagens (nao bloqueantes), fontes (FOUT/FOIT), API calls (variavel). Navegacao so esta completa quando HTML+CSS+JS processaram. Imagens podem continuar carregando

### # 2026-07-27 - Setup Plug & Play e organizacao GitHub
**Dominio:** general
**Fonte:** opencode

# 2026-07-27 - Setup Plug & Play e organizacao GitHub

## O que foi feito
- Repositorios do GitHub mapeados: 11 existentes, nenhum LER separado
- setup.bat criado: script unico para qualquer PC novo (clona, instala, configura, pede API keys)
- config/opencode.jsonc: template com {{USERPROFILE}} placeholder para geracao dinamica
- config/agents/: fonte unica dos 15 agentes OpenCode (repo eh source of truth)
- config/opencode-model-fallback.jsonc: config do plugin fallback
- Vigilante atualizado:


### # 2026-07-27 - Correcao dos 4 pontos finais do ecossistema
**Dominio:** general
**Fonte:** opencode

# 2026-07-27 - Correcao dos 4 pontos finais do ecossistema

## Problemas resolvidos
1. **Paths fixos**: vigilante.ps1, ecosystem.ps1, SKILL.md agora usam env:USERPROFILE
2. **LER vs OpenCode**: documentado que LER tem engine MODULES (Python), OpenCode tem AGENTES (LLM). Sao complementares, nao duplicados.
3. **ecosystem learn**: varredura proativa que escaneia projetos Android + registra no knowledge graph
4. **Vigilante aprende sozinho**: timer diario executa ecosystem learn automaticamente
5.


### Encoding-aware diagnostics
**Dominio:** debugging
**Fonte:** ler_aprendizado

Ao diagnosticar arquivos JSON no Windows, sempre especificar encoding=utf-8. O default cp1252 pode mascarar arquivos perfeitamente validos como corrompidos.

### Entender antes de criar: ontologia de habilidades
**Dominio:** metacognicao
**Fonte:** ler_aprendizado

Antes de catalogar habilidades, estude a taxonomia existente. O que parece habilidade pode ser ferramenta, conhecimento ou skill.

### Gramática do Português Brasileiro — Guia prático do dia a dia
**Dominio:** general
**Fonte:** opencode

# Gramática do Português Brasileiro — Guia prático do dia a dia

- **Data:** 01/08/2026
- **Sessão:** Aprendizado permanente — gramática PT-BR para uso contínuo em comunicações

## Propósito
Este guia é o referencial de gramática do Português Brasileiro que todo agente deve
usar no dia a dia: TTS, transcrições, textos, documentação e conversas. Focado no
uso prático, sem jargão acadêmico desnecessário.

## Ortografia e acentuação
- Acentuação segue o novo acordo ortográfico (em vigor no Brasil d

### Habilidade: Navegação Perita — Internet, PC e Celular
**Dominio:** general
**Fonte:** opencode

# Habilidade: Navegação Perita — Internet, PC e Celular

- **Data:** 01/08/2026
- **Sessão:** Criação da habilidade de navegação perita com pesquisa de ferramentas no GitHub

## Resumo
Criada a habilidade `navegacao-perita` no catálogo do ecossistema (Habilidades/tecnicas/navegacao-perita/skill.md),
registrada no `manifesto_geral.json`, cobrindo as três frentes: navegador (internet), programas do PC (Windows)
e aplicativos de celular (Android). Baseada em pesquisa do estado da arte de ferramenta

### Pronúncia "Járvis" (escrita sem acento, fala com acento)
**Dominio:** general
**Fonte:** opencode

# Pronúncia "Járvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **Sessão:** Pedido direto do usuário sobre pronúncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **Pronúncia (fala/TTS):** "Járvis" — acento tônico no primeiro A (JA-rvis, fonético: /ˈʒaʁ.vis/).
- Nunca pronunciar "Jár-vis" com o segundo A fechado nem com acento na última sílaba ("Jarvís").

## Implementação
- Registrado em `scripts/pronuncias.json`:
  `"jarvis": 

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [obsidian, widget, grafo, arquitetura]
data: 2026-08-02
contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho
decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automaticamente.
impacto: Cére

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [teste, pipeline]
data: 2026-08-02
contexto: Teste funcional do pipeline de tags semanticas ponta a ponta
---

# Teste de integração do pipeline de tags semânticas

Este é um arquivo de teste temporário para validar que as tags semânticas
fluem da origem até o grafo do widget.

## Decisão

Integrar extração RAKE leve no knowledge_consolidator, generate-obsidian-notes
e memory_engine para enriquecer as sinapses do grafo Obsidian.

## Impacto

O grafo do widget deve mostrar ma

### # 2026-08-03 - Scan proativo: claude-code-extra-agents
**Dominio:** general
**Fonte:** opencode

# 2026-08-03 - Scan proativo: claude-code-extra-agents
## Marcadores encontrados
- adapt_agent_prompts.py: 1 marcadores
- generate_sample_results.py: 3 marcadores
- install.ps1: 1 marcadores



### MCP Obsidian server — vault consumido pelo LLM
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM só via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteúdo. Busca semântica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas não os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar sc

﻿--

### # Hora na tela vs hora no áudio (Jarvis)
**Dominio:** general
**Fonte:** opencode

# Hora na tela vs hora no áudio (Jarvis)

- **Data:** 31/07/2026
- **Sessão:** Implementação de `normalizar_hora_display()` na bridge

## Problema
O LLM reescrevia a hora do briefing/saudação em forma falada ("23 horas e 29",
"22 horas em ponto", "meia-noite") no próprio TEXTO exibido no app. O usuário
deixou claro: **o formato exibido deve continuar `21:44`; só a PRONÚNCIA do
Jarvis precisava ser corrigida.**

## Solução (divisão de responsabilidades)
- `melhorar_fala(texto)` â†’ 

# Aprendizad

### # Aprendizado — 2026-07-31 — Pontuação automática de transcrições de voz (Jarvis)
**Dominio:** general
**Fonte:** opencode

# Aprendizado — 2026-07-31 — Pontuação automática de transcrições de voz (Jarvis)

## Contexto
- O Android STT (SpeechRecognizer) devolve texto corrido, sem pontuação e **sem prosódia** (a melodia da fala não chega à bridge). O usuário pediu: `?` em perguntas, pontuação correta e **primeira letra maiúscula** sempre.
- Já existia `fix_punctuation()` básico; a reivisão ampliou regras e corrigiu um bug de acentuação.

## O que foi feito (`scripts/jarvis_bridge.py`)
1. **Clas

# Aprendizado — 2026-0

### # Guia: Controle Total de TV LG webOS (reaproveitável)
**Dominio:** general
**Fonte:** opencode

# Guia: Controle Total de TV LG webOS (reaproveitável)
**Criado:** 01/08/2026 | Aplica-se a qualquer TV LG webOS (UT80 e similares, 2024+)

> **Know-how de ouro:** este passo-a-passo reaplica-se a qualquer TV LG webOS. Só muda o IP e o MAC.

## 1. Descoberta e identificação
- **mDNS (224.0.0.251:5353):** pergunte por `_googlecast._tcp.local`, `_airplay._tcp.local`, `_webos._tcp.local`, `_services._dns-sd._udp.local`. A TV responde com hostname + TXT records (model, serialNumber, manufacture

### # 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memória
**Dominio:** general
**Fonte:** opencode

# 2026-08-01 - OpenCode Desktop: crash do renderer por GPU + fechamento por memória

**Categoria:** aprendizado
**Contexto:** OpenCode Desktop v1.18.10 (Electron 42.3.3) em notebook com Intel HD Graphics 5500 (driver 10.18.15.4248, 2015) e 3,9 GB RAM. A interface abria e fechava logo em seguida, sem mensagem de erro.
**Projeto:** EcoSystemUmGrau (infraestrutura OpenCode Desktop)
**Agentes envolvidos:** opencode CLI (build), 10-aprendizado

## O que foi feito

Investigação exaustiva do ciclo 

--

### # 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo
**Dominio:** general
**Fonte:** opencode

# 2026-08-02 - ecosystem sync: 1 comando para sincronizar tudo

## Contexto
O usuário queria sincronizar o ecossistema inteiro com um único comando, para ficar
sempre atualizado e nada se perder ao trocar de PC.

## O que foi feito
- Corrigido `scripts/ecosystem.ps1`:
  - `$ecoDir` agora é auto-detectado via `Split-Path $PSScriptRoot -Parent` (antes
    hardcoded `Desktop\Codigos\EcoSystemUmGrau`, que não existe mais — o repo vive em
    `Documents\Default Project\EcoSystemUmGrau`).
  - `

### Servidores MCP Node criados e validados
**Dominio:** general
**Fonte:** opencode

---
tipo: padrao
tags: [mcp, infraestrutura, config, clausula-petrea]
data: 2026-08-02
contexto: Divergência detectada — config/opencode.jsonc referenciava 4 servidores MCP Node em `mcp-servers/mcp-servers/...` que não existiam, e `{{USERPROFILE}}` não é resolvido em comandos MCP (apenas em instructions). `opencode mcp list` mostrava eco-knowledge/filesystem/search/terminal como "failed".
decisao: Criar os 4 servidores Node (filesystem, search, terminal, github) em `mcp-servers/<nome>/ind

﻿---


### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags:
  - setup
  - scheduled-task
  - portabilidade
data: 2026-08-02
contexto: Vigilante estava inativo porque nenhum mecanismo criava a scheduled task. Corrigido manualmente; faltava fechar o ciclo no setup.bat para PCs novos.
decisao: Adicionado passo 7/9 ao setup.bat que cria a task EcoSystemVigilante via Register-ScheduledTask (AtLogOn, StartWhenAvailable, restart 3x, sem -Principal para nao exigir admin). Verificacao previa com schtasks /Query; se ja existir, pula.
impac

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags:
  - vigilante
  - scheduled-task
  - bootstrap
  - windows
data: 2026-08-02
contexto: Status do ecossistema reportava "Vigilante: INATIVO" sem PID e sem log.
decisao: Diagnosticado que nenhum mecanismo criava a scheduled task. Criada task via Register-ScheduledTask (AtLogOn, sem -Principal para nao exigir admin), profile.ps1 recriado com as funcoes (start/stop/status-vigilante + ecosystem), path hardcoded corrigido para $env:USERPROFILE.
impacto: Vigilante agora inicia no l

### Cláusula Pétrea — Ativação de Voz (Eco System)
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [voz, eco, clausula-petrea, bridge, config, regras]
data: 2026-08-02
contexto: O usuário pediu que o sistema de voz seja ativável em qualquer sessão do OpenCode (nova ou em andamento) com os comandos "Ativar Eco" e "Desativar Eco", seguindo as regras do EcoSystemUmGrau.
decisao: Adicionada a CLÁUSULA PÉTREA — ATIVAÇÃO DE VOZ — ECO SYSTEM à Constituição (config/agents/00-system-rules.md) e sincronizada nas 3 camadas (AGENTS.md regenerado via sync_rules.py, d

﻿---
tipo: de

### # 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView
**Dominio:** general
**Fonte:** opencode

# 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botões de filtro no topo da aba "Músicas": Todas, Favoritas, A-Z, Lista, Sel. O texto não aparecia — os botões ficavam verdes uniformes sem nenhum texto visível.

## O que deu errado

### 1. Mudança de tema AppCompat â†’ MaterialComponents quebrou os botões
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao 

---
tipo: ap

### # 2026-07-30 - Skill de Diagnóstico Remoto Android
**Dominio:** general
**Fonte:** opencode

# 2026-07-30 - Skill de Diagnóstico Remoto Android

## O que foi criado
- `scripts/android_diagnostics.py` — Script Python que conecta via ADB ao dispositivo `100.64.71.9:5555` e coleta diagnóstico completo do VoxUmGrau
- `skills/android-diagnostics/skill.md` — Skill documentando o uso do script

## Capacidades do diagnóstico
- Modelo do dispositivo, versão Android, SDK, fuso horário
- Bateria (nível, temperatura, status de carga)
- Aplicativo (versãoCode, versionName, PID, memória 

﻿# 2026-07-

### vazamento caracteres tts edge tts escapa ssml
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [tts, edge-tts, ssml, ponte-de-voz, jarvis-bridge]
data: 2026-08-02
contexto: Usuário reportou que, no início das conversas, antes de falar "David", o Jarvis pronunciava caracteres que não deveriam. Investigação da saudação revelou causa na camada de TTS.
decisao: edge-tts >= 7.x removeu suporte a SSML custom. O __init__ do Communicate() aplica escape() em todo o texto, convertendo < e > em &lt; e &gt;. Assim, tags <break>, <phoneme>, <say-as> e <prosody> nunca são interpret

### grafo vis network bug string js json dumps
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags:
  - obsidian
  - grafo
  - html
  - js
  - vis-network
  - debugging
  - gerador
data: 2026-08-02
contexto: Geramos docs/grafo.html com vis-network para visualizar o conhecimento como grafo. A pagina renderizava header/legenda mas o canvas ficava vazio.
decisao: Diagnosticado via headless Chrome + Node. Causa raiz: um no (label "Why - User expects a blank slate...") continha quebra de linha literal dentro de string JS delimitada por aspas simples -> sintaxe invalida em TODO 

### corrigido travamento widget pywebview
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [widget, pywebview, windows, travamento, recursao, debug, frameless]
data: 2026-08-02
contexto: O widget desktop do grafo (scripts/widget_grafo.py) travava; o terminal python mostrava recorrente `[pywebview] Error while processing win.native.AccessibilityObject.Bounds.Empty...: maximum recursion depth exceeded`.
decisao: Duas causas distintas atacadas:
1. GEOMETRIA: ler `win.x/win.y/win.width/win.height` a partir de thread nao-principal (loop de 1s) dispara recursao infinita

### 2026-08-04: Refinamento do grafo — zoom microscópio, expandir e cognição viva
**Dominio:** general
**Fonte:** opencode

---
tipo: aprendizado
tags: [vis-network, zoom, microsocpio, clustering, physics, barnesHut, grafo, widget, labels]
data: 2026-08-04
contexto: Refinamento do widget "Cerebro Vivo" (scripts/widget_grafo.py + scripts/generate-graph-html.py) para movimento mais vivo/realista e zoom com papel narrativo.
decisao: Movimento organico = physics.stabilization:false + timestep:0.2 + maxVelocity:6 + minVelocity:0 + adaptiveTimestep:false + barnesHut(avoidOverlap:0.55, damping:0.88). Respiracao do layout vi

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente

### Bug: parametro Pid e variavel automatica do PowerShell
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [watchdog, powershell, bug, resiliencia]
data: 2026-08-06
contexto: Certificacao forense de processos no watchdog.ps1 (Test-ForensicoLixo / Invoke-KillCertificado)
decisao: Renomear parametro [int]Pid para [int]ProcessId nas funcoes forenses
impacto: Evita que o watchdog mate o proprio processo (variavel automatica PID read-only)
---

# Bug: parametro Pid e variavel automatica do PowerShell

## Sintoma
A funcao `Test-ForensicoLixo` e `Invoke-KillCertificado` declaravam `[int

### ---
**Dominio:** general
**Fonte:** opencode

---
tipo: decisao
tags: [tts, edge-tts, ssml, prosody, pronuncia, autoevolucao, jarvis, clausula-petrea]
data: 2026-08-02
contexto: Proximos passos anotados no aprendizado 2026-08-02-evolucao-tts-naturalidade-ssml.md (prosody dinamico + dicionario de pronuncia autoevolutivo). Usuario pediu "quero tudo".
decisao: Implementados ambos. (1) _prosodia_frases() aplica prosody por sentenca DEPOIS de say-as/break/emphasis para nao corromper regex de numero — pergunta (?)=pitch+12%/rate+4% (ascendente

### MCP prompt-optimization não conectava: transporte JSON por linha em vez de MCP stdio
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [mcp, prompt-optimization, transporte, stdio, content-length, opencode, jsonrpc]
data: 2026-08-08
contexto: Usuário perguntou se o otimizador de prompt estava ativo no ecossistema; verificação revelou que estava configurado mas nunca conectava
decisao: Corrigir o transporte do MCP server prompt-optimization para o padrão stdio com Content-Length framing (JSON-RPC MCP), em vez de JSON por linha
impacto: O MCP server agora responde a initialize/tools/list/tools/call com o prot

### Erro: UnicodeEncodeError no runtime_context (cp1252)
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [runtime, unicode, windows, cp1252, runtime_context]
data: 2026-08-08
contexto: Verificação de preflight + busca de erro no runtime (pedido do módulo de compreensão de pedidos).
decisao: Adicionar sys.stdout.reconfigure(encoding='utf-8', errors='replace') em scripts/runtime_context.py, mesmo padrão já usado em scripts/lg_pair_tv.py.
impacto: Context Loader voltou a renderizar contexto sem crash; caracteres como ↔ (U+2194) presentes na memória (@sync) agora imprimem corretame

### fix favoritos tags e contagem por capitulo
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [biblia, favoritos, sqlite, schema, migracao, contagem, capitulo]
data: 2026-08-09
contexto: Bug de favoritos reportado pelo usuário + pedido de contagem de favoritos/notas por capítulo
decisao: Renomear coluna `tag` para `tags` no banco pré-populado e adicionar migração defensiva; reativar spinner de capítulos com contagens; marcar versículo favoritado com ★
impacto: Favoritos voltaram a funcionar; capítulos mostram quantos versículos estão favoritados e quantas notas exist

### fix tts corte final textos longos
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [tts, speech_pipeline, chunking, truncamento, edge-tts]
data: 2026-08-13
contexto: Textos longos narrados por voz (resumos grandes, relatórios) tinham o final cortado
decisao: O SpeechPipeline.prepare() truncava o texto em MAX_TEXT_LENGTH (2000) antes da síntese,
cortando silenciosamente todo o conteúdo restante. Corrigido movendo o split de texto longo
para a síntese: _partes_para_sintese() divide via SentenceChunker.chunk_by_length() e a
síntese concatena o áudio de cada p

### auditoria cerebro vivo fix tema padrao e bugs
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [cerebro-vivo, grafo, widget, generate-graph-html, tema-padrao, fisica, vis-network, javascript]
data: 2026-08-13
contexto: Auditoria do widget "Cérebro Vivo" (docs/grafo.html, gerado por scripts/generate-graph-html.py).
Linha de trabalho escolhida: corrigir o tema Padrão + sanar bugs. Fase 1 mapeou estados e fluxos;
Fase 2 validou todos os blocos JS com node --check (principal 740KB + widget-extra.js + resize.js).
decisao: 1) TEMAS.padrao.forca usava as chaves {grav, centra

### integracao completa mcps offline placeholder
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [integracao, mcp, opencode, config, placeholder, renderizacao, deploy]
data: 2026-08-13
contexto: Diagnóstico de integração completa do EcoSystemUmGrau. Todos os 13 MCPs
apareciam como "failed / Connection closed" no `opencode mcp list`, mesmo com o
preflight passando e o opencode.jsonc definindo todos os servidores.
decisao: A causa raiz era que o opencode.jsonc deployado em ~/.config/opencode
continha `{{USERPROFILE}}` literal nos caminhos (o opencode não expande esse
plac

### Parar Fala — corrida da flag parar_fala.flag
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [widget, narrador, parar-fala, flag, corrida, tts, jarvis, speech-pipeline]
data: 2026-08-13
contexto: Botão "Parar Fala" do widget Jarvis não parava a narração; usuário relatou que Jarvis continuava falando após acionar o botão.
decisao: cmd_interromper_fala (scripts/widget_controle_jarvis.py) passou a manter a flag runtime/parar_fala.flag por 1.5s antes de apagá-la, e removeu o feedback de áudio "Voz desativada" que era falado logo após a parada.
impacto: Narrador em proce

### ETAPA 25 — Teste End-to-End
**Dominio:** general
**Fonte:** opencode

# ETAPA 25 — Teste End-to-End

## O que foi feito
- Teste E2E que valida o fluxo completo: User→Interface→Core→MissionLoop→Tools→Memory→SelfAssessment→Observability→Response
- 126 testes PASS, 0 falhas (100% success rate)
- Regressão: 332 testes Etapa 21-24, todos PASS

## Testes executados
1. **Dependency Audit** — 10 módulos verificados, memória carregada
2. **Conversation Flow** — User message → classify → respond → correlation preserved
3. **Mission Execution** — Real `create_and_execute_mis

### ERRADO
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [adb, tailscale, scrcpy, android, conexao]
data: 2026-08-18
contexto: scrcpy nao encontrava dispositivo ADB via Tailscale
decisao: Corrigir caminho do ADB em adb_auto_connect.py para tentar multiplos caminhos
impacto: Tailscale agora funciona como alternativa viavel para conexao ADB
---

## Problema

O scrcpy retornava "Could not find any ADB device" mesmo com Tailscale ativo.

## Causa

O `adb_auto_connect.py` usava um caminho incorreto para o ADB:
```python
# ERRADO
os.pat

### respostas truncadas
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [resposta, truncamento, final, palavra, llm, mitigacao]
data: 2026-08-18
contexto: Respostas do assistente terminam com a última palavra cortada (ex.: "atuais" vira "atu")
decisao: Adicionar regra de mitigação: verificar final de toda resposta antes de entregar
impacto: Respostas completas, sem palavras cortadas
---

## Contexto

O usuário identificou um padrão recorrente: as respostas do assistente
terminam com a última palavra incompleta. Exemplo concreto: a frase terminou

### crash topicindex version mismatch
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [android, sqlite, crash, database, version-mismatch]
data: 2026-08-18
contexto: TopicIndexActivity crashava ao abrir o Índice Temático no app Bíblia de Estudo
decisao: Corrigir DATABASE_VERSION de 1 para 2 no TopicIndexDatabaseHelper
impacto: Crash resolvido, Índice Temático agora funciona com 56 tópicos bíblicos
---

## Problema

TopicIndexActivity crashava imediatamente ao abrir, sem mensagem de erro visível.

## Causa raiz

Incompatibilidade de versão entre o banco `indic

### Projecao ortho nas transicoes GL
**Dominio:** general
**Fonte:** opencode

﻿---
tipo: erro
tags: [opengl, transicoes, biblia, projecao, ortho]
data: 2026-08-19
contexto: Motor de transicoes OpenGL ES 2.0 do app BibliaEstudoCompleta
decisao: Trocar frustumM por orthoM(-1,1,-1,1,2,8) e remover a multiplicacao pos.x *= uOldAspect no shader
impacto: Pagina preenche a tela inteira sem distorcao; 4 efeitos validados no device
---

# Projecao ortho nas transicoes GL

## Problema
A pagina capturada tem a mesma proporcao da tela (1080x2400, aspect 0.45).
Com frustumM(-aspect, a

### Toast de Erros - Falsos Positivos
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [widget, deteccao, falsos-positivos, regex]
data: 2026-08-20
---

# Toast de Erros - Falsos Positivos

## Problema
O toast de erros do widget Jarvis mostrava janela vermelha piscando sem erros reais.

## Causa
O regex pegava linhas do log do narrador que continham palavras como "erro" e "falhou" no texto falado. Exemplo:
"falando (140 chars): O dialogo de erro e do crash anterior..."

Essa linha e o Jarvis FALANDO sobre um erro passado, nao um erro real.

## Correcao
Filtrar

### Narrador morto por bloco duplicado; falso-positivo de encoding no log
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [narrador, system-guardian, syntax-error, encoding, git]
data: 2026-08-21
---

# Narrador morto por bloco duplicado; falso-positivo de encoding no log

## Contexto
Investigação pedida pelo usuário sobre duas anomalias no log do system_guardian:
texto corrompido ("ap��s") e o narrador morrendo logo após iniciar em loop.

## Causa raiz 1 — narrador (real)
Entre os commits a2d996c4 (14:18) e adcfb195 (16:08) de 21/08/2026, um enxerto de
286 linhas duplicadas do próprio módulo e

### Snapshots "corrompidos" do opencode: referência no banco decide, não heurística
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [opencode-resilience, snapshots, falso-positivo, seguranca-de-dados]
data: 2026-08-21
---

# Snapshots "corrompidos" do opencode: referência no banco decide, não heurística

## Contexto
Usuário apontou a mensagem recorrente "[SNAP] 2 snapshot(s) corrompido(s) - limpeza
adiada (desktop ativo)" no log do guardian. Investigação revelou três camadas.

## Causas encontradas
1. Falso positivo estrutural: o detector marcava o subdiretório `objects` interno
   do próprio git (por co

### saudacao espontanea nao implementada
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [saudacao, autoapresentacao, clausula-petrea, boot, primeira-mensagem]
data: 2026-08-23
contexto: "Cláusula pétrea de autoapresentação automática na primeira mensagem de cada sessão (AGENTS.md e Constituição) exige saudação curta (máx 3-4 linhas), espontânea, variando o tom a cada sessão, informando que EcoSystemUmGrau está ativo e operante, com leve contexto (projeto ativo, memória, pendências)."
decisao: "Registrar erro e definir implementação: criar mecanismo de detecção 

### Pacote Seguro de Serviços Windows — Aplicação com Backup
**Dominio:** general
**Fonte:** opencode

# Pacote Seguro de Serviços Windows — Aplicação com Backup

## Metadados
- tipo: decisao
- tags: [windows, servicos, otimizacao, seguranca, tailscale, teamviewer, sshd, rdp]
- data: 2026-08-23
- contexto: Máquina com 3,9 GB RAM (0,6 GB livre) e 5 canais de acesso remoto ativos. Usuário confirmou uso de Tailscale e TeamViewer; aprovou execução do pacote seguro após verificação de impacto no EcoSystemUmGrau.

## Decisão
Desativar 27 serviços inúteis para este perfil de uso (desenvolvimento local, 

### ﻿---
**Dominio:** general
**Fonte:** opencode

﻿---
tipo: decisao
tags: [ollama, hd-externo, ntfs, exfat, reconstrucao]
data: 2026-08-27
contexto: HD externo E: estava com exFAT corrompido (leituras inconsistentes), bloqueando o Ollama.
decisao: Reformatar E: para NTFS e reconstruir o Ollama + espelhar o EcoSystemUmGrau.
impacto: Ollama 100% no E: com 5 modelos; espelho do ecossistema no E:.
---

## Reconstrução do Ollama no HD Externo (NTFS)

Causa raiz: o exFAT do E: tinha corrupção estrutural de diretório — cada leitor
(PowerShell, Python

### ﻿---
**Dominio:** general
**Fonte:** opencode

﻿---
tipo: decisao
tags: [narrador, edge, widget, pausa, cerebro]
data: 2026-08-28
contexto: Pedido de botao pausar/parar no widget. A primeira implementacao foi colocada no Cerebro Vivo (www/cerebro.html + widget_grafo.py), mas o alvo correto era a janela Edge (widget_edge.py), onde roda o motor de narracao.
decisao: Reverter as mudancas do Cerebro e implementar Pausar/Retomar no Edge. EdgeApi ganhou pause()/resume() e status() passou a retornar pausado. UI www/index.html ganhou o botao btnPaus

### ﻿---
**Dominio:** general
**Fonte:** opencode

﻿---
tipo: decisao
tags: [narrador, edge, widget, pausa, cerebro]
data: 2026-08-28
contexto: Pedido de botao pausar/parar no widget. A primeira implementacao foi colocada no Cerebro Vivo (www/cerebro.html + widget_grafo.py), mas o alvo correto era a janela Edge (widget_edge.py), onde roda o motor de narracao.
decisao: Reverter as mudancas do Cerebro e implementar Pausar/Retomar no Edge. EdgeApi ganhou pause()/resume() e status() passou a retornar pausado. UI www/index.html ganhou o botao btnPaus

### gate hd externo e preflight repos nativos
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [gate, persistencia, hd-externo, preflight, powershell]
data: 2026-08-28
contexto: Sync apos controles de narracao no widget Edge. Gate persistencia.ps1 travava espelho do HD externo e repos nativos.
decisao: Corrigir bug de continuacao de linha PowerShell no filtro $hdBloqueio (mover '-and' para o fim da linha); Invoke-PreflightGlobal passa a pular preflight quando scripts/preflight_check.py nao existe (em vez de bloquear); identidade git local configurada no repo claude-co

### audit runner recuperado
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [guardian, auditoria, monitor, audit_runner, widget]
data: 2026-08-28
contexto: system_guardian.py executava scripts/audit_runner.py a cada ~30 min para gerar runtime/audit_result.json e reportar saúde do ecossistema.
decisao: Recriar scripts/audit_runner.py (arquivo referenciado não existia mais), reutilizando audit_eco.run_audit como fonte única e escrevendo o resultado com escrita atômica (tmp + os.replace) no contrato que o guardian lê (timestamp epoch + score + findings

### ordinais text normalizer
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [tts, ordinal, text_normalizer, pronuncia, placeholder]
data: 2026-08-29
contexto: text_normalizer.py expandia 1º/2ª como "umº" (sufixo ordinal mantido), pois _normalize_numbers só tratava inteiros/percentuais. Correção necessária para expandir ordinais por extenso.
decisao: Adicionar ordinal_por_extenso(n, genero) (1..999, masc/fem) e regex (?<![\d.,])(\d{1,3})([ºª]) com placeholder "=ORDO<chave_letras>M/F=" (chave só-de-letras via _letras_de para a regex de inteiros não ca

### Silêncio do narrador — três causas empilhadas
**Dominio:** general
**Fonte:** opencode

---
titulo: Silencio do narrador tinha tres causas empilhadas
tipo: erro
tags: [narrador, tts, audio, resiliencia, diagnóstico]
data: 2026-08-29
---

# Silêncio do narrador — três causas empilhadas

## Contexto
O usuário relatou "não estou ouvindo o narrador". A telemetria mostrava fala ok (MP3 gerado, `ok=True`), mas nada saía no alto-falante.

## Causas encontradas (em camadas)

1. **Bug no widget**: `voice_off()` chamava `_narrador_pausar(True)` em vez de `False`. Corrigido — hoje a função re

### Maestro Fase Ativa - Fix Registro e Stale PID
**Dominio:** general
**Fonte:** opencode

﻿---
tipo: decisao
tags: [maestro, runtime, guardian, fase-ativa, stale-pid]
data: 2026-08-31
contexto: |
  Maestro de Runtime em fase ativa. Guardians consultam antes de iniciar servicos.
  Bug: Maestro nao verificava se PID registrado ainda estava vivo (confiava cego no campo vivo).
  Bug: Guardian nao registrava PID no Maestro apos iniciar servico.
decisao: |
  1. Adicionar verificacao de vida (psutil.pid_exists) no pode_iniciar() do Maestro.
     Se PID registrado morto, limpar registro stal

### Correção de métricas de aderência (@sync)
**Dominio:** general
**Fonte:** opencode

---
tipo: erro
tags: [aderencia, preflight, adherencia-audit, metrica, bug]
data: 2026-09-02
contexto: O @sync reportava @sync FAIL por metricas de aderencia baixas (inventario 15.8%, preflight 25%). Investigacao revelou bugs reais em duas metricas e um falso positivo no deploy config.
decisao: Correcao de 3 frentes para elevar o score geral de aderencia de 69.6 para 93.4/100.
impacto: @sync agora PASS (thresholds OK). Score EXCELENTE.
---

# Correção de métricas de aderência (@sync)

## 1. Bug 

## Heuristicas

| # | Dominio | Titulo | Descricao |
|---|--------|--------|-----------|
| 1 | debugging | Regra dos 3 logs | Antes de comecar a debugar, adicione 3 logs: (1) entrada da funcao com parametros, (2) ponto medio/dentro do loop, (3) saida com resultado. Isso cobre 90% dos bugs sem precisar de  |
| 2 | debugging | Heuristica de isolamento de falha | Quando um sistema falha, isole variaveis UMA de cada vez. Mude exatamente uma coisa entre cada teste. Se voce mudar duas coisas e o bug desaparecer, voce nao sabe qual das duas res |
| 3 | persistence | Escrita atomica sempre | Qualquer escrita em arquivo que importa: tmp + rename atomico. Nao importa o quao trivial parece. Um crash no meio do json.dump corrompe o arquivo e voce perde tudo. |
| 4 | coding | Principio do menor escopo de variavel | Declare variaveis no menor escopo possivel. Se uma variavel pode ser local a um if, nao a declare no inicio da funcao. Isso reduz carga cognitiva e previne bugs de reuse de estado. |
| 5 | coding | Interface sobre implementacao em parametros | Funcoes que aceitam dados devem aceitar o tipo MAIS GENERICO possivel (File, nao um path especifico; List, nao ArrayList; InputStream, nao FileInputStream). Isso maximiza reuso e t |
| 6 | system_design | Cache de decisoes caras | Se uma computacao e deterministica e custosa, cacheie o resultado. Se o resultado pode mudar, invalide o cache explicitamente. Nunca confie em TTL para invalidação de dados que pre |
| 7 | system_design | Sempre esperar o inesperado em E/S | Toda operacao de E/S (rede, disco, banco) pode falhar. Sempre tenha: timeout, retry com backoff, fallback, e log do erro. Nao existe excecao 'que nunca acontece' em E/S. |
| 8 | coding | Regra do 'nao magico' | Numeros magicos, strings literais repetidas, e comportamento implicito sao bugs esperando para acontecer. Extraia para constantes nomeadas com documentacao do porque daquele valor. |
| 9 | architecture | State deve ser explícito, nunca implícito | Se um componente tem estado (ativo/inativo, conectado/desconectado, editando/visualizando), represente-o como UMA variavel booleana ou enum, nao como combinacao de multiplos sinais |
| 10 | debugging | Dados > Algoritmos para debugging | Quando um algoritmo parece errado, nao olhe primeiro para o algoritmo. Imprima/inspecione os DADOS que ele esta processando. 90% das vezes o algoritmo esta certo e os dados estao e |
| 11 | debugging | Verifique o que voce acha que sabe | Toda vez que pensar 'isso nao pode ser a causa porque ja sei como funciona', VERIFIQUE. As suposicoes mais obvias sao as que mais escondem bugs. Um 'confia mas verifica' sistematic |
| 12 | architecture | Projete para falha, nao para sucesso | Um sistema robusto nao e o que nunca falha — e o que lida graciosamente com cada falha. Pergunte: 'O que acontece se o disco enche? E se a rede cai? E se a memoria acaba? E se o ar |
| 13 | configuration | Sempre validar schema apos migracao de config | Ferramentas que geram config podem produzir schema invalido; sempre ler spec e validar manualmente apos edicao |
| 14 | security | Nunca armazenar API keys em config files | Auth tokens e chaves API devem ficar em env vars ou auth.json criptografado, nunca em opencode.json |
| 15 | testing | Testar failover ativamente | Nao confiar em logica de fallback sem testar: derrubar servico primario e verificar se secundario assume |
| 16 | debugging | Elemento existe? 3 fontes de verdade | Sempre cruzar 3 fontes antes de afirmar que elemento nao existe: (1) DOM/arvore atual, (2) screenshot com OCR, (3) viewport/scroll position. Se 2 de 3 concordam, elemento existe |
| 17 | web-navigation | Navegacao em SPA: 3 sinais de sucesso | SPA navegou corretamente se 2 de 3 mudarem: (1) URL (pushState), (2) title da pagina, (3) conteudo do container principal (#root, #app). Verificar os 3 apos cada clique |
| 18 | cross-platform | Antes de clicar, verifique o interceptador | Sempre verificar (1) modal aberto, (2) notificacao, (3) teclado virtual, (4) overlay de loading antes de clicar em qualquer elemento. Cada um desses causa falha misteriosa. |
| 19 | element-detection | Hierarquia de confianca de seletores | Web: data-testid > #id > [name] > .class-unica > tag[attr] > :contains. Desktop: AutomationId > Name > ClassName > coordenadas. Mobile: resource-id > content-desc > text > coordena |
| 20 | debugging | Stale element = re-query, nao re-tentar | Elemento stale significa que a referencia morreu; re-tentar a mesma operacao no mesmo objeto nunca funciona. Re-buscar o elemento pelo seletor original e a unica solucao |
| 21 | web-navigation | Scroll forcado revela conteudo oculto | Conteudo lazy-loaded so aparece quando usuario faz scroll. Scroll ate o fim, espera 1s, scroll de novo, repete 3x. Metade dos 'elementos nao encontrados' sao lazy-loaded |
| 22 | efficiency | Velocidade = evitar esperas fixas | Esperar 10s 'para garantir' custa 10s por operacao. Usar waitForElement com polling a cada 100ms e timeout de 10s: se elemento aparece em 200ms, voce ganhou 9.8s |
| 23 | cross-platform | Teclado vence layout | Quando mouse/clique falha, Tab+Enter resolve em 80% dos casos. Atalhos de teclado sao independentes de CSS, tema, idioma, e resolucao. Sempre tenha fallback por teclado |
| 24 | efficiency | Primeiro scan, depois interaja | Antes de qualquer acao, faca um scan completo do estado atual: elementos visiveis, modais, estado de loading. Agir cegamente leva a 3x mais retries. 1 scan evita 3 falhas |
| 25 | element-detection | Seletor mais especifico = mais fragil | data-testid=product-123 e exato mas quebra se o ID mudar. Preferir seletores semanticos: [data-testid^=product-] ou .product-card capturam variacoes sem quebrar |
| 26 | element-detection | Canvas e graficos: template matching | Elementos renderizados em canvas, SVG complexo ou WebGL nao tem arvore DOM utilizavel. Screenshot + template matching (OpenCV) + OCR e o unico caminho confiavel |
| 27 | efficiency | 30s regra de timeout maximo | Nenhuma operacao de navegacao deve esperar mais que 30s. Se algo demora mais que isso, algo esta quebrado (rede, servidor, loop infinito). Fail fast, nao espere |
| 28 | debugging | Log de fallback para diagnostico rapido | Sempre logar: (1) o que tentou fazer, (2) qual seletor usou, (3) o que encontrou, (4) o que deu errado. Logs estruturados reduzem tempo de debugging em 5x |
| 29 | protocol | JSON-RPC notifications | Sempre verificar se request tem id antes de responder. Se nao tem, e notification - nao responda. |
| 30 | protocol | MCP tool naming | MCP tools/list pode expor nomes kebab-case, mas tools/call precisa de mapping explicito para metodos internos |
| 31 | organization | Workspace root | Manter projetos em raiz unica sem espacos no caminho para compatibilidade com scripts |
| 32 | debugging | open() sempre com encoding no Windows | Todo open() de arquivo texto deve especificar encoding. No Windows, o default muda conforme o locale do sistema. |

## Frameworks

### Ciclo PDCA (Plan-Do-Check-Act) para engenharia
**Fonte:** meta_cognition

Loop classico de melhoria continua adaptado para engenharia de software.

### Metodo dos 5 Porques (5 Whys)
**Fonte:** meta_cognition

Tecnica de analise de causa raiz: pergunte 'por que?' 5 vezes para cada sintoma.

### MECE (Mutually Exclusive, Collectively Exhaustive)
**Fonte:** meta_cognition

Principio de classificacao: particoes sem sobreposicao que cobrem todo o espaco.

### FIRST Principles para testes
**Fonte:** meta_cognition

Propriedades de um bom teste unitario: Fast, Isolated, Repeatable, Self-validating, Timely.

### Arvore de Decisao para Fallback de Servico
**Fonte:** meta_cognition

Estrategia para servicos com multiplas fontes de dados em ordem de preferencia.

### Framework de Persistencia com Snapshot Imutavel
**Fonte:** meta_cognition

Padrao onde cada salvamento e um snapshot timestampado, nunca overwrite.

### Framework de Aprendizado Continuo (Auto-Learning)
**Fonte:** meta_cognition

Sistema que acumula conhecimento automaticamente entre sessoes.

### Cascata de Interacao (CI)
**Fonte:** session

Framework de 4 niveis para interagir com qualquer elemento: N1 = seletor direto (data-testid/resource-id), N2 = seletor semantico (classe/tag/texto), N3 = coordenadas relativas, N4 = OCR + template matching. Subir um nivel a cada 3 falhas consecutivas

### OODA-Nav
**Fonte:** session

Adaptacao do ciclo Observe-Orient-Decide-Act de Boyd para navegacao automatizada. Ciclo completo <3s. Repetir a cada interacao

### 3-Scan Pre-Action
**Fonte:** session

Protocolo de 3 scans antes de cada acao para garantir contexto completo e evitar falhas evitaveis

---

## Meta-Informacao

**Versao do grafo:** 2
**Ultima atualizacao:** 2026-09-02T09:49:27.042785
**Proposito:** Base de conhecimento universal e auto-melhoravel para engenharia de software

*Fim da exportacao. Este arquivo MARKDOWN pode ser fornecido como contexto para QUALQUER IA.*
