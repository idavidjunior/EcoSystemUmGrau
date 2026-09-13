```markdown
# EXECUTOR GOVERNADO — FUSÃO INTELIGENTE (AIG + 09 + 11 + 12)

## ORIGEM DA FUSÃO

**Componentes fundidos:**
- **AGENTE IMPLEMENTADOR GOVERNADO (AIG)** — Governança rigorosa ponta a ponta (5 fases, 120+ perguntas, validação obrigatória, checklist de entrega)
- **09-executor** — Execução delegada, coordenação de sub-agentes
- **11-ler-executor** — Delegação ao LER (Loop Engineering Runtime) para missões complexas
- **12-parallel-planner** — Decomposição em subtarefas paralelas independentes

**Componentes mantidos como CONSELHEIROS ESPECIALIZADOS (não fundidos):**
- 01-estrategista → Define direção/roadmap (Conselheiro Estratégico)
- 02-cetico → Desafia hipóteses/riscos (Conselheiro Crítico)
- 03-realista → Avalia viabilidade/prazos (Conselheiro de Viabilidade)
- 04-etica → LGPD/GDPR, acessibilidade, conformidade (Conselheiro Ético)
- 05-futuro → Tendências/escalabilidade (Conselheiro de Futuro)
- 06-recursos → Mapeia reuso/bibliotecas (Conselheiro de Recursos)
- 07-criativo → Alternativas inovadoras (Conselheiro Criativo)
- 08-revisor → Code review, quality gates (Conselheiro de Qualidade)

**Componentes mantidos INDEPENDENTES (ortogonais):**
- 00-maestro — Coordenação runtime de processos (singleton, cooldown, anti-órfão)
- 13-flutter-orquestrador — Build Flutter/APK específico
- 99-gerador-de-agentes — Criação de novos agentes
- eco, ecocell, ecow, sync, ecomodelo — Agentes de comando/CLI
- compreender — MCP compreensão de pedidos (integra-se ao Executor Governado)

---

## ARQUITETURA DO EXECUTOR GOVERNADO

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTOR GOVERNADO                            │
│  (Fusão: AIG + Executor + LER-Executor + Parallel-Planner)      │
├─────────────────────────────────────────────────────────────────┤
│  FASE 0 — CONSULTA A CONSELHEIROS                                │
│  ├── Estratégico  → 01-estrategista (roadmap, priorização)      │
│  ├── Crítico     → 02-cetico (riscos, premissas)                │
│  ├── Viabilidade → 03-realista (prazos, custos, bloqueios)      │
│  ├── Ético       → 04-etica (LGPD, acessibilidade, conformidade)│
│  ├── Futuro      → 05-futuro (tendências, migrações)            │
│  ├── Recursos    → 06-recursos (reuso, anti-duplicação)         │
│  ├── Criativo    → 07-criativo (alternativas não-óbvias)        │
│  └── Qualidade   → 08-revisor (critérios, gates, revisão)       │
├─────────────────────────────────────────────────────────────────┤
│  FASE 1 — MAPEAMENTO EXAUSTIVO (120+ perguntas)                 │
│  ├── Respostas fundadas em evidência documental                 │
│  ├── Lacunas = bloqueios escalados                               │
│  └── Produto: contexto/mapeamento-contextual.md                 │
├─────────────────────────────────────────────────────────────────┤
│  FASE 2 — VALIDAÇÃO NORMATIVA                                    │
│  ├── Executa TODOS validadores (lint, test, type, security)     │
│  ├── Registra evidência por validador                            │
│  └── Produto: evidencias/relatorio-validacao.md                 │
├─────────────────────────────────────────────────────────────────┤
│  FASE 3 — DOCUMENTAÇÃO PRÉ-IMPLEMENTAÇÃO (5 docs)               │
│  ├── PLANO-DE-IMPLEMENTACAO.md (arquitetura, ordem, rollback)   │
│  ├── CONTRATOS.md (API, dados, eventos, UI, versões)            │
│  ├── MATRIZ-DE-TESTES.md (tipos, cobertura, casos críticos)     │
│  ├── RUNBOOK.md (local, test, deploy, rollback, diagnóstico)    │
│  └── EVIDENCIAS.md (rastreabilidade requisito→evidência)        │
├─────────────────────────────────────────────────────────────────┤
│  FASE 4 — IMPLEMENTAÇÃO GOVERNADA                                │
│  ├── Ordem do plano (sequencial, validado por módulo)           │
│  ├── Contratos congelados (mudança = revalidação)               │
│  ├── Testes primeiro (TDD obrigatório por módulo)               │
│  ├── Evidência contínua (cada commit = validadores passam)      │
│  ├── Paralelismo seguro (delega ao LER via 11-ler-executor)     │
│  │   └── Planner paralelo (12-parallel-planner) decompõe tarefas│
│  └── Zero supressão (falha = correção ou escalação)             │
├─────────────────────────────────────────────────────────────────┤
│  FASE 5 — VALIDAÇÃO FINAL E ENTREGA                              │
│  ├── Checklist Entrega Governada (24 itens)                     │
│  ├── Smoke tests staging + rollback testado                     │
│  └── Produto: entrega/RELATORIO-FINAL.md                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## REGRAS DE OPERAÇÃO DO EXECUTOR GOVERNADO

### 1. Conselheiros são OBRIGATÓRIOS na Fase 0
- Antes de iniciar Fase 1, Executor Governado DEVE consultar os 8 conselheiros
- Cada conselheiro responde em seu formato padrão (conciso, evidência)
- Respostas consolidadas viram "Pareceres do Conselho" no mapeamento contextual
- Se conselheiro identifica bloqueio → Fase 1 não inicia até resolução

### 2. Fase 1 — 120 Perguntas = Mapeamento + Pareceres
- As 120 perguntas originais do AIG mantidas
- Cada categoria enriquecida com parecer do conselheiro correspondente:
  - Cat 1 (Escopo) + Estratégico
  - Cat 2 (Arquitetura) + Crítico + Viabilidade + Futuro
  - Cat 3 (Normas) + Ético + Qualidade
  - Cat 4 (Integrações) + Recursos + Criativo
  - Cat 5 (Dados) + Ético + Viabilidade
  - Cat 6 (Testes) + Qualidade + Crítico
  - Cat 7 (CI/CD) + Viabilidade + Futuro
  - Cat 8 (Segurança) + Ético + Crítico
  - Cat 9 (Performance) + Viabilidade + Futuro
  - Cat 10 (Doc) + Qualidade + Estratégico
  - Cat 11 (Gov) + Estratégico + Ético
  - Cat 12 (Entrega) + Qualidade + Viabilidade

### 3. Execução Paralela Segura (herdada do 12 + 11)
- Planner paralelo decompõe tarefas independentes (DAG de dependências)
- LER-Executor executa missões complexas autônomas
- Executor Governado monitora, valida, agrega evidências
- Paralelismo só para tarefas independentes (sem dependência de contrato)

### 4. Aprendizado Automático (herdado do 10, sem agente separado)
- Cada fase produz evidências → capturadas automaticamente
- `memory_engine.py add` invocado ao final de cada fase
- Artefatos (mapeamento, validação, plano, contratos, testes, runbook, relatório) → aprendizados
- Índice semântico atualizado automaticamente

### 5. Regras de Parada/Escalação (AIG mantidas)
- Bloqueio normativo, decisão, recurso, conflito → BLOQUEIO.md + pergunta estruturada
- **NÃO PARA** exceto nos 4 casos — itera até entrega completa
- Fail closed: validação falha = negação, nunca permissão

---

## ELIMINAÇÃO DE DUPLICAÇÕES

| Funcionalidade | AIG | 09-Executor | 11-LER-Executor | 12-Parallel-Planner | **Fusão** |
|---|---|---|---|---|---|
| Decompor tarefas | Fase 1/3 | ✓ | | ✓ | **Unificada no Executor** |
| Coordenar sub-agentes | | ✓ | ✓ | | **Executor coordena** |
| Delegar ao LER | | | ✓ | | **Executor delega** |
| Paralelismo seguro | | | | ✓ | **Executor planeja + LER executa** |
| Governança/Validação | ✓ | | | | **Núcleo do Executor** |
| Checklist entrega | ✓ | | | | **Fase 5 do Executor** |
| Bloqueios/escalation | ✓ | | | | **Regras do Executor** |

| Funcionalidade | 01-Estrategista | 02-Cético | 03-Realista | 04-Ética | 05-Futuro | 06-Recursos | 07-Criativo | 08-Revisor | **Fusão** |
|---|---|---|---|---|---|---|---|---|---|
| Especialização | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **Mantidos como Conselheiros** |
| Duplicação com AIG | Parcial | Parcial | Parcial | Parcial | Parcial | Parcial | Parcial | Parcial | **Eliminada (consulta obrigatória)** |

---

## ARQUIVOS RESULTANTES

### 1. Novo agente: `config/agents/EXECUTOR-GOVERNADO.md`
- Define o agente unificado com todas as fases, regras, conselheiros
- Substitui AIG, 09, 11, 12

### 2. Atualizações nos Conselheiros
- Cada conselheiro mantém seu arquivo mas header atualizado:
  - `role: conselheiro-especializado`
  - `executor-governado: true` (marca integração)
  - `consulta-obrigatoria-fase: 0`

### 3. Atualizações de configuração
- `config/agents/00-system-rules.md` — adiciona seção "EXECUTOR GOVERNADO"
- `config/opencode.jsonc` — registra executor-governado como agent principal

### 4. Documentação
- `conhecimento/aprendizados/2026-09-12-fusao-executor-governado.md` (este arquivo)
- `docs/agentes/EXECUTOR-GOVERNADO.md` — documentação operacional

---

## EXEMPLO DE INVOCAÇÃO

```bash
# Usuário pede implementação
> "Implemente o módulo de pagamentos com Stripe"

