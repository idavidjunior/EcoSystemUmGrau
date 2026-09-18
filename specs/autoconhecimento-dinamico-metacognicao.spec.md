# SPEC — AUTOCONHECIMENTO DINÂMICO E METACOGNIÇÃO

Versão: 1.0
Status: Normativa
Escopo: Todo o Ecossistema
Aplicação: OpenCode, LER, Jarvis, agentes, módulos de aprendizado e governança.

---

## 1. OBJETIVO E PRINCÍPIO CENTRAL

Transformar o autoconhecimento do ecossistema de **estático** para **dinâmico**, adicionando capacidade de autocrítica contínua e metacognição sistemática.

**«O ecossistema deve saber o que sabe, o que não sabe, e como está performando em tempo real.»**

---

## 2. PROBLEMA ATUAL

### 2.1 Autoconhecimento Estático
- Knowledge graph atualiza apenas manualmente ou via batch
- Inventário de estruturas é snapshot, não dinâmico
- Não há monitoramento em tempo real do próprio estado

### 2.2 Ausência de Autocrítica Contínua
- Não há avaliação automática de performance
- Erros e falhas não são analisados sistematicamente
- Não há detecção de regressão ou degradação

### 2.3 Falta de Metacognição
- Ecossistema não sabe "o que não sabe"
- Não há identificação sistemática de lacunas de conhecimento
- Não há mapeamento de fronteiras de competência

---

## 3. SOLUÇÃO PROPOSTA

### 3.1 Arquitetura em Três Camadas

**Camada 1: Autoconhecimento Dinâmico**
- Monitoramento em tempo real do estado do ecossistema
- Inventário dinâmico de estruturas ativas
- Health checks contínuos de todos os componentes
- Atualização automática do knowledge graph

**Camada 2: Autocrítica Contínua**
- Análise automática de erros e falhas
- Detecção de regressão e degradação
- Avaliação de performance por componente
- Geração de métricas de qualidade

**Camada 3: Metacognição**
- Identificação sistemática de lacunas de conhecimento
- Mapeamento de fronteiras de competência
- Classificação de confiança por domínio
- Recomendação de aprendizado priorizado

---

## 4. IMPLEMENTAÇÃO

### 4.1 Autoconhecimento Dinâmico

#### 4.1.1 Monitoramento em Tempo Real
**Componente**: `scripts/dynamic_self_knowledge.py`

**Funcionalidades**:
- Scanner contínuo de estruturas ativas (agentes, skills, scripts, MCPs)
- Detecção de alterações em tempo real
- Atualização dinâmica do inventário
- Publicação de estado via WebSocket

**Interface**:
```python
class DynamicSelfKnowledge:
    def scan_structures(self) -> dict
    def detect_changes(self) -> list
    def update_inventory(self) -> bool
    def publish_state(self) -> None
```

#### 4.1.2 Health Checks Contínuos
**Componente**: `scripts/health_monitor.py`

**Funcionalidades**:
- Health check de todos os serviços (Jarvis, TTS, Vigilante, MCPs)
- Verificação de integridade de dados
- Monitoramento de recursos (CPU, memória, disco)
- Alertas automáticos de degradação

**Interface**:
```python
class HealthMonitor:
    def check_service(self, service: str) -> dict
    def check_integrity(self) -> dict
    def check_resources(self) -> dict
    def generate_alert(self, severity: str, message: str) -> None
```

#### 4.1.3 Atualização Automática do Knowledge Graph
**Componente**: Extensão do `ler-runtime/knowledge/`

**Funcionalidades**:
- Integração em tempo real com autoconhecimento dinâmico
- Atualização incremental do knowledge graph
- Versão timestamped para rollback
- Sincronização bidirecional com Obsidian

**Interface**:
```python
class DynamicKnowledgeGraph:
    def incremental_update(self, changes: list) -> bool
    def create_snapshot(self) -> str
    def rollback_to(self, timestamp: str) -> bool
    def sync_obsidian(self) -> bool
```

### 4.2 Autocrítica Contínua

#### 4.2.1 Análise Automática de Erros
**Componente**: `scripts/error_analyzer.py`

