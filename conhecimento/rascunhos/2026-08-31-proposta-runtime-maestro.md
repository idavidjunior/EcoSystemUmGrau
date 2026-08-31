---
titulo: Maestro de Runtime — proposta final
tipo: decisao
tags: [maestro, runtime, coordenador, anti-conflito, arquitetura]
data: 2026-08-31
status: RASCUNHO
resumo: |
  Proposta de criar runtime_maestro.py como único autorizado a iniciar/parar
  serviços. Fase 1: modo observador (logar sem bloquear). Comunicação via
  arquivo de comando em disco. Fallback: se maestro cair, componente permite
  a ação mas loga ALERTA. Após 1-3 dias validando, vai pra fase ativa.
decisoes_do_usuario:
  fase_inicial: observador (não bloqueia ninguém nos primeiros 1-3 dias)
  comunicacao: arquivo em disco (mesmo padrão do tts_cmd.json)
  fallback: permite a ação com ALERTA alto se maestro não responder em 5s
  observacao: maestro ja tem regras deterministicas (singleton, cooldown,
    anti-orfao). Nao precisa aprender, precisa apenas ser validado que
    enxerga todos os starts e suas decisoes batem com o cenario real.
    1-3 dias cobrem uso normal + fim de semana + variacao.
contexto: |
  Hoje o ecossistema tem 3 "chefes" de processos decidindo em paralelo:
  - system_guardian.py (PID 5604, 9220 — duplicado)
  - vigilante.ps1 (PID 4296)
  - widget_edge.py decide sozinho sobre narrador
  Resultado observado: TTS service nasceu 3x, áudio repetia mesma frase,
  narrador logava triplicado. Falta um único chefe.
arquitetura: |
  ┌─────────────────────────────────────────────────┐
  │            runtime_maestro (singleton)           │
  │  livro_estado.json (inventário único)           │
  │  maestro_cmd.json (entrada)                     │
  │  maestro_resp_<id>.json (saída)                 │
  │  cooldown global por script                     │
  │  singleton check global                         │
  │  heartbeat próprio (anti-órfão)                 │
  └────────┬──────────┬──────────┬─────────┬────────┘
           │          │          │         │
     ┌─────▼───┐ ┌────▼────┐ ┌──▼─────┐ ┌─▼──────────┐
     │ guardian│ │ widget  │ │ bridge │ │ vigilante  │
     │  (olho) │ │(narrador)│ │  (voz) │ │(legado PS1)│
     └─────────┘ └─────────┘ └────────┘ └────────────┘

  Todos consultam maestro antes de agir via arquivo de comando.
contrato_publico: |
  Comandos (runtime/maestro_cmd.json):
    {"cmd": "pode_iniciar", "script": "tts_service.py", "request_id": "abc"}
    {"cmd": "registrar",    "script": "...", "pid": 1234, "owner": "guardian"}
    {"cmd": "heartbeat",    "script": "...", "pid": 1234}
    {"cmd": "parar",        "script": "..."}
    {"cmd": "matar_duplicatas", "script": "..."}
    {"cmd": "listar_vivos"}

  Respostas (runtime/maestro_resp_<id>.json):
    {"status": "ok|warn|error", "decisao": true|false, "motivo": "..."}

  Sempre responde em até 1s. Se não responder em 5s, componente entra
  em modo degraded (permite + ALERTA).
fluxo_fase1_observador: |
  1. Componente decide o que fazer (como hoje)
  2. Componente escreve comando em maestro_cmd.json
  3. Maestro observa e loga:
     - O que componente QUER fazer
     - O que componente FEZ de fato
     - Se a decisão do componente bate com a recomendação do maestro
  4. Se houver divergência, reporta WARN imediato (nao acumula)
  5. Após 1-3 dias de observacao (cobre variacao de uso), passa pra fase 2
     se nao houver divergencias criticas. 7 dias era conservador demais
     para um sistema com regras deterministicas — ele nao aprende,
     apenas executa logica conhecida.
fluxo_fase2_ativo: |
  1. Componente escreve comando em maestro_cmd.json
  2. Maestro DECIDE: pode ou não pode
  3. Componente só age se maestro respondeu "pode"
  4. Se maestro não respondeu em 5s: modo degraded (age + ALERTA)
  5. Loga todas decisões pra auditoria posterior
fallback_detalhado: |
  Modo degraded (maestro indisponível):
  - Componente executa a ação normalmente
  - Loga ALERTA no formato: [MAESTRO_OFFLINE] guardian tentou iniciar
    tts_service sem resposta do maestro em 5s. Ação executada.
  - Cada componente tem seu próprio cooldown local como segurança
  - Após 3 ALERTAs consecutivos, watchdog tenta religar maestro
  - Maestro tem heartbeat próprio; watchdog detecta queda
anti_orfao_maestro: |
  O maestro não pode ficar órfão:
  - watchdog.ps1 vigia maestro.pid
  - Se maestro cair, watchdog tenta religar em até 3x
  - Se falhar 3x, sistema fica em degraded total (permite tudo +
    ALERTA MÁXIMO a cada ação) até maestro voltar
migracao_3_fases: |
  Fase 1 (1-3 dias, observador):
  - Criar runtime_maestro.py + livro_estado.json
  - Componentes passam a logar o que fariam e o que fizeram
  - Maestro compara mas não bloqueia
  - Relatório: divergências por dia
  Fase 2 (ativo):
  - Maestro começa a bloquear ações conflitantes
  - Componentes perdem autonomia de start_*
  - Cooldown central substitui os cooldowns locais
  Fase 3 (consolidação):
  - vigilante.ps1 migrado pra maestro (Python único)
  - Documentar maestro em AGENTS.md como ponto único
  - Remover lógica de singleton/cooldown duplicada
riscos_e_mitigacoes: |
  Risco 1: Maestro vira mais um fiscal duplicado
  Mitigação: fase 1 observa, não decide. Só ativa após validação.

  Risco 2: Se maestro cair, ninguém inicia nada
  Mitigação: fallback permite + ALERTA em 5s.

  Risco 3: Adiciona latência (arquivo em disco)
  Mitigação: comando/resp são minúsculos (<1KB). Disco local SSD.

  Risco 4: Complexidade adicional sem ganho real
  Mitigação: só continua se fase 1 mostrar bugs reais sendo prevenidos.
testes_fase1:
  - Maestro roda por 7 dias sem divergência
  - Simular TTS duplicado: maestro detecta e loga WARN
  - Simular widget fantasma: maestro detecta e loga WARN
  - Derrubar maestro manualmente: todos os componentes continuam
    funcionando com ALERTA visível
  - Reload do maestro: nenhum serviço precisa reiniciar
arquivos_seriam_criados:
  - scripts/runtime_maestro.py (daemon singleton)
  - scripts/test_runtime_maestro.py (testes fase 1)
  - runtime/maestro_estado.json (gerado em runtime)
arquivos_seriam_alterados_fase2:
  - scripts/system_guardian.py (start_* consultam maestro)
  - scripts/widget_edge.py (singleton narrador alinha com maestro)
  - scripts/jarvis_bridge.py (start_http_server consulta maestro)
  - config/agents/00-system-rules.md (maestro como ponto único)
proximos_passos:
  1. Usuário aprova este rascunho (ou pede ajustes)
  2. Implementar runtime_maestro.py mínimo (esqueleto + livro_estado)
  3. Rodar fase 1 por 7 dias
  4. Relatório de divergências
  5. Decisão go/no-go pra fase 2
