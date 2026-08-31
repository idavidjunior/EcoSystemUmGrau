---
titulo: Maestro de Runtime — proposta de cérebro unificado de processos
tipo: decisao
tags: [maestro, runtime, coordenador, anti-conflito, arquitetura]
data: 2026-08-31
status: RASCUNHO
resumo: |
  Proposta de criar runtime_maestro.py como único autorizado a iniciar/parar
  serviços e validar mudanças de estado. Hoje guardian, vigilante e widget
  decidem em paralelo sem se coordenar (causa do bug triplo do narrador e
  do TTS duplicado). O Maestro seria invocado por todos antes de agir.
contexto: |
  Diagnóstico atual (31/08/2026):
  - system_guardian.py tem 5 funcoes start_* (bridge, serve, widget,
    narrador, tts_service) e roda em 2 processos duplicados (PID 5604, 9220)
  - vigilante.ps1 (PowerShell) tambem acorda processos (PID 4296)
  - widget_edge.py decide sozinho se acorda narrador
  - jarvis_bridge.py inicia http_server sozinho
  - runtime_kernel.py valida TEXTO mas nao gerencia PROCESSOS
  Resultado: 3 "chefes" tomando decisao sobre a mesma coisa, sem se falar.
  Consequencia observada: TTS service nasceu 3x no mesmo ciclo, audio
  do narrador repetia a mesma frase 2-3 vezes.
proposta: |
  Criar scripts/runtime_maestro.py como singleton daemon com 3
  responsabilidades:
  1. UNICA porta de entrada para start_/stop_ de qualquer servico Eco.
     Guardian, widget, bridge, vigilante consultam o Maestro via
     comando (pode ser arquivo de lock + IPC simples, ou socket local).
  2. LIVRO DE ESTADO UNICO: runtime/maestro_estado.json com o inventario
     ao vivo de todos os servicos (pid, script, started_at, owner,
     cooldown_ate). Substitui a leitura espalhada de pid_files.
  3. COOLDOWN/SINGLETON GLOBAL: a unica instancia que decide se pode
     iniciar algo. Cooldown compartilhado entre todos os chamadores.
     Se alguem pediu start_foo() ha 5s, o proximo start_foo() e no-op.
arquitetura_alvo: |
  ┌─────────────────────────────────────────────────┐
  │            runtime_maestro (singleton)           │
  │  - livro_estado (pid, script, owner, cooldown)  │
  │  - lock global por script                       │
  │  - cooldown por script                          │
  │  - heartbeat proprio (anti-orfão do maestro)    │
  └────────┬──────────┬──────────┬─────────┬────────┘
           │          │          │         │
     ┌─────▼───┐ ┌────▼────┐ ┌──▼─────┐ ┌─▼──────────┐
     │ guardian│ │ widget  │ │ bridge │ │ vigilante  │
     │  (olho) │ │(narrador)│ │  (voz) │ │(legado PS1)│
     └─────────┘ └─────────┘ └────────┘ └────────────┘

  Antes de agir, TODOS consultam o Maestro:
  - guardian.check_and_act() → maestro.pode_iniciar("tts_service")?
  - widget_edge.boot() → maestro.pode_iniciar("narrador_thread")?
  - jarvis_bridge.boot() → maestro.pode_iniciar("http_server")?
  - vigilante.ps1 → maestro.pode_iniciar(...)?
contrato_publico: |
  Maestro expoe (via CLI ou IPC):
  - pode_iniciar(script_py) -> bool  (checa singleton + cooldown)
  - registrar(script_py, pid, owner) -> ok
  - heartbeat(script_py) -> ok  (atualiza timestamp)
  - listar_vivos() -> dict  (inventario ao vivo)
  - parar(script_py) -> bool  (mata via PID registrado)
  - matar_duplicatas(script_py) -> int  (anti-orfao automatico)
migracao: |
  Fase 1 (segura):
  - Criar runtime_maestro.py comecando como OBSERVADOR (so loga, nao bloqueia)
  - Guardian e widget passam a chamar maestro.pode_iniciar() em modo shadow
  - Comparar decisoes: maestro X decisao atual. Se discordarem, loga WARN
  Fase 2:
  - Quando fase 1 mostrar 100% concordancia por 7 dias, modo ATIVO
  - Componentes passam a obedecer a resposta do maestro
  - Remover logicas duplicadas de singleton/cooldown de cada arquivo
  Fase 3:
  - vigilante.ps1 migrado pra Python OU passa a consultar maestro via
    comando shell (python scripts/runtime_maestro.py pode_iniciar X)
  - Documentar maestro como ponto unico em AGENTS.md
riscos: |
  - Se maestro cair, ninguem consegue iniciar servico: precisa de
    fallback (se maestro nao responde em 5s, modo degraded = permite
    tudo, mas loga ALERTA)
  - Adicionar camada de complexidade. So vale a pena se a dor
    continuar aparecendo.
  - Cuidado para nao virar mais um fiscal duplicado (ja tivemos isso
    com 2 guardians).
beneficio_esperado: |
  - Bug triplo do narrador: impossivel de voltar (singleton central)
  - TTS duplicado: impossivel (cooldown central)
  - Qualquer novo servico que alguem esquecer de coordenar: maestro
    recusa automaticamente
  - Um unico ponto de observacao (runtime/maestro_estado.json) pra
    ver tudo que ta vivo
alternativas_consideradas: |
  A) Estender runtime_kernel.py pra cuidar de processos tambem.
     Rejeitada: kernel e modullo de validacao de texto/resposta, nao
     de processo. Misturar responsabilidades viola separacao.
  B) Fazer Guardian ser o maestro (ele ja cuida de processos).
     Rejeitada: Guardian e executado por alguem (vigilante). Maestro
     precisa ser independente do executor.
  C) Deixar como esta e so documentar.
     Rejeitada: ja vimos que da bug. Nao tem coordenacao.
decisao_pendente: |
  Antes de implementar, o usuario precisa decidir:
  1. Aprovar a proposta como esta?
  2. Comecar por fase 1 (observador) ou ja ir pra ativa?
  3. Quem deve ser o primeiro chamador migrado (guardian ou widget)?
arquivos_seriam_criados:
  - scripts/runtime_maestro.py
  - runtime/maestro_estado.json (gerado em runtime)
arquivos_seriam_alterados:
  - scripts/system_guardian.py (substituir start_* por chamada ao maestro)
  - scripts/widget_edge.py (singleton narrador ja existe, alinhar com maestro)
  - scripts/jarvis_bridge.py (start_http_server passa pelo maestro)
  - config/agents/00-system-rules.md (documentar maestro como ponto unico)
testes_pendentes:
  - Fase 1: comparar decisoes atuais vs maestro por 7 dias
  - Fase 2: matar um servico e confirmar que maestro recusa renascimento
    imediato (cooldown funciona)
  - Fase 3: rodar preflight e verificar 0 conflitos