**Funcionalidades**:
- Coleta automática de logs de erro
- Classificação por tipo e severidade
- Análise de padrões de falha
- Geração de relatórios de autocrítica

**Interface**:
```python
class ErrorAnalyzer:
    def collect_errors(self, timeframe: str) -> list
    def classify_error(self, error: dict) -> dict
    def detect_patterns(self, errors: list) -> list
    def generate_self_critique(self) -> dict
```

#### 4.2.2 Detecção de Regressão
**Componente**: `scripts/regression_detector.py`

**Funcionalidades**:
- Comparação de performance ao longo do tempo
- Detecção de degradação de qualidade
- Alertas de regressão funcional
- Baseline automático de performance

**Interface**:
```python
class RegressionDetector:
    def measure_performance(self, component: str) -> dict
    def compare_with_baseline(self, current: dict, baseline: dict) -> dict
    def detect_regression(self) -> list
    def update_baseline(self) -> bool
```

#### 4.2.3 Avaliação de Performance por Componente
**Componente**: `scripts/performance_evaluator.py`

**Funcionalidades**:
- Métricas de tempo de resposta
- Taxa de sucesso por componente
- Qualidade de respostas (via ResponseNormalizer)
- Ranking de componentes por performance

**Interface**:
```python
class PerformanceEvaluator:
    def measure_response_time(self, component: str) -> float
    def calculate_success_rate(self, component: str) -> float
    def evaluate_response_quality(self, component: str) -> dict
    def rank_components(self) -> list
```

### 4.3 Metacognição

#### 4.3.1 Identificação de Lacunas de Conhecimento
**Componente**: `scripts/knowledge_gap_detector.py`

**Funcionalidades**:
- Análise de perguntas sem resposta satisfatória
- Detecção de domínios pouco explorados
- Identificação de termos técnicos não explicados
- Mapeamento de fronteiras de competência

**Interface**:
```python
class KnowledgeGapDetector:
    def analyze_unanswered_questions(self) -> list
    def detect_underexplored_domains(self) -> list
    def find_unexplained_terms(self) -> list
    def map_competence_boundaries(self) -> dict
```

#### 4.3.2 Classificação de Confiança por Domínio
**Componente**: `scripts/confidence_classifier.py`

**Funcionalidades**:
- Classificação de confiança por domínio de conhecimento
- Identificação de domínios de alta/baixa confiança
- Recomendação de investimento em aprendizado
- Visualização de mapa de confiança

**Interface**:
```python
class ConfidenceClassifier:
    def classify_domain_confidence(self, domain: str) -> dict
    def identify_low_confidence_domains(self) -> list
    def recommend_learning_investment(self) -> list
    def visualize_confidence_map(self) -> str
```

#### 4.3.3 Recomendação de Aprendizado Priorizado
**Componente**: `scripts/learning_prioritizer.py`

**Funcionalidades**:
- Priorização de aprendizado baseada em lacunas e confiança
- Geração de roadmap de aprendizado
- Sugerência de skills a desenvolver
- Integração com agente 10-Aprendizado

**Interface**:
```python
class LearningPrioritizer:
    def prioritize_learning(self, gaps: list, confidence: dict) -> list
    def generate_roadmap(self) -> dict
    def suggest_skills(self) -> list
    def integrate_with_agent_10(self) -> bool
```

---

## 5. INTEGRAÇÃO

### 5.1 Integração com Componentes Existentes

**ResponseNormalizer**:
- Coletar métricas de qualidade de resposta
- Passar dados de checklist para autocrítica
- Identificar padrões de problemas

**Memory Engine**:
- Registrar eventos de autocrítica
- Persistir lacunas de conhecimento
- Man histórico de performance

**Vigilante**:
- Incorporar health checks dinâmicos
- Atualizar inventário automaticamente
- Publicar estado de autoconhecimento

**LER Runtime**:
- Integrar autocrítica no loop de aprendizado
- Usar metacognição para direcionar exploração
- Atualizar knowledge graph dinamicamente

### 5.2 Nova Arquitetura de Autoconhecimento

