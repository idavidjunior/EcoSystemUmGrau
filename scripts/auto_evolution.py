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
    python scripts/auto_evolution.py evolve              # Dry-run do ciclo fechado (padrão, seguro)
    python scripts/auto_evolution.py evolve --apply      # Executa evoluções via subagente
    python scripts/auto_evolution.py evolve --apply --max-plans 1   # Limita a 1 plano
    python scripts/auto_evolution.py evolve --apply --force         # Permite risco alto
    python scripts/auto_evolution.py evolve --apply --no-preflight  # Audita sem preflight
    python scripts/auto_evolution.py status              # Status da auto-evolução
    python scripts/auto_evolution.py health              # Diagnóstico da saúde do ecossistema
    python scripts/auto_evolution.py radar               # Busca externa de gaps (evolution radar)

Ciclo fechado: detecta → prioriza → avalia risco → gate de veto (kernel) →
checkpoint → delega → detecta mudanças → valida escopo → preflight técnico/ético →
testes → persiste via gate → aprende. Em falha: rollback de código + estado,
memória de erro preservada. O motor nunca altera o sistema diretamente.
"""

import os
import sys
import json
import re
import shutil
import hashlib
import subprocess
import time
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
CYCLE_DIR = os.path.join(EVOLUTION_DIR, 'cycle')
LOCK_FILE = os.path.join(EVOLUTION_DIR, '.evolve.lock')

sys.path.insert(0, SCRIPTS)

def _ensure_dirs():
    for d in [RUNTIME, LEARNING_DIR, EVOLUTION_DIR, CYCLE_DIR]:
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
        'description': 'Memória episódica com decay de Ebbinghaus, tipos: decisao/erro/padrao/episodio/contexto/preferencia. JÁ TEM: confidence (float 0-1), source_type (provenance), source_anchors (evidence grounding)',
        'components': ['ebbinghaus_decay', 'semantic_tags', 'session_tracking', 'query_by_tag', 'confidence', 'provenance', 'source_anchors'],
        'pattern': 'add(task, summary, kind, confidence, source_type, source_anchors) → query(termo) → context(project)',
        'coverage': 'high',
    },
    'knowledge_graph': {
        'name': 'Knowledge Graph (knowledge_graph.py)',
        'description': 'Grafo de conhecimento com BM25 semântico para busca. JÁ TEM: confidence (float). FALTA: provenance enum, source_anchors por node/edge.',
        'components': ['bm25_search', 'tfidf_index', 'nodes', 'edges', 'confidence_float'],
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
        'description': 'Estado persistente entre sessões: projeto ativo, objetivo, última tarefa, pendências. JÁ TEM: checkpoint, restore, list, pre-restore backup.',
        'components': ['state_persistence', 'checkpoint', 'restore', 'last_task', 'pre_restore_backup'],
        'pattern': 'set(key, value) → get(key) → checkpoint(label) → restore(cid)',
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
    'behavior_slices': {
        'name': 'Behavior Slices (behavior_slices.py)',
        'description': 'Rastreio de fluxos de comportamento (flows) e changesets, com evidence-grounding (anchors, confidence, provenance). Inspirado no Cartographer.',
        'components': ['flow_narratives', 'changeset_tracking', 'step_ordering', 'source_anchors', 'confidence_levels', 'provenance_tracking'],
        'pattern': 'write_slice(name, kind, steps[], evidence) → query_slices(entity) → get_slice(id)',
        'coverage': 'high',
    },
    'evidence_grounding': {
        'name': 'Evidence-Grounding (memory_engine + behavior_slices)',
        'description': 'Fatos com source anchors (file:line + snippet), confidence e provenance. Presente em memory_engine (source_anchors) e behavior_slices.',
        'components': ['source_anchors', 'confidence_levels', 'provenance_tracking'],
        'pattern': 'fact → anchors[] → confidence → provenance → reasoning',
        'coverage': 'high',
    },
    'snapshots': {
        'name': 'Snapshots & Restore (runtime_state.py)',
        'description': 'Checkpoints com backup pré-restore atômico (os.replace) e cleanup automático.',
        'components': ['atomic_write', 'prune_old', 'pre_restore_backup'],
        'pattern': 'checkpoint(label) → restore(cid) → pre-restore backup',
        'coverage': 'high',
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
    sources: List[Dict[str, Any]] = field(default_factory=list)  # fontes relevantes do source_registry

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


def _enrich_gaps_with_sources(gaps: List[Gap]) -> List[Gap]:
    """Enriquece cada gap com fontes relevantes do source_registry.

    Para cada gap, mapeia a categoria para domínios do catálogo e busca
    fontes de alta autoridade nesses domínios. A busca é guiada por
    mapeamento semântico (não apenas matching textual), pois os gaps são
    sobre conceitos de arquitetura de software, não sobre linguagens específicas.
    """
    try:
        from source_registry import SourceRegistry
        reg = SourceRegistry()
    except Exception:
        return gaps  # fail-soft: sem registry, gaps ficam sem fontes

    # Mapeamento de categorias de gap → domínios relevantes no catálogo
    GAP_DOMAIN_MAP = {
        'entity_kind': ['architecture', 'general'],
        'relationship': ['architecture', 'database'],
        'confidence': ['architecture', 'general'],
        'evidence': ['architecture', 'security'],
        'behavior': ['architecture', 'general'],
        'perspective': ['architecture', 'frontend'],
        'query': ['architecture', 'database'],
        'search': ['architecture', 'database'],
        'knowledge': ['architecture', 'ml'],
        'memory': ['architecture', 'python'],
        'monitor': ['devops', 'architecture'],
        'alert': ['devops', 'architecture'],
        'test': ['python', 'architecture'],
        'security': ['security', 'architecture'],
        'api': ['api', 'architecture'],
        'data': ['database', 'architecture'],
        'graph': ['architecture', 'ml'],
        'source': ['architecture', 'general'],
        'anchor': ['architecture', 'general'],
    }

    for gap in gaps:
        # Determinar categorias do gap
        ref_key = gap.reference_id.split(':')[0] if ':' in gap.reference_id else gap.reference_id

        # Buscar domínios relevantes
        domains = GAP_DOMAIN_MAP.get(ref_key, ['architecture', 'general'])

        # Buscar fontes de alta autoridade nos domínios relevantes.
        # Preferir domínio 'architecture' como principal se presente; 'general'
        # só é usado como fallback para evitar fontes genéricas (Git, Vim).
        primary_domains = [d for d in domains if d != 'general']
        if not primary_domains:
            primary_domains = domains

        relevant = []
        for domain in primary_domains:
            domain_sources = reg.get_top_authority(domain=domain, limit=3)
            relevant.extend(domain_sources)

        # Deduplicar e ordenar por reliability
        seen = set()
        unique = []
        for s in relevant:
            sid = s.get('id', '')
            if sid not in seen:
                seen.add(sid)
                unique.append(s)
        unique.sort(key=lambda s: -s.get('reliability', 0))

        gap.sources = [
            {
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'url': s.get('url', ''),
                'authority_level': s.get('authority_level', ''),
                'reliability': s.get('reliability', 0),
            }
            for s in unique[:3]  # máx 3 por gap
        ]

    return gaps


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
    has_slices = any(s in eco_entity_types for s in ('flow_narratives', 'step_ordering', 'changeset_tracking'))
    if not has_slices:
        gaps.append(Gap(
            reference_id='behavior:slices',
            reference_name='Behavior Slices',
            description='Fluxos de comportamento ordenados (orderados) e changesets de PR',
            severity='high',
            ecosystem_equivalent='behavior_slices.py',
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
    has_snapshots = any(s in eco_entity_types for s in ('pre_restore_backup', 'atomic_write', 'checkpoint'))
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

    # Enriquecer cada gap com fontes relevantes do catálogo
    gaps = _enrich_gaps_with_sources(gaps)

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
            task=f'Auto-evolução: {assessment["gaps_detected"]} gaps vs Cartographer',
            summary=f'Análise comparativa detectou {assessment["gaps_detected"]} gaps e gerou {assessment["plans_generated"]} planos. '
                    f'Severidades: {assessment["gaps_by_severity"]}. '
                    f'Capacidades: {assessment["reference_capabilities"]} referência vs {assessment["ecosystem_capabilities"]} ecossistema.',
            kind='decisao',
            tags=['auto-evolution', 'cartographer', 'gap-analysis', 'architecture'],
            confidence=0.9,
            source_type='inferido',
            source_anchors=[{
                'filePath': 'scripts/auto_evolution.py',
                'lineStart': 1,
                'lineEnd': 40,
                'snippet': 'Auto-Evolution Engine — Motor de Auto-Aprendizado e Evolução do Ecossistema',
            }],
        )
    except Exception as e:
        print(f'[WARN] Não foi possível registrar memória: {e}')

    return assess_file


# ═══════════════════════════════════════════════════════════════════
# 6. MOTOR DE INCORPORAÇÃO — CICLO FECHADO
# ═══════════════════════════════════════════════════════════════════
# O motor nunca altera o sistema diretamente. Ele orquestra, supervisiona,
# valida e aprende. A alteração é sempre delegada a um executor externo.
# Princípio: «O sistema pode mudar a si mesmo, mas nunca sem saber o que
# pretende mudar, sem proteger o estado anterior, sem validar o resultado e
# sem aprender com as consequências.»

# Estados da máquina de estados (enxuta, funcional).
STATE_DISCOVERED = 'discovered'
STATE_CHECKPOINTED = 'checkpointed'
STATE_DELEGATED = 'delegated'
STATE_EXECUTING = 'executing'
STATE_SCOPE_OK = 'scope_ok'
STATE_PREFLIGHT_TECH = 'preflight_technical'
STATE_PREFLIGHT_ETH = 'preflight_ethical'
STATE_TESTING = 'testing'
STATE_PERSISTING = 'persisting'
STATE_COMPLETED = 'completed'
STATE_NO_CHANGE = 'no_change'
STATE_BLOCKED_VETO = 'blocked_veto'
STATE_BLOCKED_RISK = 'blocked_risk'
STATE_BLOCKED_EXTERNAL = 'blocked_external'
STATE_TIMEOUT = 'timeout'
STATE_VALIDATION_FAILED = 'validation_failed'
STATE_ROLLED_BACK = 'rolled_back'
STATE_ROLLBACK_FAILED = 'rollback_failed'
STATE_SKIPPED = 'skipped'

# Paths que nunca podem ser alterados por evolução (segurança).
FORBIDDEN_PATHS = ['.env', 'credentials', 'runtime/secrets', 'config/opencode.jsonc', '.git/']


def _process_alive(pid: int) -> bool:
    """Verifica se um processo existe no Windows (tolerante a encoding OEM)."""
    if not pid or pid <= 0:
        return False
    try:
        r = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
            capture_output=True, timeout=10,
        )
        out = r.stdout.decode('utf-8', errors='replace')
        if not out.strip():
            return False
        # A saída de processo vivo contém o PID; a de "não encontrado" não.
        return str(pid) in out
    except Exception:
        return True  # dúvida: mantém lock (conservador, evita execução concorrente)


class EvolutionLock:
    """Lock por repositório para impedir execução concorrente."""

    def __init__(self, lock_path: str = LOCK_FILE):
        self.lock_path = lock_path

    def acquire(self, execution_id: str) -> bool:
        _ensure_dirs()
        if os.path.exists(self.lock_path):
            # Trata lock órfão: se o PID que o criou não está mais vivo, libera.
            try:
                with open(self.lock_path, encoding='utf-8-sig') as f:
                    data = json.load(f)
                pid = data.get('pid')
                if pid and not _process_alive(pid):
                    print(f'[EVOLVE] Lock órfão removido (PID {pid} não está mais ativo).')
                    os.remove(self.lock_path)
                else:
                    return False
            except Exception:
                return False
        payload = {
            'execution_id': execution_id,
            'pid': os.getpid(),
            'created_at': datetime.now().isoformat(),
        }
        with open(self.lock_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        return True

    def release(self):
        try:
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
        except OSError:
            pass

    def is_locked(self) -> bool:
        return os.path.exists(self.lock_path)

    def status(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.lock_path):
            return None
        with open(self.lock_path, encoding='utf-8') as f:
            return json.load(f)


def _git_status() -> List[str]:
    """Retorna lista de arquivos modificados/novos no git (read-only)."""
    try:
        r = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, cwd=BASE, timeout=15,
        )
        if r.returncode != 0:
            return []
        return [line.strip() for line in r.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def _snapshot_files(paths: List[str], snapshot_dir: str) -> List[Dict[str, Any]]:
    """Cria snapshot (cópia) dos arquivos que serão alterados, para rollback."""
    snapshots = []
    for rel_path in paths:
        src = os.path.join(BASE, rel_path)
        if not os.path.exists(src):
            continue
        try:
            dest = os.path.join(snapshot_dir, rel_path.replace('/', '__'))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            snapshots.append({'rel': rel_path, 'snapshot': os.path.relpath(dest, BASE)})
        except Exception as e:
            print(f'[EVOLVE] Aviso: não foi possível snapshot de {rel_path}: {e}')
    return snapshots


def _restore_snapshots(snapshots: List[Dict[str, Any]]):
    """Restaura arquivos a partir de um snapshot."""
    for snap in snapshots:
        rel = snap['rel']
        snap_path = os.path.join(BASE, snap['snapshot'])
        dest = os.path.join(BASE, rel)
        try:
            if os.path.exists(snap_path):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(snap_path, dest)
        except Exception as e:
            print(f'[EVOLVE] Erro no rollback de {rel}: {e}')


def _detect_changes(before: List[str], after: List[str]) -> Tuple[str, List[str]]:
    """Compara estado git antes/depois para detectar mudanças reais."""
    new_changes = [c for c in after if c not in before]
    if new_changes:
        return 'mudanca_detectada', new_changes
    return 'sem_mudanca', []


def _validate_scope(changes: List[str], allowed_paths: List[str]) -> Tuple[bool, List[str]]:
    """Valida se as mudanças estão dentro do escopo permitido."""
    violations = []
    for change in changes:
        rel = change[3:].strip() if len(change) > 3 else change  # remove " M " prefix
        rel = re.sub(r'^[A-Z? ]+\s+', '', change)
        for forbidden in FORBIDDEN_PATHS:
            if rel.startswith(forbidden):
                violations.append(rel)
        if allowed_paths:
            in_scope = any(rel.startswith(p) for p in allowed_paths)
            if not in_scope:
                violations.append(rel)
    return (len(violations) == 0, violations)


def _run_executor(command: str, timeout_seconds: int) -> Dict[str, Any]:
    """Executa um subagente externo com timeout e captura de saída."""
    started = datetime.now().isoformat()
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=BASE, timeout=timeout_seconds,
        )
        status = 'success' if r.returncode == 0 else 'failed'
        return {
            'executor': 'opencode',
            'command': command,
            'started_at': started,
            'finished_at': datetime.now().isoformat(),
            'timeout_seconds': timeout_seconds,
            'exit_code': r.returncode,
            'execution_status': status,
            'output': (r.stdout or '')[-2000:],
            'error': (r.stderr or '')[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {
            'executor': 'opencode',
            'command': command,
            'started_at': started,
            'finished_at': datetime.now().isoformat(),
            'timeout_seconds': timeout_seconds,
            'exit_code': -1,
            'execution_status': 'timeout',
            'output': '',
            'error': 'timeout',
        }
    except Exception as e:
        return {
            'executor': 'opencode',
            'command': command,
            'started_at': started,
            'finished_at': datetime.now().isoformat(),
            'timeout_seconds': timeout_seconds,
            'exit_code': -1,
            'execution_status': 'failed',
            'output': '',
            'error': str(e),
        }


def _run_preflight(preflight_script: str) -> Dict[str, Any]:
    """Executa um script de preflight e retorna resultado."""
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, preflight_script)],
            capture_output=True, text=True, cwd=BASE, timeout=120,
        )
        return {
            'script': preflight_script,
            'exit_code': r.returncode,
            'passed': r.returncode == 0,
            'output': (r.stdout or '')[-2000:],
            'error': (r.stderr or '')[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {'script': preflight_script, 'exit_code': -1, 'passed': False,
                'output': '', 'error': 'timeout'}
    except Exception as e:
        return {'script': preflight_script, 'exit_code': -1, 'passed': False,
                'output': '', 'error': str(e)}


def _run_tests() -> Dict[str, Any]:
    """Executa testes do projeto (best-effort)."""
    test_cmds = [
        [sys.executable, os.path.join(SCRIPTS, 'valida_specs.py'), '--json'],
    ]
    for cmd in test_cmds:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE, timeout=120)
            return {'command': cmd, 'exit_code': r.returncode,
                    'passed': r.returncode == 0, 'output': (r.stdout or '')[-1500:]}
        except Exception as e:
            return {'command': cmd, 'exit_code': -1, 'passed': False, 'output': str(e)}
    return {'command': None, 'exit_code': 0, 'passed': True, 'output': ''}


def _persist_via_gate() -> Dict[str, Any]:
    """Persiste mudanças via gate oficial (persistencia.ps1). Nunca git direto."""
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             r'& "scripts/persistencia.ps1" run-sync'],
            capture_output=True, text=True, cwd=BASE, timeout=180,
        )
        return {'exit_code': r.returncode, 'passed': r.returncode == 0,
                'output': (r.stdout or '')[-1500:], 'error': (r.stderr or '')[-1500:]}
    except Exception as e:
        return {'exit_code': -1, 'passed': False, 'output': '', 'error': str(e)}


def _register_memory(kind: str, task: str, summary: str, metadata: Dict[str, Any] = None,
                     source_anchors: List[Dict[str, Any]] = None):
    """Registra memória de decisão ou erro (best-effort, nunca bloqueia)."""
    try:
        from memory_engine import add_memory
        add_memory(
            task=task, summary=summary, kind=kind,
            tags=['auto-evolution', 'ciclo-fechado'],
            confidence=0.9 if kind == 'decisao' else 0.7,
            source_type='inferido',
            source_anchors=source_anchors or [],
            metadata=metadata or {},
            reindex=False,
        )
    except Exception as e:
        print(f'[EVOLVE] Aviso: memória não registrada: {e}')


def _plan_fingerprint(plan: EvolutionPlan) -> str:
    """Hash determinístico do plano para idempotência."""
    gap_sig = f"{plan.gap.reference_id}:{plan.gap.reference_name}:{plan.gap.severity}"
    files_sig = ','.join(sorted(plan.files_to_create + plan.files_to_modify))
    steps_sig = ';'.join(plan.implementation_steps[:3])
    return hashlib.sha256(f"{gap_sig}|{files_sig}|{steps_sig}".encode()).hexdigest()[:16]


def _is_applied(fingerprint: str) -> bool:
    """Verifica se um plano (por fingerprint) já foi aplicado."""
    state_file = os.path.join(EVOLUTION_DIR, 'evolution_state.json')
    if not os.path.exists(state_file):
        return False
    with open(state_file, encoding='utf-8') as f:
        state = json.load(f)
    applied = state.get('applied_plans', [])
    return any(a.get('fingerprint') == fingerprint and a.get('final_status') == 'completed'
               for a in applied)


def _record_applied(fingerprint: str, record: Dict[str, Any]):
    """Registra um plano aplicado para idempotência."""
    state_file = os.path.join(EVOLUTION_DIR, 'evolution_state.json')
    state = {}
    if os.path.exists(state_file):
        with open(state_file, encoding='utf-8') as f:
            state = json.load(f)
    applied = state.setdefault('applied_plans', [])
    # Remove anterior com mesmo fingerprint para não duplicar
    applied = [a for a in applied if a.get('fingerprint') != fingerprint]
    applied.append({'fingerprint': fingerprint, **record})
    state['applied_plans'] = applied[-50:]
    _ensure_dirs()
    tmp = state_file + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, state_file)


def _save_cycle_record(record: Dict[str, Any]):
    """Salva registro de execução do ciclo."""
    _ensure_dirs()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = os.path.join(CYCLE_DIR, f'cycle_{ts}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return fname


def _kernel_gate_veto(goal: str) -> Dict[str, Any]:
    """Consulta o gate de veto do Kernel (Fase 2) antes de aplicar um plano.

    Integra o auto-evolution ao kernel de governança: o mesmo gate usado
    no roteamento de tarefas (`runtime_kernel.Kernel.gate_veto`) é consultado
    aqui para que a evolução respeite as regras de veto (commit direto,
    destruição, segredos, etc.). Fail-soft: se o kernel estiver indisponível,
    o plano segue sem bloqueio (evolução não trava por dependência externa).

    Returns:
        dict: {'aprovado': bool, 'status': str, 'vetos': list,
               'objetivo': str, 'gate': bool, 'motivo': str}
    """
    try:
        from runtime_kernel import Kernel
        kernel = Kernel()
        return kernel.gate_veto(goal)
    except Exception as e:
        return {'aprovado': True, 'status': 'APROVADO', 'vetos': [],
                'objetivo': goal, 'gate': False,
                'motivo': f'kernel indisponível ({e}) — fail-soft aprovado'}


def _maestro_consulta(script: str, acao: str = 'confirmar') -> Dict[str, Any]:
    """Consulta o Maestro de Runtime antes de acionar/delegar uma evolução.

    Cláusula pétrea do Maestro: todo serviço Eco consulta o Maestro antes de
    iniciar/parar processos críticos. O auto-evolution consulta por segurança
    (comando 'registrar') antes de delegar cada plano. Fail-soft: se o Maestro
    estiver offline ou não responder, a evolução segue (modo degraded),
    nunca travando por dependência externa.

    Returns:
        dict: resposta do maestro, ou {'status':'offline', ...} em fail-soft.
    """
    try:
        from maestro_client import consultar_maestro
        return consultar_maestro(acao, script=script, owner='auto-evolution')
    except Exception as e:
        return {'status': 'offline', 'motivo': f'maestro_client indisponível ({e})'}


def _save_cycle_learning_report(records: List[Dict[str, Any]], execution_id: str = None) -> Optional[str]:
    """Gera relatório consolidado do ciclo de evolução em conhecimento/aprendizados/.

    Ao final de cada ciclo apply, consolida todos os planos processados
    (concluídos, bloqueados, rollback, etc.) em um único Markdown datado,
    para que a evolução fique rastreável e indexável no acervo de
    conhecimento — não apenas em JSON interno (runtime/learning/evolution).
    Retorna o caminho do arquivo ou None.
    """
    if not records:
        return None
    try:
        from datetime import date
        ts = datetime.now()
        fname = os.path.join(KNOWLEDGE, 'aprendizados',
                             f"{ts.strftime('%Y-%m-%d')}-auto-evolucao.md")
        total = len(records)
        done = sum(1 for r in records if r.get('final_status') == 'completed')
        lines = [
            '---',
            'tipo: episodio',
            'tags: [auto-evolution, ciclo-fechado, evolucao]',
            f'data: {ts.strftime("%Y-%m-%d")}',
            f'hora: {ts.strftime("%H:%M")}',
            'contexto: Ciclo de auto-evolucao do Ecossistema (auto_evolution.py).',
            'impacto: Evidencia do ciclo de evolucao e suas decisoes.',
            '---',
            '',
            f'# Ciclo de Auto-Evolução — {ts.strftime("%Y-%m-%d %H:%M")}',
            '',
            f'Execution ID: {execution_id or "n/a"}',
            f'Planos processados: {total} | Concluídos: {done}',
            '',
        ]
        for rec in records:
            status = rec.get('final_status', '?')
            name = rec.get('name', '?')
            gap = rec.get('gap_id', '?')
            lines.append(f'- [{status.upper()}] {name} (gap {gap})')
            if rec.get('note'):
                lines.append(f'  - Nota: {rec["note"]}')
            if rec.get('kernel_gate', {}).get('status'):
                lines.append(f'  - Kernel gate: {rec["kernel_gate"]["status"]}')
        lines.append('')
        content = '\n'.join(lines)
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        tmp = fname + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp, fname)
        return fname
    except Exception as e:
        print(f'[EVOLVE] Aviso: relatório de aprendizado não gerado: {e}')
        return None


def _print_cycle_report(records: List[Dict[str, Any]]):
    """Imprime relatório do ciclo de evolução."""
    print(f'\n{"="*60}')
    print('  AUTO-EVOLUTION CYCLE')
    print(f'{"="*60}\n')
    for rec in records:
        gap = rec.get('gap_id', '?')
        name = rec.get('name', '?')
        status = rec.get('final_status', '?')
        print(f'  Plano: {gap} — {name}')
        print(f'    Risco: {rec.get("risk", "?")} | Executor: {rec.get("executor", "?")}')
        print(f'    Checkpoint: {rec.get("checkpoint", "?")} | Estado: {rec.get("final_state", "?")}')
        print(f'    STATUS FINAL: {status.upper()}')
        print()
    total_completed = sum(1 for r in records if r['final_status'] == 'completed')
    print(f'  Resumo: {len(records)} plano(s), {total_completed} concluído(s)')
    print()


def run_evolution(apply_changes: bool = False, max_plans: int = 0,
                  force: bool = False, no_preflight: bool = False) -> Dict[str, Any]:
    """Executa o ciclo fechado de auto-evolução.

    apply_changes: se True, executa de verdade (delega a subagente). Se False, dry-run.
    max_plans: limite de planos. No dry-run, 0 = mostra todos. No apply, 0 = não executa
        nenhum (seguro por padrão — exige --max-plans N para aplicar).
    force: permite planos de risco alto.
    no_preflight: ignora preflights (apenas auditoria manual controlada).
    """
    _ensure_dirs()
    assessment = full_assessment()
    assess_file = _persist_evolution(assessment)
    gaps = analyze_gaps()
    plans = generate_evolution_plans(gaps)

    records = []
    applied_count = 0

    if not apply_changes:
        # Dry-run: mostra o que seria feito, sem alterar nada.
        limit = max_plans if max_plans > 0 else len(plans)
        for plan in plans[:limit]:
            records.append({
                'gap_id': plan.gap.reference_id,
                'name': plan.gap.reference_name,
                'risk': plan.gap.risk,
                'executor': 'opencode' if plan.gap.effort != 'large' else 'ler',
                'checkpoint': 'simulado',
                'final_state': STATE_DISCOVERED,
                'final_status': 'dry_run',
            })
        _print_cycle_report(records)
        return {
            'assessment_file': assess_file,
            'gaps': assessment['gaps_detected'],
            'plans': assessment['plans_generated'],
            'applied': False,
            'changes': records,
            'mode': 'dry-run',
        }

    # ── Modo APPLY: ciclo fechado governado ──
    # Lock de concorrência
    execution_id = f"evo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    lock = EvolutionLock()
    if not lock.acquire(execution_id):
        return {'status': 'evolucao_bloqueada_por_lock',
                'assessment_file': assess_file, 'applied': False,
                'changes': [], 'lock': lock.status()}
    try:
        before = _git_status()
        count = 0
        for plan in plans:
            if count >= max_plans:
                break
            record = _execute_plan(plan, before, force=force, no_preflight=no_preflight,
                                   execution_id=execution_id)
            records.append(record)
            if record['final_status'] == 'completed':
                count += 1
            # Se rollback falhou, interrompe o ciclo (estado potencialmente inconsistente)
            if record['final_status'] == 'rollback_failed':
                break
    finally:
        lock.release()

    _print_cycle_report(records)
    report_file = _save_cycle_learning_report(records, execution_id)
    done = sum(1 for r in records if r.get('final_status') == 'completed')
    if records:
        _register_memory(
            'episodio', f'Ciclo de auto-evolução: {done}/{len(records)} concluídos',
            f'{len(records)} planos processados, {done} concluídos, relatório em {report_file}.',
            {'execution_id': execution_id, 'concluidos': done, 'total': len(records)},
        )
    return {
        'assessment_file': assess_file,
        'gaps': assessment['gaps_detected'],
        'plans': assessment['plans_generated'],
        'applied': True,
        'changes': records,
        'mode': 'apply',
        'execution_id': execution_id,
        'learning_report': report_file,
    }


def _execute_plan(plan: EvolutionPlan, git_before: List[str],
                  force: bool, no_preflight: bool, execution_id: str) -> Dict[str, Any]:
    """Executa um plano individual com checkpoint, validação e rollback."""
    _ensure_dirs()
    plan_snapshot_dir = os.path.join(CYCLE_DIR, f'plan_{datetime.now().strftime("%H%M%S%f")}')
    os.makedirs(plan_snapshot_dir, exist_ok=True)

    record = {
        'plan_id': execution_id,
        'gap_id': plan.gap.reference_id,
        'name': plan.gap.reference_name,
        'risk': plan.gap.risk,
        'effort': plan.gap.effort,
        'checkpoint': 'ok',
        'executor': 'opencode' if plan.gap.effort != 'large' else 'ler',
        'final_state': STATE_DISCOVERED,
        'final_status': 'pending',
    }

    # 1. Gaps de documentação (entity_kind/relationship) não exigem execução real.
    if plan.gap.reference_id.startswith(('entity_kind:', 'relationship:')):
        record['final_state'] = STATE_SKIPPED
        record['final_status'] = 'skipped'
        record['note'] = 'Gap de ontologia — documentado para implementação futura'
        return record

    # 2. Idempotência: plano já aplicado?
    fp = _plan_fingerprint(plan)
    if _is_applied(fp):
        record['final_state'] = STATE_SKIPPED
        record['final_status'] = 'pulado_por_idempotencia'
        record['note'] = 'Plano já aplicado anteriormente (mesmo fingerprint)'
        return record

    # 3. Avaliação de risco
    if plan.gap.risk == 'high' and not force:
        record['final_state'] = STATE_BLOCKED_RISK
        record['final_status'] = 'bloqueado_por_risco'
        record['note'] = 'Risco alto requer --force'
        return record

    # 3b. Gate de veto do Kernel (Fase 2) — respeita regras de governança
    gate = _kernel_gate_veto(plan.gap.reference_name)
    record['kernel_gate'] = gate
    if not gate['aprovado']:
        record['final_state'] = STATE_BLOCKED_VETO
        record['final_status'] = 'bloqueado_por_veto'
        record['note'] = gate['motivo']
        _register_memory('erro', f'Evolução vetada pelo kernel: {plan.gap.reference_name}',
                         gate['motivo'], {'gap': plan.gap.reference_id})
        return record

    # 4. Verificar executor disponível
    executor_available = shutil.which('opencode') is not None or shutil.which('ler') is not None
    if not executor_available:
        record['final_state'] = STATE_BLOCKED_EXTERNAL
        record['final_status'] = 'bloqueado_externo'
        record['note'] = 'Nenhum executor (opencode/ler) disponível'
        return record

    # 4b. Consulta ao Maestro de Runtime (cláusula pétrea) — fail-soft
    maestro = _maestro_consulta(script=plan.gap.reference_id)
    record['maestro'] = maestro
    if maestro.get('status') == 'blocked':
        record['final_state'] = STATE_BLOCKED_RISK
        record['final_status'] = 'bloqueado_por_maestro'
        record['note'] = maestro.get('motivo', 'Maestro bloqueou a ação')
        return record

    # 5. Checkpoint obrigatório (snapshot de código + runtime)
    files_to_touch = list(set(plan.files_to_create + plan.files_to_modify))
    snapshots = _snapshot_files(files_to_touch, plan_snapshot_dir)
    try:
        from runtime_state import save_checkpoint
        cp_id = save_checkpoint(f'auto-evolve-{plan.gap.reference_id}')
    except Exception as e:
        cp_id = None
        print(f'[EVOLVE] Aviso: checkpoint runtime: {e}')
    if not files_to_touch and cp_id is None:
        record['final_state'] = STATE_CHECKPOINTED
        record['checkpoint'] = 'parcial'
    record['snapshots'] = snapshots
    record['runtime_checkpoint'] = cp_id

    # 6. Montar comando de delegação
    steps_desc = ' | '.join(plan.implementation_steps)
    if shutil.which('opencode'):
        cmd = (f'opencode run --model nvidia/deepseek-ai/deepseek-v4-flash '
               f'--agent general "Execute o plano de evolução do EcoSystemUmGrau. '
               f'Objetivo: {plan.gap.reference_name}. {steps_desc}. '
               f'Respeite os arquivos: {files_to_touch}. Trabalhe na raiz do projeto '
               f'C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau. '
               f'Retorne o que foi alterado."')
    else:
        cmd = (f'ler "{plan.gap.reference_name}. {steps_desc} '
               f'(respete: {files_to_touch})"')

    timeout_seconds = 900 if plan.gap.effort == 'large' else 300
    record['command'] = cmd
    record['timeout_seconds'] = timeout_seconds

    # 7. Delegar execução
    record['final_state'] = STATE_EXECUTING
    exec_result = _run_executor(cmd, timeout_seconds)

    if exec_result['execution_status'] == 'timeout':
        record['execution'] = exec_result
        record['final_state'] = STATE_TIMEOUT
        record['final_status'] = 'timeout'
        # Avaliar se houve mudança parcial → rollback
        after = _git_status()
        status, changes = _detect_changes(git_before, after)
        if status == 'mudanca_detectada':
            _restore_snapshots(snapshots)
            record['rollback'] = 'ok'
            record['final_status'] = 'rolled_back'
        _register_memory('erro', f'Timeout na evolução: {plan.gap.reference_name}',
                         f'Subagente excedeu {timeout_seconds}s.', {'gap': plan.gap.reference_id})
        return record

    if exec_result['execution_status'] == 'failed':
        record['execution'] = exec_result
        record['final_state'] = STATE_VALIDATION_FAILED
        record['final_status'] = 'execution_failed'
        _register_memory('erro', f'Falha na execução: {plan.gap.reference_name}',
                         f'Exit {exec_result.get("exit_code")}. {exec_result.get("error", "")}',
                         {'gap': plan.gap.reference_id})
        return record

    record['execution'] = exec_result

    # 8. Detecção de mudanças
    after = _git_status()
    change_status, changes = _detect_changes(git_before, after)
    if change_status == 'sem_mudanca':
        record['final_state'] = STATE_NO_CHANGE
        record['final_status'] = 'sem_mudanca'
        record['note'] = 'Executor terminou com sucesso mas nada mudou'
        return record
    record['changes'] = changes

    # 9. Validação de escopo
    allowed_paths = [p for p in files_to_touch if not p.startswith('scripts/_legado')]
    scope_ok, violations = _validate_scope(changes, allowed_paths)
    if not scope_ok:
        record['final_state'] = STATE_VALIDATION_FAILED
        record['final_status'] = 'alteracao_invalida'
        record['violations'] = violations
        _restore_snapshots(snapshots)
        record['rollback'] = 'ok'
        record['final_status'] = 'rolled_back'
        _register_memory('erro', f'Alteração fora de escopo: {plan.gap.reference_name}',
                         f'Violou: {violations}', {'gap': plan.gap.reference_id})
        return record

    # 10. Preflight técnico (obrigatório salvo --no-preflight)
    if no_preflight:
        record['preflight_technical'] = {'passed': None, 'note': 'ignorado por --no-preflight'}
    else:
        pt = _run_preflight('preflight_check.py')
        record['preflight_technical'] = pt
        if not pt['passed']:
            record['final_state'] = STATE_VALIDATION_FAILED
            record['final_status'] = 'validation_failed'
            _restore_snapshots(snapshots)
            record['rollback'] = 'ok'
            record['final_status'] = 'rolled_back'
            _register_memory('erro', f'Preflight técnico falhou: {plan.gap.reference_name}',
                             f'Exit {pt.get("exit_code")}. {pt.get("error", "")}',
                             {'gap': plan.gap.reference_id})
            return record

    # 11. Preflight ético
    if no_preflight:
        record['preflight_ethical'] = {'passed': None, 'note': 'ignorado por --no-preflight'}
    else:
        pe = _run_preflight('preflight_etica.py')
        record['preflight_ethical'] = pe
        if not pe['passed']:
            record['final_state'] = STATE_VALIDATION_FAILED
            record['final_status'] = 'validation_failed'
            _restore_snapshots(snapshots)
            record['rollback'] = 'ok'
            record['final_status'] = 'rolled_back'
            _register_memory('erro', f'Preflight ético falhou: {plan.gap.reference_name}',
                             f'Exit {pe.get("exit_code")}. {pe.get("error", "")}',
                             {'gap': plan.gap.reference_id})
            return record

    # 12. Testes
    test_result = _run_tests()
    record['tests'] = test_result
    if not test_result['passed']:
        record['final_state'] = STATE_VALIDATION_FAILED
        record['final_status'] = 'validation_failed'
        _restore_snapshots(snapshots)
        record['rollback'] = 'ok'
        record['final_status'] = 'rolled_back'
        _register_memory('erro', f'Testes falharam: {plan.gap.reference_name}',
                         test_result.get('output', '')[:300],
                         {'gap': plan.gap.reference_id})
        return record

    # 13. Persistir via gate
    persist = _persist_via_gate()
    record['persistence'] = persist
    if not persist['passed']:
        record['final_state'] = STATE_PERSISTING
        record['final_status'] = 'persistence_failed'
        _register_memory('erro', f'Persistência falhou: {plan.gap.reference_name}',
                         persist.get('error', '')[:300], {'gap': plan.gap.reference_id})
        return record

    # 14. Registrar memória de decisão + idempotência + estado
    record['final_state'] = STATE_COMPLETED
    record['final_status'] = 'completed'
    _record_applied(fp, {'gap_id': plan.gap.reference_id,
                         'final_status': 'completed',
                         'executor': record['executor'],
                         'completed_at': datetime.now().isoformat()})
    _register_memory(
        'decisao', f'Evolução aplicada: {plan.gap.reference_name}',
        f'Gap {plan.gap.reference_id} implementado via {record["executor"]}. '
        f'Validações: técnico={record.get("preflight_technical", {}).get("passed")}, '
        f'ético={record.get("preflight_ethical", {}).get("passed")}, testes=OK.',
        {'gap': plan.gap.reference_id, 'plan': plan.gap.reference_name,
         'executor': record['executor']},
        source_anchors=[{'filePath': 'scripts/auto_evolution.py', 'lineStart': 1,
                         'lineEnd': 20, 'snippet': 'Ciclo fechado de auto-evolução'}],
    )

    # 15. Limpar snapshot do plano (evolução aprovada e persistida)
    try:
        shutil.rmtree(plan_snapshot_dir, ignore_errors=True)
    except Exception:
        pass

    _save_cycle_record(record)
    return record


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
    """Imprime gaps formatados com fontes relevantes."""
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
        if gap.sources:
            print(f'     Fontes:')
            for s in gap.sources:
                print(f'       [{s.get("authority_level", "?")}] {s.get("name", "")} ({s.get("url", "")})')
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


def _run_health() -> Dict[str, Any]:
    """Diagnóstico autônomo da saúde do ecossistema (orquestra checks existentes).

    Reutiliza os checks consolidados (preflight técnico, preflight ético,
    testes, git status read-only, memória) sem duplicar a lógica deles.
    Gera um relatório único e um veredito geral. Se um check apontar falha,
    o ecossistema permanece operante mas o relatório marca a saúde degradada
    para atuação subsequente (evolve/audit).
    """
    import subprocess as _sp
    report = {'timestamp': datetime.now().isoformat(), 'checks': {}, 'saudavel': True}

    def _run(cmd, timeout=120):
        try:
            r = _sp.run(['python', os.path.join('scripts', cmd)], capture_output=True,
                        text=True, cwd=BASE, timeout=timeout, env={**os.environ, 'PYTHONUTF8': '1'})
            return {'exit_code': r.returncode, 'passed': r.returncode == 0,
                    'output': (r.stdout or '')[-1200:], 'error': (r.stderr or '')[-800:]}
        except Exception as e:
            return {'exit_code': -1, 'passed': False, 'output': '', 'error': str(e)}

    report['checks']['preflight_tecnico'] = _run('preflight_check.py')
    report['checks']['preflight_etico'] = _run('preflight_etica.py')

    try:
        from runtime_state import save_checkpoint
        cp = save_checkpoint('auto-evolution-health')
        if isinstance(cp, dict):
            report['checkpoint'] = cp.get('id') or cp
        else:
            report['checkpoint'] = cp
    except Exception as e:
        report['checkpoint'] = {'id': None, 'erro': str(e)}

    # Git status read-only (sem commitar — gate de persistência intocado)
    try:
        r = _sp.run(['git', 'status', '--short'], capture_output=True, text=True,
                    cwd=BASE, timeout=60)
        pendentes = [l for l in (r.stdout or '').splitlines() if l.strip()]
        report['checks']['git_status'] = {'passed': True, 'pendentes': len(pendentes),
                                          'output': (r.stdout or '')[:1500]}
    except Exception as e:
        report['checks']['git_status'] = {'passed': False, 'error': str(e)}

    # Memória (stats/sanidade), se disponível — read-only
    try:
        r = _sp.run(['python', os.path.join('scripts', 'memory_engine.py'), 'stats'],
                    capture_output=True, text=True, cwd=BASE, timeout=120,
                    env={**os.environ, 'PYTHONUTF8': '1'})
        report['checks']['memoria'] = {'passed': r.returncode == 0,
                                       'output': (r.stdout or '')[:1200],
                                       'error': (r.stderr or '')[:600]}
    except Exception as e:
        report['checks']['memoria'] = {'passed': False, 'error': str(e)}

    report['saudavel'] = all(c.get('passed', True) for c in report['checks'].values()
                             if isinstance(c, dict))
    return report


def _collect_external_gaps() -> Dict[str, Any]:
    """Busca autônoma de gaps em fontes externas via Evolution Radar Collector.

    Executa `evolution_radar_collect.py --full` (collect → filter → package),
    que coleta propostas reais do GitHub e outras fontes configuradas em
    config/evolution_sources.json. Depois consolida as propostas/pacotes
    existentes como candidatos de evolução externa. Reutiliza o coletor
    existente (responsabilidade única) — não recria a coleta.
    """
    import subprocess as _sp
    result = {'timestamp': datetime.now().isoformat(), 'execution': None,
              'candidatos': [], 'pacotes': [], 'saudavel': True}
    try:
        r = _sp.run(['python', os.path.join('scripts', 'evolution_radar_collect.py'), '--full'],
                    capture_output=True, text=True, cwd=BASE, timeout=300,
                    env={**os.environ, 'PYTHONUTF8': '1'})
        result['execution'] = {'exit_code': r.returncode, 'passed': r.returncode == 0,
                               'output': (r.stdout or '')[-2500:],
                               'error': (r.stderr or '')[-1000:]}
    except Exception as e:
        result['execution'] = {'exit_code': -1, 'passed': False, 'output': '', 'error': str(e)}
        result['saudavel'] = False

    # Consolida propostas filtradas (.spec.md) como candidatos
    radar = os.path.join(KNOWLEDGE, 'evolution-radar')
    filtrados = os.path.join(radar, 'filtrado')
    if os.path.isdir(filtrados):
        for f in sorted(os.listdir(filtrados)):
            if f.endswith('.spec.md'):
                result['candidatos'].append({'arquivo': f, 'fonte': 'evolution-radar'})

    # Consolida pacotes gerados
    pacotes = os.path.join(radar, 'pacotes')
    if os.path.isdir(pacotes):
        for f in sorted(os.listdir(pacotes)):
            if f.endswith('.json'):
                result['pacotes'].append(f)

    return result


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
        force = '--force' in sys.argv
        no_preflight = '--no-preflight' in sys.argv
        max_plans = 0
        for i, arg in enumerate(sys.argv):
            if arg == '--max-plans' and i + 1 < len(sys.argv):
                try:
                    max_plans = int(sys.argv[i + 1])
                except ValueError:
                    max_plans = 0
        result = run_evolution(apply_changes=apply, max_plans=max_plans,
                               force=force, no_preflight=no_preflight)
        if result.get('status') == 'evolucao_bloqueada_por_lock':
            print(f'\nEVOLUÇÃO BLOQUEADA POR LOCK')
            print(f'Outra execução está em andamento: {result.get("lock")}')
        elif not apply:
            print(f'\n[DRY-RUN] Nenhuma mudança real foi feita.')
            print(f'Assessment: {result["assessment_file"]}')
            print(f'Gaps: {result["gaps"]} | Planos: {result["plans"]}')
        else:
            print(f'\nResultado da evolução (apply):')
            print(f'  Assessment: {result["assessment_file"]}')
            print(f'  Execution ID: {result.get("execution_id")}')
            print(f'  Planos processados: {len(result["changes"])}')

    elif cmd == 'status':
        _print_status()

    elif cmd == 'health':
        report = _run_health()
        print(f'\n{"="*70}')
        print('  SAÚDE DO ECOSSISTEMA (auto-evolution health)')
        print(f'  {report["timestamp"]}')
        print(f'{"="*70}\n')
        for k, v in report['checks'].items():
            if not isinstance(v, dict):
                continue
            ok = 'OK ' if v.get('passed', True) else 'FALHA'
            print(f'  [{ok}] {k}')
            if v.get('error'):
                print(f'        {v["error"]}')
        cp_val = report.get('checkpoint')
        if isinstance(cp_val, str) and cp_val:
            print(f'  [OK ] checkpoint: {cp_val}')
        veredito = 'SAUDÁVEL' if report['saudavel'] else 'DEGRADADO — atuar via evolve/audit'
        print(f'\n  VEREDITO: {veredito}\n')

    elif cmd == 'radar':
        report = _collect_external_gaps()
        print(f'\n{"="*70}')
        print('  RADAR DE EVOLUÇÃO EXTERNA (auto-evolution radar)')
        print(f'  {report["timestamp"]}')
        print(f'{"="*70}\n')
        ex = report.get('execution') or {}
        print(f'  Coleta (evolution_radar_collect --full): '
              f'{"OK" if ex.get("passed") else "FALHA"} (exit {ex.get("exit_code")})')
        if ex.get('error'):
            print(f'        {ex["error"]}')
        print(f'  Candidatos (propostas filtradas): {len(report["candidatos"])}')
        for c in report['candidatos']:
            print(f'    - {c["arquivo"]} [{c["fonte"]}]')
        print(f'  Pacotes gerados: {len(report["pacotes"])}')
        for p in report['pacotes']:
            print(f'    - {p}')
        print()
        if ex.get('output'):
            print('  --- Saída da coleta (resumo) ---')
            print(ex['output'])
            print()

    else:
        print(f'Comando desconhecido: {cmd}')
        print(__doc__)


if __name__ == '__main__':
    main()
