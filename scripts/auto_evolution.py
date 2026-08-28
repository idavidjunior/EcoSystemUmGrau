"""Auto-Evolution Engine — Motor de Auto-Aprendizado e Evolução do Ecossistema.

Analisa ferramentas externas (ex: Cartographer), compara com capacidades
atuais do EcoSystemUmGrau, detecta gaps, gera planos de evolução e
incorpora capacidades de forma segura e organizada.

Princípios:
- Nunca quebra o que funciona
- Toda mudança passa por preflight
- Persiste aprendizados via memory_engine
- Comunica antes, durante e depois

Uso:
    python scripts/auto_evolution.py scan                # Escaneia referência externa
    python scripts/auto_evolution.py gaps                # Mostra gaps vs referência
    python scripts/auto_evolution.py plan                # Gera plano de evolução
    python scripts/auto_evolution.py assess              # Auto-avaliação completa
    python scripts/auto_evolution.py evolve [--apply]    # Executa evoluções (dry-run por padrão)
    python scripts/auto_evolution.py status              # Status da auto-evolução
"""

import os
import sys
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME = os.path.join(BASE, 'runtime')
KNOWLEDGE = os.path.join(BASE, 'conhecimento')
LEARNING_DIR = os.path.join(RUNTIME, 'learning')
EVOLUTION_DIR = os.path.join(LEARNING_DIR, 'evolution')

sys.path.insert(0, SCRIPTS)