```
┌─────────────────────────────────────────────────────────────┐
│                  ECOSYSTEMA AUTOCONHECIMENTO                │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌───────────────────────┐   ┌─────────────────────────────┐
│ CAMADA 1: DINÂMICO   │   │ CAMADA 2: AUTOCRÍTICA     │
│ - Scanner contínuo    │   │ - Análise de erros         │
│ - Health checks      │   │ - Detecção de regressão    │
│ - Inventário dinâmico │   │ - Avaliação de performance │
│ - Monitoramento RT    │   │ - Métricas de qualidade    │
└──────────┬────────────┘   └────────────┬────────────────┘
           │                              │
           └──────────────┬───────────────┘
                          ▼
              ┌─────────────────────────────┐
              │ CAMADA 3: METACOGNIÇÃO     │
              │ - Lacunas de conhecimento  │
              │ - Confiança por domínio    │
              │ - Priorização de aprendizado│
              │ - Fronteiras de competência │
              └──────────┬──────────────────┘
                         │
                         ▼
              ┌─────────────────────────────┐
              │   KNOWLEDGE GRAPH DINÂMICO  │
              │   (atualização contínua)     │
              └─────────────────────────────┘
```

---

## 6. PIPELINE DE AUTOCRÍTICA

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

---

## 7. CRITÉRIOS DE SUCESSO

### 7.1 Autoconhecimento Dinâmico
- [ ] Inventário atualizado em tempo real (< 1min de latência)
- [ ] Health checks executados a cada 5min
- [ ] Knowledge graph atualizado incrementalmente
- [ ] Estado publicado via WebSocket

### 7.2 Autocrítica Contínua
- [ ] Erros analisados automaticamente
- [ ] Regressão detectada em < 24h
- [ ] Performance medida por componente
- [ ] Métricas de qualidade coletadas

### 7.3 Metacognição
- [ ] Lacunas identificadas sistematicamente
- [ ] Confiança classificada por domínio
- [ ] Aprendizado priorizado automaticamente
- [ ] Fronteiras de competência mapeadas

---

## 8. RISCOS E MITIGAÇÃO

### 8.1 Sobrecarga de Monitoramento
**Risco**: Scanner contínuo pode consumir muitos recursos
**Mitigação**: Throttling, priorização de componentes críticos

### 8.2 Falsos Positivos em Regressão
**Risco**: Detecção de regressão onde não existe
**Mitigação**: Thresholds conservadores, confirmação manual

### 8.3 Lacunas Falsas
**Risco**: Identificação de lacunas onde há conhecimento
**Mitigação**: Validação cruzada com múltiplas fontes

---

## 9. IMPLEMENTAÇÃO FASEADA

### Fase 1: Autoconhecimento Dinâmico (Semanas 1-2)
- Implementar scanner contínuo
- Health checks básicos
- Inventário dinâmico

### Fase 2: Autocrítica Contínua (Semanas 3-4)
- Análise de erros
- Detecção de regressão
- Métricas de performance

### Fase 3: Metacognição (Semanas 5-6)
- Detecção de lacunas
- Classificação de confiança
- Priorização de aprendizado

### Fase 4: Integração e Refinamento (Semanas 7-8)
- Integração com componentes existentes
- Refinamento de thresholds
- Documentação e treinamento

---

## 10. RESULTADO ESPERADO

Ao final da implementação, o ecossistema deve:

**«Saber o que sabe, o que não sabe, e como está performando em tempo real.»**

- Autoconhecimento atualizado continuamente
- Autocrítica automática de performance
- Metacognição sistemática de lacunas
- Aprendizado direcionado por prioridade
- Mapa visual de confiança por domínio

---

## 11. REFERÊNCIAS

- Constituição do Ecossistema (`config/agents/00-system-rules.md`)
- Knowledge Graph (`ler-runtime/knowledge/knowledge_graph.json`)
- ResponseNormalizer (`scripts/response_normalizer.py`)
- Memory Engine (`scripts/memory_engine.py`)
- Vigilante (`scripts/vigilante.ps1`)
- SPEC Padrão Universal de Resposta (`specs/padrao-universal-resposta.spec.md`)