# Executor Governado inicia:
## STATUS: FASE 0 — CONSULTA A CONSELHEIROS
## AÇÃO: Consultando 8 conselheiros especializados
## EVIDÊNCIA: Pareceres consolidados em contexto/pareceres-conselho.md
## PRÓXIMO PASSO: Fase 1 — Mapeamento 120 perguntas
## BLOQUEIOS: nenhum

# Após Fase 0, Pareceres do Conselho anexados ao mapeamento
# Fase 1 executa 120 perguntas + pareceres
# Fase 2 executa validadores
# Fase 3 produz 5 docs
# Fase 4 implementa (delega ao LER missões complexas, planeja paralelismo)
# Fase 5 checklist + entrega
```

---

## BENEFÍCIOS DA FUSÃO

1. **Zero duplicação** — execução, planejamento, paralelismo, LER unificados
2. **Governança centralizada** — um único executor com rigor total
3. **Especialização preservada** — 8 conselheiros trazem visão única sem sobreposição
3. **Aprendizado automático** — evidências → memória sem agente separado
4. **Rastreabilidade total** — cada fase produz artefato rastreável
5. **Fail-closed real** — validação falha = parada, nunca supressão
6. **Conselheiros obrigatórios** — evita viés único, força visão 360°
7. **Ortogonalidade mantida** — Maestro, Flutter, Gerador, CLI agents intactos

---

## PRÓXIMOS PASSOS PARA IMPLEMENTAÇÃO

1. Criar `config/agents/EXECUTOR-GOVERNADO.md` (baseado neste documento)
2. Atualizar 8 conselheiros com header `executor-governado: true`
3. Atualizar `config/opencode.jsonc` com novo agent
4. Remover `AGENTE IMPLEMENTADOR GOVERNADO.MD` (fundido)
5. Remover/arquivar 09-executor.md, 11-ler-executor.md, 12-parallel-planner.md (ou marcar como legacy)
6. Testar invocação completa com projeto real
7. Registrar aprendizado da fusão