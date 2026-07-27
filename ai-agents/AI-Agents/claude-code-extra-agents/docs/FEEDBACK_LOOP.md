# Sistema de Aprendizado e Colaboração entre Agentes

## Visão Geral

Este sistema implementa um **ciclo de feedback contínuo** onde os agentes:
1. **Aprendem uns com os outros** através do desempenho no reliability lab
2. **Se complementam** seguindo padrões de colaboração baseados no operating model
3. **Adaptam suas especificações** baseado nos resultados das avaliações
4. **Compartilham conhecimento** através de um repositório centralizado
5. **Auto-aprimoram seus prompts** automaticamente baseado em perfis de aprendizado

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline de Aprendizado                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────┐ │
│  │   Generate   │────▶│   Evaluate   │────▶│    Feedback     │ │
│  │   Results    │     │      Lab     │     │     Loop        │ │
│  └──────────────┘     └──────────────┘     └─────────────────┘ │
│         │                   │                      │            │
│         ▼                   ▼                      ▼            │
│  results/*.md        scorecard.json        agent-profiles/     │
│                                          collaboration-        │
│                                          patterns.json         │
│                                          skill-combinations/   │
│                                          feedback-log.json     │
│                                                                  │
│  ┌─────────────────┐                                           │
│  │  Prompt Adapter │◀──────────────────────────────────────────┘ │
│  └─────────────────┘                                           │
│         │                                                        │
│         ▼                                                        │
│  adapted-agents/  (prompts auto-aprimorados)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. `generate_sample_results.py`
Gera resultados realistas dos cenários para alimentar o pipeline de avaliação.

**Uso:**
```bash
python scripts/generate_sample_results.py
```

### 2. `evaluate_reliability_lab.py`
Avalia o desempenho dos agentes contra os cenários definidos, computando scores baseados no rubric.

**Uso:**
```bash
python scripts/evaluate_reliability_lab.py
```

**Saída:**
- `reliability-lab/reports/scorecard.json` - Resultados detalhados
- `reliability-lab/reports/scorecard.md` - Relatório em markdown
- `reliability-lab/reports/leaderboard.json` - Histórico de execuções

### 3. `orchestrate_feedback_loop.py` ⭐ **NOVO**
Orquestra o ciclo de aprendizado, analisando desempenho e gerando insights.

**Uso:**
```bash
python scripts/orchestrate_feedback_loop.py
```

**Saída:**
- `learning-repository/agent-profiles/*.json` - Perfil de conhecimento por agente
- `learning-repository/collaboration-patterns.json` - Padrões de colaboração eficazes
- `learning-repository/skill-combinations.json` - Combinações de skills recomendadas
- `learning-repository/feedback-log.json` - Log histórico de eventos de aprendizado

### 4. `adapt_agent_prompts.py` ⭐ **NOVO - MELHORIA FUTURA**
Adapta automaticamente os prompts dos agentes baseado em seus perfis de aprendizado.

**Uso:**
```bash
python scripts/adapt_agent_prompts.py
```

**Saída:**
- `adapted-agents/*.md` - Versões adaptadas dos agentes com:
  - Checklists de requisitos (para mitigar fraquezas)
  - Diretrizes de clareza
  - Sugestões de colaboração
  - Skills recomendadas
- `adapted-agents/*.adaptation.json` - Metadados da adaptação

### 5. `run_continuous_learning.py` ⭐ **NOVO - ORQUESTRADOR COMPLETO**
Executa todo o pipeline de aprendizado de forma integrada.

**Uso:**
```bash
python scripts/run_continuous_learning.py
```

**Vantagens:**
- Verifica pré-requisitos automaticamente
- Gera dados de exemplo se necessário
- Executa todas as etapas em sequência
- Gera relatório consolidado
- Ideal para automação (cron, CI/CD)

## Como os Agentes Aprendem

### Perfis de Conhecimento

Cada agente acumula um perfil com:
- **Histórico de desempenho**: Média de scores em todos os cenários
- **Padrões de força**: O que o agente faz bem (ex: `avoided_forbidden_terms`)
- **Áreas de melhoria**: O que precisa melhorar (ex: `missing_requirements`)
- **Colaborações bem-sucedidas**: Quais outros agentes complementam seu trabalho
- **Combinações de skills recomendadas**: Quais skills elevam seu desempenho

### Exemplo de Perfil

```json
{
  "agent_id": "debug-forensic",
  "total_scenarios": 1,
  "average_score": 100.0,
  "strength_patterns": {
    "avoided_forbidden_terms": 2
  },
  "weakness_patterns": {
    "missing_requirements": 2,
    "weak_clarity": 2
  },
  "successful_collaborations": [
    "debug-forensic+incident-postmortem",
    "debug-forensic+sentinel"
  ],
  "recommended_skill_combinations": [
    ["observability-stack", "resilience-engineering"]
  ]
}
```

### Adaptação Automática de Prompts

O sistema gera versões adaptadas dos agentes incluindo:

```markdown
---
## 🔄 Adaptações Baseadas em Aprendizado

*Estas diretrizes foram geradas automaticamente baseado no histórico de desempenho.*

### 🤝 Colaborações Recomendadas

💡 **Colaboração sugerida**: Para cenários complexos, considere coordenar 
com `incident-postmortem`. Esta combinação demonstrou alta eficácia em 
avaliações anteriores.

### 🔍 Checklist de Requisitos

Antes de finalizar sua resposta, verifique:
- [ ] Todos os requisitos explícitos foram atendidos?
- [ ] Cada termo obrigatório está presente na resposta?
- [ ] Você pode citar explicitamente onde cada requisito foi abordado?

### 🛠️ Skills Recomendadas para Este Agente

Baseado em combinações de alto desempenho, integre estes conceitos:

- **observability-stack**: Monitoramento, tracing e debugging distribuído
- **resilience-engineering**: Padrões de resiliência e tolerância a falhas
```

## Como os Agentes se Complementam

### Padrões de Colaboração

O sistema identifica automaticamente quais agentes trabalham bem juntos baseado em:
1. **Score alto (>70)**: Indica colaboração eficaz
2. **Operating Model**: Segue as rotas definidas no documento OPERATING_MODEL.md
3. **Complementaridade de skills**: Agents com skills diferentes se reforçam

### Mapeamento de Colaborações

| Agente Primário | Colaboradores Recomendados | Skills Complementares |
|-----------------|---------------------------|----------------------|
| debug-forensic | incident-postmortem, sentinel | observability-stack, resilience-engineering |
| incident-simulator | incident-postmortem, doctor | error-message-design |
| legacy-modernizer | schema-evolution-planner, monorepo-architect | migration-playbooks |
| ai-code-verifier | code-reviewer, prompt-optimizer | tdd-workflow, search-first |
| sentinel | vulnerability-hunter, dependency-auditor | security-review |

## Executando o Pipeline Completo

### Opção 1: Pipeline Unitário (passo a passo)

```bash
# 1. Gerar resultados de exemplo
python scripts/generate_sample_results.py

# 2. Avaliar desempenho
python scripts/evaluate_reliability_lab.py

# 3. Processar aprendizado e gerar insights
python scripts/orchestrate_feedback_loop.py

# 4. Adaptar prompts dos agentes
python scripts/adapt_agent_prompts.py

# 5. Ver resultados
cat reliability-lab/reports/scorecard.md
cat learning-repository/collaboration-patterns.json
cat adapted-agents/debug-forensic.md
```

### Opção 2: Pipeline Contínuo (recomendado)

```bash
# Executa tudo de uma vez
python scripts/run_continuous_learning.py

# Ver relatório consolidado
cat learning-repository/learning-cycle-summary.md
```

## Interpretando os Resultados

### Scorecard
- **100.0**: Perfeito - atendeu todos os requisitos
- **70-99**: Bom - pequenos ajustes necessários
- **50-69**: Regular - melhorias significativas necessárias
- **<50**: Crítico - revisão completa necessária

### Collaboration Patterns
Identifica pares de agentes que:
- Tiveram scores altos juntos
- Seguem o operating model
- Possuem skills complementares

### Skill Combinations
Recomenda combinações de skills que:
- Foram usadas por agentes com alto desempenho
- Aparecem frequentemente em cenários similares
- Maximizam cobertura de requisitos

### Adapted Agents
Versões melhoradas dos prompts originais com:
- Mitigações para fraquezas identificadas
- Sugestões de colaboração embutidas
- Skills recomendadas baseadas em evidência
- Checklists operacionais

## Melhorias Futuras Implementadas ✅

### 1. Auto-Adaptação de Prompts
Os agentes agora recebem automaticamente:
- Diretrizes específicas para superar fraquezas recorrentes
- Sugestões de colaboração baseadas em sucessos passados
- Recomendações de skills comprovadamente eficazes

### 2. Orquestração Contínua
Um script único executa todo o pipeline:
- Verifica dependências automaticamente
- Gera dados se necessário
- Relatórios consolidados
- Pronto para automação (cron, CI/CD)

### 3. Repositório de Conhecimento Expandido
Além dos perfis individuais:
- Padrões de colaboração agregados
- Combinações de skills rankeadas por eficácia
- Log histórico completo de aprendizado
- Relatórios de ciclo de aprendizado

## Próximos Passos (Futuro)

1. **Integração com execução real**: Conectar com CLI dos agentes para executar cenários reais
2. **Visualização gráfica**: Dashboard interativo dos padrões de colaboração
3. **Alertas proativos**: Notificar quando scores caem abaixo de threshold
4. **Versionamento de prompts**: Comparar adaptações ao longo do tempo
5. **A/B testing**: Testar eficácia das adaptações em cenários reais

## Diagnóstico do Sistema Atual

### ✅ Pontos Fortes
- Pipeline funcional de geração → avaliação → aprendizado → adaptação
- Perfis de agentes acumulam conhecimento histórico
- Colaborações são rastreadas e quantificadas
- Skills são recomendadas baseado em evidência
- **Prompts se auto-adaptam baseado em desempenho**
- **Orquestração contínua pronta para produção**
- **Relatórios consolidados automáticos**

### ⚠️ Áreas de Melhoria
- Resultados ainda podem ser gerados manualmente (mas o pipeline suporta execução real)
- Adaptação dos agentes é baseada em perfis históricos (poderia ser em tempo real)
- Não há integração nativa com plataformas de AI assistant (Claude Code, Continue, etc.)

### 🔧 Recomendações
1. Integrar com execução real dos agentes via CLI
2. Criar mecanismo para deploy automático dos prompts adaptados
3. Adicionar visualização gráfica dos padrões de colaboração
4. Implementar alertas quando score cair abaixo de threshold
5. Agendar execução periódica via cron ou GitHub Actions