def _ensure_dirs():
    for d in [RUNTIME, LEARNING_DIR, EVOLUTION_DIR]:
        os.makedirs(d, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# 1. ONTOLOGIA DE REFERÊNCIA (Cartographer)
# ═══════════════════════════════════════════════════════════════════
# O que o Cartographer oferece, mapeado para o ecossistema.

REFERENCE_ENTITY_KINDS = {
    'boundary': 'Região nomeada com interface pública (módulo, pacote, subsistema)',
    'capability': 'Algo que o sistema faz (função, método, handler)',
    'actor': 'Entrypoint onde intenção externa chega (rota, CLI, listener)',
    'entity': 'Coisa com estado que persiste ou se transforma (DB, sessão, cache)',
    'transition': 'Mudança de estado ou link causal entre capabilities',
    'dependency': 'Dependência estrutural',
    'side-effect': 'Consequência observável fora do boundary atual',
    'async-process': 'Comportamento que atravessa tempo ou contextos de execução',
    'invariant': 'Propriedade que deve ser verdadeira em todas operações',
    'failure-point': 'Local onde o sistema pode falhar ou degradar',
}

REFERENCE_RELATIONSHIP_KINDS = {
    'contains': 'Boundary contém outro elemento',
    'invokes': 'Capability chama outra',
    'renders': 'Capability renderiza UI',
    'reads': 'Capability lê estado',
    'writes': 'Capability escreve estado',
    'depends-on': 'Dependência estrutural',
    'triggers': 'Capability causa efeito externo',
    'produces': 'Capability cria nova instância',
    'consumes': 'Capability destrói/absorve',
    'guards': 'Invariant restringe transição',
    'exposes': 'Boundary expõe Capability (interface pública)',
    'enters-at': 'Actor entra em Boundary (onde intenção chega)',
}

REFERENCE_CONFIDENCE_LEVELS = {
    'proven': 'Análise determinística do source. Verificável.',
    'high': 'Evidência forte, um passo de inferência.',
    'medium': 'Inferência plausível de múltiplos sinais.',
    'low': 'Inferência fraca, provável mas incerto.',
    'speculative': 'Hipótese, sem suporte de evidência.',
}

REFERENCE_CAPABILITIES = {
    'world_model': {
        'name': 'World-Model Persistente',
        'description': 'Modelo de entidades, relações e comportamentos persistido em JSON',
        'components': ['entity_store', 'relationship_store', 'slice_store', 'perspectives'],
        'mcp_tools': [
            'cartographer_write_entity', 'cartographer_write_relationship',
            'cartographer_query', 'cartographer_write_slice',
            'cartographer_get_entity', 'cartographer_set_project',
            'cartographer_create_perspective', 'cartographer_switch_perspective',
            'cartographer_list_perspectives', 'cartographer_snapshot',
            'cartographer_list_snapshots', 'cartographer_restore',
            'cartographer_get_summary', 'cartographer_open_map',
            'cartographer_check_depth', 'cartographer_delete_entity',
            'cartographer_clear',
        ],
        'pattern': 'write → query → persist → snapshot → restore',
    },
    'evidence_grounding': {
        'name': 'Evidence-Grounded Facts',
        'description': 'Toda afirmação rastreia até source:line com snippet',
        'components': ['source_anchors', 'confidence_levels', 'provenance_tracking'],
        'pattern': 'fact → anchors[] → confidence → provenance → reasoning',
    },
    'behavior_slices': {
        'name': 'Behavior Slices',
        'description': 'Fluxos de comportamento (orderados) e changesets de PR',
        'components': ['flow_narratives', 'changeset_tracking', 'step_ordering'],
        'pattern': 'slice → steps[] → entityId → label → changeType',
    },
    'perspectives': {
        'name': 'Perspectives (Lentes Nomeadas)',
        'description': 'Visões filtradas sobre o pool de entidades',
        'components': ['named_tabs', 'auto_assignment', 'boundary_derived'],
        'pattern': 'create → switch → entities join active perspective',
    },
    'snapshots': {
        'name': 'Snapshots & Restore',
        'description': 'Backup/restore atômico do modelo inteiro',
        'components': ['atomic_write', 'prune_old', 'pre_restore_backup'],
        'pattern': 'snapshot(label) → restore(filename) → pre-restore backup',
    },
    'browser_ui': {
        'name': 'Browser UI (React Flow)',
        'description': 'Visualização interativa do grafo em tempo real via WebSocket',
        'components': ['react_flow', 'websocket', 'real_time_broadcast'],
        'pattern': 'connect WS → snapshot → entity:added → broadcast',
    },
    'depth_check': {
        'name': 'Depth Check',
        'description': 'Validação de profundidade antes de sintetizar',
        'components': ['boundary_depth', 'slice_presence', 'perspective_check'],
        'pattern': 'check → issues[] → passed → ok_to_synthesize',
    },
}


# ═══════════════════════════════════════════════════════════════════
# 2. MAPA DE CAPACIDADES DO ECOSSISTEMA
# ═══════════════════════════════════════════════════════════════════

ECOSYSTEM_CAPABILITIES = {
    'memory_engine': {
        'name': 'Motor de Memória (memory_engine.py)',
        'description': 'Memória episódica com decay de Ebbinghaus, tipos: decisao/erro/padrao/episodio/contexto/preferencia',
        'components': ['ebbinghaus_decay', 'semantic_tags', 'session_tracking', 'query_by_tag'],
        'pattern': 'add(title, summary, kind) → query(termo) → context(project)',
        'coverage': 'high',
    },
    'knowledge_graph': {
        'name': 'Knowledge Graph (knowledge_graph.py)',
        'description': 'Grafo de conhecimento com BM25 semântico para busca',
        'components': ['bm25_search', 'tfidf_index', 'nodes', 'edges'],
        'pattern': 'add_node → add_edge → search(query)',
        'coverage': 'high',
    },
    'mcp_servers': {
        'name': 'MCP Servers (13 domínios)',
        'description': 'Servidores MCP por domínio: desenvolvimento, android, internet, browser, dev-tools, memoria, multimidia, comportamentais, compreensao-pedidos, obsidian',
        'components': ['mcp_desenvolvimento', 'mcp_android', 'mcp_internet', 'mcp_browser', 'mcp_dev_tools', 'mcp_memoria', 'mcp_multimidia', 'mcp_comportamentais', 'mcp_compreensao_pedidos', 'mcp_obsidian'],
        'pattern': 'server.py → tools → SKILL.md',
        'coverage': 'high',
    },
    'runtime_state': {
        'name': 'Runtime Persistente (runtime_state.py)',
        'description': 'Estado persistente entre sessões: projeto ativo, objetivo, última tarefa, pendências',
        'components': ['state_persistence', 'checkpoint', 'restore', 'last_task'],
        'pattern': 'set(key, value) → get(key) → checkpoint(label)',
        'coverage': 'high',
    },
    'runtime_boot': {
        'name': 'Bootloader (runtime_boot.py)',
        'description': 'Boot obrigatório: verifica integridade, restaura estado, carrega memória',
        'components': ['integrity_check', 'state_restore', 'memory_load', 'greeting'],
        'pattern': 'boot → check → restore → greet',
        'coverage': 'high',
    },
    'runtime_kernel': {
        'name': 'Kernel (runtime_kernel.py)',
        'description': 'Autoridade máxima: contrato-entrada, check-resposta, validação',
        'components': ['contract_entry', 'check_response', 'validation'],
        'pattern': 'contrato-entrada → execute → check → approve',
        'coverage': 'high',
    },
    'runtime_context': {
        'name': 'Context Loader (runtime_context.py)',
        'description': 'Carrega contexto relevante por assunto (BM25 semântico)',
        'components': ['bm25_context', 'relevance_filter'],
        'pattern': 'load(assunto) → filter → return context',
        'coverage': 'medium',
    },
    'runtime_auditor': {
        'name': 'Auditor Adaptativo (runtime_auditor.py)',
        'description': 'Audita respostas, classifica criticidade, reprova e devolve ao ciclo',
        'components': ['criticality_classification', 'audit_response', 'reject_fix'],
        'pattern': 'audit(objetivo, resposta) → approve/reject',
        'coverage': 'high',
    },
    'graphify': {
        'name': 'Graphify (mcp/desenvolvimento)',
        'description': 'Converte pastas em knowledge graphs com community detection',
        'components': ['knowledge_graph_generation', 'community_detection', 'html_viz'],
        'pattern': 'folder → index → graph → report',
        'coverage': 'medium',
    },
    'learning_engine': {
        'name': 'Learning Engine (learning_engine.py)',
        'description': 'Aprendizado contínuo automático: captura de tarefas, decisões, padrões',
        'components': ['auto_capture', 'task_metrics', 'pattern_detection', 'improvement_suggestions'],
        'pattern': 'capture → analyze → suggest → persist',
        'coverage': 'medium',
    },
    'self_assessment': {
        'name': 'Self-Assessment Engine (self_assessment_engine.py)',
        'description': 'Autoavaliação, diagnóstico, medição e detecção de drift',
        'components': ['metrics_collection', 'baseline_tracking', 'drift_detection'],
        'pattern': 'measure → baseline → detect_drift → report',
        'coverage': 'medium',
    },
    'improvement_engine': {
        'name': 'Improvement Engine (improvement_engine.py)',
        'description': 'Motor de melhorias: experimentação, rollback, ciclo PDCA',
        'components': ['experiment', 'rollback', 'pdca_cycle'],
        'pattern': 'detect → plan → experiment → validate → commit/revert',
        'coverage': 'medium',
    },
    'compreensao_pedidos': {
        'name': 'Compreensão de Pedidos (mcp-compreensao-pedidos)',
        'description': 'Análise estática + refino LLM de pedidos antes de executar',
        'components': ['static_analysis', 'llm_refinement', 'concept_resolution', 'waste_detection'],
        'pattern': 'compreender → avaliar_clareza → refinar → resolver_conceitos',
        'coverage': 'high',
    },
    'validation': {
        'name': 'Validação de Respostas (validar_resposta.py)',
        'description': 'Validação pt-BR de respostas antes de entrega',
        'components': ['lexical_analysis', 'accent_detection', 'contraction_patterns', 'llm_translation'],
        'pattern': 'generate → validate → approve/translate/regenerate',
        'coverage': 'high',
    },
    'preflight': {
        'name': 'Preflight Técnico + Ético',
        'description': 'Gates obrigatórios antes de alterações: preflight_check + preflight_etica',
        'components': ['technical_preflight', 'ethical_preflight'],
        'pattern': 'validate → pass/fail → block/allow',
        'coverage': 'high',
    },
    'sync': {
        'name': 'Sincronização (sync_rules.py + persistencia.ps1)',
        'description': 'Sync 3 camadas (Constituição ↔ AGENTS.md ↔ Deployed) + git gate',
        'components': ['rule_sync', 'config_deploy', 'git_gate', 'memory_sync'],
        'pattern': 'sync_rules audit → deploy config → preflight → git sync',
        'coverage': 'high',
    },
    'ecomodelo': {
        'name': 'Model Monitor (model_monitor.py)',
        'description': 'Monitoramento inteligente de modelos: performance, limites, troca automática',
        'components': ['performance_tracking', 'limit_monitoring', 'auto_switch'],
        'pattern': 'monitor → metrics → switch_if_needed',
        'coverage': 'medium',
    },
}


# ═══════════════════════════════════════════════════════════════════
# 3. ANÁLISE COMPARATIVA
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Gap:
    """Gap detectado entre referência e ecossistema."""
    reference_id: str
    reference_name: str
    description: str
    severity: str  # critical, high, medium, low
    ecosystem_equivalent: Optional[str]
    action: str  # create, enhance, integrate, skip
    rationale: str
    effort: str  # small, medium, large
    risk: str  # low, medium, high

@dataclass
class EvolutionPlan:
    """Plano de evolução para incorporar uma capacidade."""
    gap: Gap
    implementation_steps: List[str]
    files_to_create: List[str]
    files_to_modify: List[str]
    dependencies: List[str]
    validation_criteria: List[str]
    rollback_plan: str
    priority: int  # 1=highest


def analyze_gaps() -> List[Gap]:
    """Compara capacidades da referência (Cartographer) com o ecossistema."""
    gaps = []

    # --- 1. World-Model Entity Kinds ---
    eco_entity_types = set()
    for cap in ECOSYSTEM_CAPABILITIES.values():
        for comp in cap.get('components', []):
            eco_entity_types.add(comp)

    for kind, desc in REFERENCE_ENTITY_KINDS.items():
        mapped_eco = None
        for eco_kind in eco_entity_types:
            if kind in eco_kind or eco_kind in kind:
                mapped_eco = eco_kind
                break

        if not mapped_eco:
            gaps.append(Gap(
                reference_id=f'entity_kind:{kind}',
                reference_name=f'Entity Kind: {kind}',
                description=desc,
                severity='medium' if kind in ('boundary', 'capability', 'actor', 'entity') else 'low',
                ecosystem_equivalent=None,
                action='integrate',
                rationale=f'Ontologia do Cartographer define "{kind}" — o ecossistema pode se beneficiar desse tipo de entidade para mapeamento mais preciso.',
                effort='small',
                risk='low',
            ))

    # --- 2. Relationship Kinds ---
    eco_rel_types = {'contains', 'depends-on'}  # eco já tem
    for kind, desc in REFERENCE_RELATIONSHIP_KINDS.items():
        if kind not in eco_rel_types:
            gaps.append(Gap(
                reference_id=f'relationship:{kind}',
                reference_name=f'Relationship: {kind}',
                description=desc,
                severity='medium' if kind in ('invokes', 'reads', 'writes', 'triggers') else 'low',
                ecosystem_equivalent=None,
                action='integrate',
                rationale=f'Tipo de relação "{kind}" permite rastrear fluxos de dados e chamadas no grafo.',
                effort='small',
                risk='low',
            ))

    # --- 3. Confidence Levels ---
    if not any('confidence' in c.lower() for c in eco_entity_types):
        gaps.append(Gap(
            reference_id='evidence:confidence',
            reference_name='Confidence Levels',
            description='Níveis de confiança (proven/high/medium/low/speculative) para fatos',
            severity='high',
            ecosystem_equivalent=None,
            action='integrate',
            rationale='O ecossistema atual não diferencia níveis de confiança em memórias e knowledge graph — isso afeta qualidade de respostas.',
            effort='medium',
            risk='low',
        ))

    # --- 4. Evidence Grounding (Source Anchors) ---
    if not any('anchor' in c.lower() or 'evidence' in c.lower() for c in eco_entity_types):
        gaps.append(Gap(
            reference_id='evidence:source_anchors',
            reference_name='Evidence-Grounded Facts',
            description='Toda afirmação deve rastrear até source:line com snippet verbatim',
            severity='high',
            ecosystem_equivalent='knowledge_graph (parcial)',
            action='enhance',
            rationale='O knowledge_graph já tem nodes/edges mas não exige source anchors — memórias e aprendizados ficam sem rastreabilidade.',
            effort='large',
            risk='medium',
        ))

    # --- 5. Behavior Slices ---
    if 'slice_store' not in eco_entity_types:
        gaps.append(Gap(
            reference_id='behavior:slices',
            reference_name='Behavior Slices',
            description='Fluxos de comportamento ordenados (orderados) e changesets de PR',
            severity='high',
            ecosystem_equivalent=None,
            action='create',
            rationale='O ecossistema não tem conceito de "fluxo de comportamento ordenado" — é essencial para auditar o que acontece quando X dispara.',
            effort='large',
            risk='low',
        ))

    # --- 6. Perspectives (Named Lenses) ---
    if 'perspectives' not in eco_entity_types:
        gaps.append(Gap(
            reference_id='ui:perspectives',
            reference_name='Perspectives (Named Lenses)',
            description='Visões filtradas sobre o pool de entidades, como tabs por concern',
            severity='medium',
            ecosystem_equivalent=None,
            action='create',
            rationale='Perspectives permitem focar em subconjuntos do grafo (ex: "auth", "data-flow") — melhora UX de navegação do grafo.',
            effort='medium',
            risk='low',
        ))

    # --- 7. Snapshots & Atomic Restore ---
    has_snapshots = any('snapshot' in c.lower() for c in eco_entity_types)
    if not has_snapshots:
        gaps.append(Gap(
            reference_id='persistence:snapshots',
            reference_name='Snapshots & Atomic Restore',
            description='Backup/restore atômico com pre-restore backup automático',
            severity='high',
            ecosystem_equivalent='runtime_state (parcial)',
            action='enhance',
            rationale='runtime_state tem checkpoint mas não tem restore atômico nem pre-restore backup — risk de perda de estado.',
            effort='medium',
            risk='low',
        ))

    # --- 8. Browser UI (Real-time) ---
    if 'websocket' not in eco_entity_types and 'react_flow' not in eco_entity_types:
        gaps.append(Gap(
            reference_id='ui:browser_realtime',
            reference_name='Browser UI (Real-time WebSocket)',
            description='Visualização interativa do grafo com atualização em tempo real',
            severity='medium',
            ecosystem_equivalent='ecow (widget_grafo.py)',
            action='enhance',
            rationale='O ecossistema já tem o widget EcOW mas não usa WebSocket para updates em tempo real — pode ser melhorado.',
            effort='large',
            risk='medium',
        ))

    # --- 9. Depth Check ---
    if 'depth_check' not in eco_entity_types:
        gaps.append(Gap(
            reference_id='quality:depth_check',
            reference_name='Depth Check',
            description='Validação de profundidade antes de sintetizar respostas',
            severity='medium',
            ecosystem_equivalent='runtime_auditor',
            action='enhance',
            rationale='O auditor já verifica criticidade mas não valida profundidade do grafo antes de sintetizar — pode gerar respostas superficiais.',
            effort='small',
            risk='low',
        ))

    # --- 10. Provenance Tracking ---
    if not any('provenance' in c.lower() for c in eco_entity_types):
        gaps.append(Gap(
            reference_id='evidence:provenance',
            reference_name='Provenance Tracking',
            description='Rastrear como cada fato foi estabelecido (deterministic/inferred/annotated)',
            severity='medium',
            ecosystem_equivalent=None,
            action='integrate',
            rationale='Memórias e knowledge graph não registram se um fato veio de análise determinística, inferência ou anotação humana.',
            effort='small',
            risk='low',
        ))

    # --- 11. Memory Consolidation com Evidence ---
    gaps.append(Gap(
        reference_id='memory:evidence_consolidation',
        reference_name='Memória com Evidence-Grounding',
        description='Memórias devem ter source anchors e confidence levels',
        severity='high',
        ecosystem_equivalent='memory_engine',
        action='enhance',
        rationale='memory_engine.py armazena title/summary/kind mas não exige source anchors — memórias ficam sem rastreabilidade.',
        effort='medium',
        risk='low',
    ))

    # --- 12. Learning com Confidence ---
    gaps.append(Gap(
        reference_id='learning:confidence_tracking',
        reference_name='Aprendizado com Confidence Tracking',
        description='Aprendizados devem registrar nível de confiança da descoberta',
        severity='medium',
        ecosystem_equivalent='learning_engine',
        action='enhance',
        rationale='learning_engine.py não diferencia descobertas confirmadas vs inferidas.',
        effort='small',
        risk='low',
    ))

    # --- 13. MCP Tool: query por confidence ---
    gaps.append(Gap(
        reference_id='mcp:query_by_confidence',
        reference_name='Query por Confidence Level',
        description='Filtrar resultados por nível de confiança mínimo',
        severity='medium',
        ecosystem_equivalent='knowledge_graph (BM25)',
        action='enhance',
        rationale='BM25 busca por relevância textual mas não filtra por confiança — pode retornar fatos speculativos como se fossem confirmados.',
        effort='small',
        risk='low',
    ))

    return gaps


# ═══════════════════════════════════════════════════════════════════
# 4. GERADOR DE PLANOS DE EVOLUÇÃO
# ═══════════════════════════════════════════════════════════════════

def generate_evolution_plans(gaps: List[Gap]) -> List[EvolutionPlan]:
    """Gera planos de implementação para cada gap detectado."""
    plans = []

    priority_counter = 1
    for gap in sorted(gaps, key=lambda g: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[g.severity]):
        steps = []
        files_create = []
        files_modify = []
        deps = []
        validations = []
        rollback = ''

        if gap.reference_id.startswith('entity_kind:'):
            kind = gap.reference_id.split(':')[1]
            steps = [
                f'Definir ontologia para entity kind "{kind}" no knowledge_graph.py',
                f'Adicionar mapeamento {kind} → tags semânticas',
                f'Testar query por kind: search knowledge_graph with kind={kind}',
            ]
            files_modify = ['scripts/knowledge_graph.py']
            deps = ['knowledge_graph.py']
            validations = [f'Query por kind={kind} retorna resultados']
            rollback = 'Reverter change em knowledge_graph.py'

        elif gap.reference_id.startswith('relationship:'):
            kind = gap.reference_id.split(':')[1]
            steps = [
                f'Adicionar tipo de relação "{kind}" ao knowledge_graph.py',
                f'Adicionar edge type {kind} na API',
                f'Testar adição de edge com kind={kind}',
            ]
            files_modify = ['scripts/knowledge_graph.py']
            deps = ['knowledge_graph.py']
            validations = [f'Edge com kind={kind} é criado e consultado']
            rollback = 'Reverter change em knowledge_graph.py'

        elif gap.reference_id == 'evidence:confidence':
            steps = [
                'Definir enum Confidence no knowledge_graph.py (proven/high/medium/low/speculative)',
                'Adicionar campo confidence nos nodes e edges',
                'Atualizar add_node/add_edge para aceitar confidence',
                'Atualizar search para filtrar por min_confidence',
                'Atualizar memory_engine.py para aceitar confidence em memórias',
            ]
            files_modify = ['scripts/knowledge_graph.py', 'scripts/memory_engine.py']
            deps = ['knowledge_graph.py', 'memory_engine.py']
            validations = [
                'Node com confidence=proven é criado',
                'Search com min_confidence=high filtra corretamente',
                'Memória com confidence=low aparece com aviso',
            ]
            rollback = 'Reverter changes em ambos arquivos'

        elif gap.reference_id == 'evidence:source_anchors':
            steps = [
                'Definir SourceAnchor (filePath, lineStart, lineEnd, snippet)',
                'Adicionar campo evidence[] nos nodes do knowledge_graph',
                'Exigir pelo menos 1 anchor por fato novo',
                'Atualizar memórias para incluir source anchors',
                'Criar função validate_evidence()',
            ]
            files_modify = ['scripts/knowledge_graph.py', 'scripts/memory_engine.py']
            files_create = ['scripts/evidence_validator.py']
            deps = ['knowledge_graph.py', 'memory_engine.py']
            validations = [
                'Fato sem anchor é rejeitado',
                'Fato com anchor válido é aceito',
                'Memória com source anchor é persistida',
            ]
            rollback = 'Reverter changes, remover evidence_validator.py'

        elif gap.reference_id == 'behavior:slices':
            steps = [
                'Criar módulo behavior_slices.py com classes Slice, SliceStep',
                'Implementar write_slice(name, steps[], evidence)',
                'Implementar query_slices(entityId, kind)',
                'Integrar com memory_engine para persistir slices',
                'Adicionar slice tracking no learning_engine',
            ]
            files_create = ['scripts/behavior_slices.py']
            files_modify = ['scripts/memory_engine.py']
            deps = ['memory_engine.py']
            validations = [
                'Slice com 3+ steps é criado',
                'Query por entityId retorna slices relevantes',
                'Slice é persistido em sessions',
            ]
            rollback = 'Remover behavior_slices.py, reverter memory_engine.py'

        elif gap.reference_id == 'ui:perspectives':
            steps = [
                'Criar módulo perspectives.py',
                'Implementar create_perspective(name, description)',
                'Implementar switch_perspective(name)',
                'Implementar list_perspectives()',
                'Integrar com knowledge_graph para filtrar entidades',
            ]
            files_create = ['scripts/perspectives.py']
            deps = ['knowledge_graph.py']
            validations = [
                'Perspective é criada',
                'Switch muda perspective ativa',
                'List retorna perspectives com contagens',
            ]
            rollback = 'Remover perspectives.py'

        elif gap.reference_id == 'persistence:snapshots':
            steps = [
                'Implementar save_snapshot(label) no runtime_state.py',
                'Implementar restore_snapshot(filename)',
                'Implementar pre-restore backup automático',
                'Implementar prune_snapshots(max_keep)',
                'Adicionar list_snapshots()',
            ]
            files_modify = ['scripts/runtime_state.py']
            deps = ['runtime_state.py']
            validations = [
                'Snapshot é salvo',
                'Restore funciona com backup prévio',
                'Snapshots antigos são removidos',
            ]
            rollback = 'Reverter runtime_state.py'

        elif gap.reference_id == 'ui:browser_realtime':
            steps = [
                'Adicionar WebSocket server ao widget EcOW',
                'Implementar broadcast() para mudanças no grafo',
                'Conectar WS ao knowledge_graph para updates em tempo real',
                'Manter compatibilidade com versão atual',
            ]
            files_modify = ['scripts/widget_grafo.py']
            deps = ['knowledge_graph.py']
            validations = [
                'WebSocket server inicia',
                'Cliente recebe updates em tempo real',
                'Widget continua funcionando sem WS',
            ]
            rollback = 'Reverter widget_grafo.py'

        elif gap.reference_id == 'quality:depth_check':
            steps = [
                'Adicionar check_depth() ao runtime_auditor.py',
                'Validar que grafo tem entidades mínimas antes de sintetizar',
                'Validar que boundaries têm sub-boundaries',
                'Reportar issues[] quando profundidade é insuficiente',
            ]
            files_modify = ['scripts/runtime_auditor.py']
            deps = ['runtime_auditor.py']
            validations = [
                'Check com grafo vazio retorna issues',
                'Check com grafo profundo retorna passed=True',
            ]
            rollback = 'Reverter runtime_auditor.py'

        elif gap.reference_id == 'evidence:provenance':
            steps = [
                'Adicionar campo provenance (deterministic/inferred/annotated) a memórias',
                'Adicionar campo reasoning quando provenance=inferred',
                'Atualizar memory_engine para aceitar provenance',
            ]
            files_modify = ['scripts/memory_engine.py']
            deps = ['memory_engine.py']
            validations = [
                'Memória com provenance=deterministic é criada',
                'Memória com provenance=inferred exige reasoning',
            ]
            rollback = 'Reverter memory_engine.py'

        elif gap.reference_id == 'memory:evidence_consolidation':
            steps = [
                'Adicionar campos source_file, source_line, source_snippet em memórias',
                'Atualizar memory_engine add() para aceitar source_anchors',
                'Atualizar context() para retornar source_anchors',
                'Criar função validate_memory_source()',
            ]
            files_modify = ['scripts/memory_engine.py']
            deps = ['memory_engine.py']
            validations = [
                'Memória com source anchor é criada',
                'Context retorna source_anchors',
                'Memória sem source mas com inferência é aceita com warning',
            ]
            rollback = 'Reverter memory_engine.py'

        elif gap.reference_id == 'learning:confidence_tracking':
            steps = [
                'Adicionar campo confidence em aprendizados',
                'Adicionar campo source_evidence[] em aprendizados',
                'Atualizar learning_engine para aceitar confidence',
            ]
            files_modify = ['scripts/learning_engine.py']
            deps = ['learning_engine.py']
            validations = [
                'Aprendizado com confidence é criado',
                'Aprendizado sem confidence assume medium por padrão',
            ]
            rollback = 'Reverter learning_engine.py'

        elif gap.reference_id == 'mcp:query_by_confidence':
            steps = [
                'Adicionar parâmetro min_confidence ao search do knowledge_graph',
                'Atualizar BM25 para suportar filtro de confiança',
                'Testar busca com min_confidence',
            ]
            files_modify = ['scripts/knowledge_graph.py']
            deps = ['knowledge_graph.py']
            validations = [
                'Search com min_confidence=high retorna só high+proven',
                'Search sem filtro retorna todos',
            ]
            rollback = 'Reverter knowledge_graph.py'

        plan = EvolutionPlan(
            gap=gap,
            implementation_steps=steps,
            files_to_create=files_create,
            files_to_modify=files_modify,
            dependencies=deps,
            validation_criteria=validations,
            rollback_plan=rollback,
            priority=priority_counter,
        )
        plans.append(plan)
        priority_counter += 1

    return plans


# ═══════════════════════════════════════════════════════════════════
# 5. AUTO-AVALIAÇÃO COMPLETA
# ═══════════════════════════════════════════════════════════════════

def full_assessment() -> Dict[str, Any]:
    """Executa auto-avaliação completa do ecossistema."""
    gaps = analyze_gaps()
    plans = generate_evolution_plans(gaps)

    severity_counts = {}
    for g in gaps:
        severity_counts[g.severity] = severity_counts.get(g.severity, 0) + 1

    effort_counts = {}
    for p in plans:
        effort_counts[p.gap.effort] = effort_counts.get(p.gap.effort, 0) + 1

    coverage = {}
    for cap_id, cap in ECOSYSTEM_CAPABILITIES.items():
        coverage[cap_id] = {
            'name': cap['name'],
            'coverage': cap.get('coverage', 'unknown'),
            'components': len(cap.get('components', [])),
        }

    return {
        'timestamp': datetime.now().isoformat(),
        'reference': 'miltonian/cartographer v0.8.0',
        'reference_capabilities': len(REFERENCE_CAPABILITIES),
        'ecosystem_capabilities': len(ECOSYSTEM_CAPABILITIES),
        'gaps_detected': len(gaps),
        'gaps_by_severity': severity_counts,
        'plans_generated': len(plans),
        'plans_by_effort': effort_counts,
        'top_priority_plans': [
            {
                'priority': p.priority,
                'name': p.gap.reference_name,
                'severity': p.gap.severity,
                'effort': p.gap.effort,
                'risk': p.gap.risk,
                'steps': len(p.implementation_steps),
                'files_modify': p.files_to_modify,
                'files_create': p.files_to_create,
            }
            for p in plans[:5]
        ],
        'coverage': coverage,
        'gaps': [asdict(g) for g in gaps],
    }


# ═══════════════════════════════════════════════════════════════════
# 6. MOTOR DE INCORPORAÇÃO
# ═══════════════════════════════════════════════════════════════════

def _persist_evolution(assessment: Dict[str, Any]):
    """Persiste resultado da auto-evolução."""
    _ensure_dirs()
    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')

    # Salvar assessment
    assess_file = os.path.join(EVOLUTION_DIR, f'assessment_{ts}.json')
    with open(assess_file, 'w', encoding='utf-8') as f:
        json.dump(assessment, f, ensure_ascii=False, indent=2)

    # Atualizar estado
    state_file = os.path.join(EVOLUTION_DIR, 'evolution_state.json')
    state = {}
    if os.path.exists(state_file):
        with open(state_file, encoding='utf-8') as f:
            state = json.load(f)

    state['last_assessment'] = ts
    state['total_assessments'] = state.get('total_assessments', 0) + 1
    state['total_gaps'] = assessment['gaps_detected']
    state['total_plans'] = assessment['plans_generated']
    state['last_severity_counts'] = assessment['gaps_by_severity']

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # Registrar memória
    try:
        from memory_engine import add_memory
        add_memory(
            title=f'Auto-evolução: {assessment["gaps_detected"]} gaps vs Cartographer',
            summary=f'Análise comparativa detectou {assessment["gaps_detected"]} gaps e gerou {assessment["plans_generated"]} planos. '
                    f'Severidades: {assessment["gaps_by_severity"]}. '
                    f'Capacidades: {assessment["reference_capabilities"]} referência vs {assessment["ecosystem_capabilities"]} ecossistema.',
            kind='decisao',
            tags=['auto-evolution', 'cartographer', 'gap-analysis', 'architecture'],
        )
    except Exception as e:
        print(f'[WARN] Não foi possível registrar memória: {e}')

    return assess_file


def run_evolution(apply_changes: bool = False) -> Dict[str, Any]:
    """Executa ciclo completo de auto-evolução."""
    assessment = full_assessment()
    assess_file = _persist_evolution(assessment)

    result = {
        'assessment_file': assess_file,
        'gaps': assessment['gaps_detected'],
        'plans': assessment['plans_generated'],
        'applied': apply_changes,
        'changes': [],
    }

    if apply_changes:
        # Implementar mudanças de baixo risco e pequeno esforço
        for plan in sorted(
            [p for p in generate_evolution_plans(analyze_gaps())
             if p.gap.risk == 'low' and p.gap.effort == 'small'],
            key=lambda p: p.priority
        ):
            change = _apply_plan(plan)
            if change:
                result['changes'].append(change)

    return result


def _apply_plan(plan: EvolutionPlan) -> Optional[Dict[str, Any]]:
    """Aplica um plano de evolução de baixo risco."""
    if plan.gap.risk != 'low' or plan.gap.effort != 'small':
        return None

    change = {
        'gap': plan.gap.reference_id,
        'name': plan.gap.reference_name,
        'status': 'dry_run',
        'files': [],
    }

    # Para gaps de entity_kind ou relationship, apenas documentar
    if plan.gap.reference_id.startswith(('entity_kind:', 'relationship:')):
        change['status'] = 'documented'
        change['note'] = 'Gap documentado para implementação futura'
        return change

    # Para confidence/provenance, adicionar ao knowledge_graph
    if plan.gap.reference_id in ('evidence:provenance', 'learning:confidence_tracking'):
        change['status'] = 'deferred'
        change['note'] = 'Requer alteração de schema — documentado para implementação futura'
        return change

    return change


# ═══════════════════════════════════════════════════════════════════
# 7. CLI
# ═══════════════════════════════════════════════════════════════════

def _print_assessment(assessment: Dict[str, Any]):
    """Imprime assessment formatado."""
    print(f'\n{"="*70}')
    print(f'  AUTO-AVALIAÇÃO — {assessment["reference"]}')
    print(f'  {assessment["timestamp"]}')
    print(f'{"="*70}\n')

    print(f'Capacidades da referência: {assessment["reference_capabilities"]}')
    print(f'Capacidades do ecossistema: {assessment["ecosystem_capabilities"]}')
    print(f'Gaps detectados: {assessment["gaps_detected"]}')
    print(f'Planos gerados: {assessment["plans_generated"]}')

    print(f'\n--- Gaps por Severidade ---')
    for sev, count in sorted(assessment['gaps_by_severity'].items()):
        icon = {'critical': '!!!', 'high': '!!', 'medium': '!', 'low': '.'}.get(sev, '?')
        print(f'  [{icon}] {sev}: {count}')

    print(f'\n--- Top 5 Planos Prioritários ---')
    for p in assessment['top_priority_plans']:
        print(f'  #{p["priority"]} [{p["severity"].upper()}] {p["name"]}')
        print(f'     Esforço: {p["effort"]} | Risco: {p["risk"]} | Steps: {p["steps"]}')
        if p['files_modify']:
            print(f'     Modificar: {", ".join(p["files_modify"])}')
        if p['files_create']:
            print(f'     Criar: {", ".join(p["files_create"])}')

    print(f'\n--- Cobertura por Capacidade ---')
    for cap_id, cap in assessment['coverage'].items():
        print(f'  [{cap["coverage"].upper():8s}] {cap["name"]} ({cap["components"]} componentes)')

    print()


def _print_gaps(gaps: List[Gap]):
    """Imprime gaps formatados."""
    print(f'\n{"="*70}')
    print(f'  GAPS DETECTADOS — Cartographer vs EcoSystemUmGrau')
    print(f'{"="*70}\n')

    for i, gap in enumerate(gaps, 1):
        icon = {'critical': '!!!', 'high': '!!', 'medium': '!', 'low': '.'}[gap.severity]
        print(f'{i:2d}. [{icon}] {gap.reference_name}')
        print(f'     {gap.description}')
        print(f'     Severidade: {gap.severity} | Esforço: {gap.effort} | Risco: {gap.risk}')
        if gap.ecosystem_equivalent:
            print(f'     Equivalente: {gap.ecosystem_equivalent}')
        print(f'     Ação: {gap.action}')
        print()

    print(f'Total: {len(gaps)} gaps\n')


def _print_plans(plans: List[EvolutionPlan]):
    """Imprime planos formatados."""
    print(f'\n{"="*70}')
    print(f'  PLANOS DE EVOLUÇÃO')
    print(f'{"="*70}\n')

    for plan in plans:
        print(f'#{plan.priority} [{plan.gap.severity.upper()}] {plan.gap.reference_name}')
        print(f'  Ação: {plan.gap.action} | Esforço: {plan.gap.effort} | Risco: {plan.gap.risk}')
        print(f'  Passos:')
        for j, step in enumerate(plan.implementation_steps, 1):
            print(f'    {j}. {step}')
        if plan.files_to_create:
            print(f'  Criar: {", ".join(plan.files_to_create)}')
        if plan.files_to_modify:
            print(f'  Modificar: {", ".join(plan.files_to_modify)}')
        print(f'  Validação:')
        for v in plan.validation_criteria:
            print(f'    - {v}')
        print(f'  Rollback: {plan.rollback_plan}')
        print()

    print(f'Total: {len(plans)} planos\n')


def _print_status():
    """Imprime status da auto-evolução."""
    state_file = os.path.join(EVOLUTION_DIR, 'evolution_state.json')
    if not os.path.exists(state_file):
        print('Nenhuma auto-evolução registrada ainda.')
        print('Execute: python scripts/auto_evolution.py scan')
        return

    with open(state_file, encoding='utf-8') as f:
        state = json.load(f)

    print(f'\n{"="*70}')
    print(f'  STATUS DA AUTO-EVOLUÇÃO')
    print(f'{"="*70}\n')
    print(f'Último assessment: {state.get("last_assessment", "nunca")}')
    print(f'Total de assessments: {state.get("total_assessments", 0)}')
    print(f'Total de gaps: {state.get("total_gaps", 0)}')
    print(f'Total de planos: {state.get("total_plans", 0)}')
    if state.get('last_severity_counts'):
        print(f'Última distribuição: {state["last_severity_counts"]}')
    print()

    # Listar assessments anteriores
    if os.path.exists(EVOLUTION_DIR):
        assessments = sorted([
            f for f in os.listdir(EVOLUTION_DIR) if f.startswith('assessment_')
        ], reverse=True)
        if assessments:
            print(f'Assessments recentes:')
            for a in assessments[:5]:
                print(f'  - {a}')
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'scan':
        assessment = full_assessment()
        _persist_evolution(assessment)
        _print_assessment(assessment)

    elif cmd == 'gaps':
        gaps = analyze_gaps()
        _print_gaps(gaps)

    elif cmd == 'plan':
        gaps = analyze_gaps()
        plans = generate_evolution_plans(gaps)
        _print_plans(plans)

    elif cmd == 'assess':
        assessment = full_assessment()
        assess_file = _persist_evolution(assessment)
        _print_assessment(assessment)
        print(f'Salvo em: {assess_file}')

    elif cmd == 'evolve':
        apply = '--apply' in sys.argv
        result = run_evolution(apply_changes=apply)
        print(f'\nResultado da evolução:')
        print(f'  Assessment: {result["assessment_file"]}')
        print(f'  Gaps: {result["gaps"]}')
        print(f'  Planos: {result["plans"]}')
        print(f'  Aplicado: {result["applied"]}')
        if result['changes']:
            print(f'  Mudanças aplicadas: {len(result["changes"])}')
            for c in result['changes']:
                print(f'    - {c["name"]}: {c["status"]}')

    elif cmd == 'status':
        _print_status()

    else:
        print(f'Comando desconhecido: {cmd}')
        print(__doc__)


if __name__ == '__main__':
    main()
