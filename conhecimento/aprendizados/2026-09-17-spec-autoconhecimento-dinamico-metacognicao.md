---
tipo: spec
tags: [spec, autoconhecimento, metacognicao, autocrítica, dinamico, learning-gap, confidence, performance]
data: 2026-09-17
contexto: Usuario perguntou sobre o estado do autoconhecimento do ecossistema. Verifiquei que o ecossistema tem autoconhecimento avançado estatico (knowledge graph, inventario, memoria) mas falta autoconhecimento dinamico, autocrítica continua e metacognicao. Usuario pediu para criar SPEC para implementar os tres itens que faltam.
decisao: Criar SPEC completa de Autoconhecimento Dinâmico e Metacognicao com arquitetura em tres camadas: (1) Autoconhecimento Dinâmico (scanner continuo, health checks, inventario dinamico), (2) Autocrítica Continua (analise de erros, deteccao de regressao, avaliacao de performance), (3) Metacognicao (lacunas de conhecimento, confianca por dominio, priorizacao de aprendizado).
impacto: Arquitetura definida para transformar autoconhecimento de estatico para dinamico com monitoramento em tempo real, autocrítica automatica e metacognicao sistematica. Pipeline de autocrítica definido: EVENTO -> COLETA -> ANALISE -> METACOGNICAO -> PRIORIZACAO -> ACAO -> REGISTRO -> PUBLICACAO.
validacao: SPEC criada com interfaces detalhadas para cada componente, criterios de sucesso claros, implementacao faseada em 8 semanas, e mitigacao de riscos.
licao: Autoconhecimento dinamico requer arquitetura de tres camadas interdependentes. Monitoramento continuo precisa de throttling para nao sobrecarregar recursos. Autocrítica deve ter thresholds conservadores para evitar falsos positivos. Metacognicao depende de analise sistematica de lacunas e confianca, nao apenas de coleta de dados.
---

# SPEC de Autoconhecimento Dinâmico e Metacognição

## STATUS

SPEC criada para implementar autoconhecimento dinâmico, autocrítica contínua e metacognição no ecossistema.

## O que aconteceu

Usuário perguntou sobre o estado do autoconhecimento do ecossistema. Verifiquei que o ecossistema tem autoconhecimento avançado estático (knowledge graph com 611 entradas, inventário de estruturas, memória persistente) mas falta:

1. **Autoconhecimento dinâmico** - Atualização em tempo real
2. **Autocrítica contínua** - Avaliação automática de performance
3. **Metacognição** - Saber "o que não sabe" sistematicamente

## O que foi feito

### 1. Diagnóstico do estado atual
**Autoconhecimento existente:**
- ✅ Sistema automático de captura de conhecimento
- ✅ Knowledge graph com projeto "ecosistema-opencode"
- ✅ Inventário de estruturas (16 agentes, specs, scripts)
- ✅ Memória persistente (611 entradas)
- ✅ Agente 10-Aprendizado
- ✅ Ponte LER para sincronização

**Limitações identificadas:**
- ❌ Autoconhecimento estático, não dinâmico
- ❌ Sem autocrítica contínua
- ❌ Sem metacognição sistemática

### 2. Arquitetura proposta

**Camada 1: Autoconhecimento Dinâmico**
- `scripts/dynamic_self_knowledge.py` - Scanner contínuo de estruturas
- `scripts/health_monitor.py` - Health checks contínuos
- Extensão do `ler-runtime/knowledge/` - Atualização automática do knowledge graph

**Camada 2: Autocrítica Contínua**
- `scripts/error_analyzer.py` - Análise automática de erros
- `scripts/regression_detector.py` - Detecção de regressão
- `scripts/performance_evaluator.py` - Avaliação de performance por componente

**Camada 3: Metacognição**
- `scripts/knowledge_gap_detector.py` - Identificação de lacunas
- `scripts/confidence_classifier.py` - Classificação de confiança por domínio
- `scripts/learning_prioritizer.py` - Priorização de aprendizado

### 3. Pipeline de autocrítica

```
EVENTO (erro/mudança/pergunta)
  ↓
COLETA DE DADOS
  ↓
ANÁLISE (classificação/padrão)
  ↓
METACOGNIÇÃO (lacunas/confiança)
  ↓
PRIORIZAÇÃO (aprendizado)
  ↓
AÇÃO (atualização/alerta/recomendação)
  ↓
REGISTRO (memory engine)
  ↓
PUBLICAÇÃO (WebSocket/grafo)
```

### 4. Integração com componentes existentes

**ResponseNormalizer:**
- Coletar métricas de qualidade de resposta
- Passar dados de checklist para autocrítica
- Identificar padrões de problemas

**Memory Engine:**
- Registrar eventos de autocrítica
- Persistir lacunas de conhecimento
- Manter histórico de performance

**Vigilante:**
- Incorporar health checks dinâmicos
- Atualizar inventário automaticamente
- Publicar estado de autoconhecimento

**LER Runtime:**
- Integrar autocrítica no loop de aprendizado
- Usar metacognição para direcionar exploração
- Atualizar knowledge graph dinamicamente

## Resultado

**SPEC criada** em `specs/autoconhecimento-dinamico-metacognicao.spec.md` com:

- Arquitetura em três camadas definida
- Interfaces detalhadas para cada componente
- Critérios de sucesso claros por camada
- Pipeline de autocrítica completo
- Integração com componentes existentes
- Implementação faseada em 8 semanas
- Mitigação de riscos

**Caminho para implementação:**

**Fase 1 (Semanas 1-2):** Autoconhecimento Dinâmico
- Scanner contínuo de estruturas
- Health checks básicos
- Inventário dinâmico

**Fase 2 (Semanas 3-4):** Autocrítica Contínua
- Análise de erros
- Detecção de regressão
- Métricas de performance

**Fase 3 (Semanas 5-6):** Metacognição
- Detecção de lacunas
- Classificação de confiança
- Priorização de aprendizado

**Fase 4 (Semanas 7-8):** Integração e Refinamento
- Integração com componentes existentes
- Refinamento de thresholds
- Documentação e treinamento

## Impacto

Transformação do autoconhecimento de **estático** para **dinâmico**:

- Inventário atualizado em tempo real (< 1min de latência)
- Health checks executados a cada 5min
- Knowledge graph atualizado incrementalmente
- Erros analisados automaticamente
- Regressão detectada em < 24h
- Performance medida por componente
- Lacunas identificadas sistematicamente
- Confiança classificada por domínio
- Aprendizado priorizado automaticamente

## Pendências

Implementação das fases conforme cronograma de 8 semanas.

## Próximo passo

Escolher qual fase iniciar ou aguardar aprovação da SPEC.
