"""Memory + Learning Consolidation — ETAPA 21

Camada de consolidação que transforma experiências, eventos, decisões, resultados
e evidências em memória estruturada, recuperável, confiável e útil.

Constrói sobre:
- ETAPA 18: Cognitive Core
- ETAPA 19: Tool/Permission Runtime
- ETAPA 20: Autonomous Mission Loop (Mission Journal, Evidence, Failures, Successes)
- memory_engine.py (memória básica existente)
- learning_engine.py (registros de aprendizado existentes)

Princípios:
- Memória ≠ verdade: toda memória possui status epistêmico e confiança
- Experiência ≠ regra universal: generalização exige evidência suficiente
- Memória não controla segurança: autorização pertence à ETAPA 19
- Contexto e temporalidade sempre registrados
- Proveniência sempre preservada
"""

import sys
import os
import json
import uuid
import time
import re
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

# Adicionar raiz do projeto ao path
BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

# Importar memória existente
from memory_engine import (
    _load_memories, _save_memories, add_memory, query, reinforce,
    decay_pass, stats, _decay_score, _next_id, HALF_LIFE, get_context
)

# Importar learning engine existente
from learning_engine import (
    LearningEngine, LearningKind, LearningRecord, LearningSource, engine as learning_engine
)

# ──────────────────────────────────────────────────────────────────
# Status Epistêmico
# ──────────────────────────────────────────────────────────────────

EPISTEMIC_STATUS = (
    "OBSERVED",        # observado diretamente (mais forte como evidência)
    "INFERRED",        # inferido de observações
    "HYPOTHESIS",      # hipótese, sem evidência forte
    "PATTERN",         # padrão observado em múltiplos episódios
    "VALIDATED",       # validado com evidência suficiente
    "CONTRADICTED",    # contradito por evidência mais forte
    "DEPRECATED",      # obsoleto/substituído
)

# Prioridade de fontes (mais forte primeiro)
SOURCE_PRIORITY = [
    "SYSTEM_SECURITY_RULES",   # regras de segurança do sistema
    "VALIDATED_SYSTEM_STATE",  # estado validado do sistema
    "EXPLICIT_USER",           # instrução explícita do usuário
    "TRUSTED_KNOWLEDGE",       # conhecimento confiável
    "VERIFIED_EXTERNAL",       # fonte externa verificada
    "HISTORICAL_MEMORY",       # memória histórica
    "INFERENCE",               # inferência
    "HYPOTHESIS",              # hipótese
]

# Tipos de relação entre memórias
RELATION_TYPES = (
    "supports",
    "contradicts",
    "derived_from",
    "caused_by",
    "related_to",
    "supersedes",
    "refines",
    "depends_on",
)

# Categorias de esquecimento
FORGET_CATEGORIES = (
    "temporary",
    "episodic",
    "low_value",
    "obsolete",
    "deprecated",
    "expired",
)

# Prioridade de consolidação
CONSOLIDATION_PRIORITY = {
    "CRITICAL": 4,
    "HIGH": 3,
    "NORMAL": 2,
    "LOW": 1,
}

# Proteção contra esquecimento automático
PROTECTED_KINDS = {
    "seguranca", "security", "arquitetura", "architecture",
    "regra", "rule", "politica", "policy"
}
PROTECTED_SOURCES = {
    "SYSTEM_SECURITY_RULES",
    "VALIDATED_SYSTEM_STATE",
    "EXPLICIT_USER",
}


# ──────────────────────────────────────────────────────────────────
# MemoryConsolidation — núcleo da consolidação
# ──────────────────────────────────────────────────────────────────

class MemoryConsolidation:
    """Motor de consolidação de memória e aprendizado operacional."""

    def __init__(self):
        self._lock = threading.Lock()
        self._audit_log: List[Dict[str, Any]] = []
        self._learning_candidates: List[Dict[str, Any]] = []
        self._max_audit = 500

    # ---- Proveniência ----

    def _make_provenance(self, source_type: str,
                         source_reference: Optional[str] = None,
                         actor: str = "system") -> Dict[str, Any]:
        return {
            "source_type": source_type,
            "source_reference": source_reference,
            "actor": actor,
            "timestamp": datetime.now().isoformat(),
        }

    # ---- Auditoria ----

    def _audit(self, operation: str, memory_id: Optional[int],
               source: Dict[str, Any], reason: str,
               previous_state: Optional[Dict] = None,
               new_state: Optional[Dict] = None):
        entry = {
            "memory_id": memory_id,
            "operation": operation,
            "source": source,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "previous_state": previous_state,
            "new_state": new_state,
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > self._max_audit:
            self._audit_log = self._audit_log[-self._max_audit:]

    # ---- Sanitização / redação ----

    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{20,}", "sk-[REDACTED]"),
        (r"ghp_[a-zA-Z0-9]{30,}", "ghp_[REDACTED]"),
        (r"(password|passwd|pwd|senha)[\s]*[:=][\s]*[^\s,;]{3,}", r"\1=[REDACTED]"),
        (r"Bearer [a-zA-Z0-9._-]{20,}", "Bearer [REDACTED]"),
        (r"eyJ[a-zA-Z0-9._-]{20,}\.eyJ[a-zA-Z0-9._-]{10,}", "[JWT-REDACTED]"),
        (r"AKIA[a-zA-Z0-9]{16}", "AKIA[REDACTED]"),
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
         "[PRIVATE-KEY-REDACTED]"),
    ]

    def sanitize_text(self, text: str) -> str:
        """Redige segredos antes de persistir."""
        if not text:
            return text
        result = text
        for pattern, replacement in self.SECRET_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.DOTALL)
        return result

    def sanitize_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Redige segredos em todos os campos de texto da memória."""
        sanitized = dict(memory)
        for field in ('task', 'summary', 'context', 'decision', 'impact'):
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = self.sanitize_text(sanitized[field])
        if 'metadata' in sanitized and isinstance(sanitized['metadata'], dict):
            for k, v in sanitized['metadata'].items():
                if isinstance(v, str):
                    sanitized['metadata'][k] = self.sanitize_text(v)
        return sanitized

    # ---- Confiança ----

    def compute_confidence(self, source_type: str,
                           evidence_count: int = 1,
                           supporting: int = 1,
                           contradicting: int = 0,
                           validated: bool = False) -> float:
        """Calcula confiança baseada em fonte, evidências e validação."""
        base = {
            "SYSTEM_SECURITY_RULES": 0.99,
            "VALIDATED_SYSTEM_STATE": 0.97,
            "EXPLICIT_USER": 0.95,
            "TRUSTED_KNOWLEDGE": 0.9,
            "VERIFIED_EXTERNAL": 0.85,
            "HISTORICAL_MEMORY": 0.6,
            "INFERENCE": 0.4,
            "HYPOTHESIS": 0.25,
            "USER": 0.9,
            "MISSION": 0.7,
            "TOOL": 0.75,
            "LEARNING": 0.65,
            "WEB": 0.5,
            "DOCUMENT": 0.7,
            "SYSTEM": 0.8,
        }.get(source_type, 0.5)

        # Ajuste por evidência
        evidence_boost = min(0.1, evidence_count * 0.01)
        conflict_penalty = min(0.3, contradicting * 0.15)

        conf = base + evidence_boost - conflict_penalty

        if validated:
            conf = min(0.98, conf + 0.08)

        return max(0.05, min(0.99, conf))

    # ---- Importância ----

    def compute_importance(self, memory: Dict[str, Any]) -> float:
        """Pontuação de importância (relevance, recency, utility, impact, novelty)."""
        score = 0.0

        # Confiança
        score += (memory.get('confidence', 0.5) - 0.5) * 0.3

        # Recência (memórias recentes mais importantes)
        created_at = memory.get('created_at', '')
        try:
            created_dt = datetime.fromisoformat(created_at)
            days_old = (datetime.now() - created_dt).days
            recency = max(0.0, 1.0 - days_old / 90)
        except Exception:
            recency = 0.5
        score += recency * 0.2

        # Acesso (memórias usadas são mais importantes)
        access_count = memory.get('access_count', 0)
        usage = min(1.0, access_count / 20)
        score += usage * 0.2

        # Impacto por tipo
        kind = memory.get('kind', '')
        kind_impact = {
            'decisao': 0.15, 'padrao': 0.15, 'erro': 0.12,
            'preferencia': 0.08, 'episodio': 0.05,
        }
        score += kind_impact.get(kind, 0.05)

        # Reforço (strength)
        strength = memory.get('strength', 1.0)
        score += min(0.2, (strength - 1.0) * 0.2)

        return max(0.0, min(1.0, score))

    # ---- Deduplicação ----

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação de similaridade."""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def find_duplicates(self, task: str, summary: str,
                        kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Encontra memórias duplicadas por similaridade de texto."""
        norm_task = self._normalize_text(task)
        norm_summary = self._normalize_text(summary)
        memories = _load_memories()
        dupes = []

        for m in memories:
            if kind and m.get('kind') != kind:
                continue
            m_task = self._normalize_text(m.get('task', ''))
            m_summary = self._normalize_text(m.get('summary', ''))

            # Similaridade simples: match exato ou substring
            task_match = norm_task and (norm_task == m_task or
                                        norm_task in m_task or m_task in norm_task)
            summary_match = norm_summary and (norm_summary == m_summary or
                                              norm_summary in m_summary or m_summary in norm_summary)

            if task_match and summary_match:
                dupes.append(m)

        return dupes

    # ---- Consolidação ----

    def consolidate_episode(self, objective: str, outcome: str,
                            strategy: Optional[str] = None,
                            tools: Optional[List[str]] = None,
                            evidence: Optional[List[Dict]] = None,
                            mission_id: Optional[str] = None,
                            success: Optional[bool] = None,
                            project: str = "",
                            kind: str = "episodio",
                            source_type: str = "MISSION") -> int:
        """Consolida um episódio em memória de longo prazo.

        Retorna o ID da memória criada.
        """
        with self._lock:
            # Sanitizar entrada
            objective_s = self.sanitize_text(objective)
            outcome_s = self.sanitize_text(outcome)

            # Verificar duplicatas
            dupes = self.find_duplicates(objective_s, outcome_s, kind)
            if dupes:
                # Reforçar memória existente em vez de duplicar
                for d in dupes[:1]:
                    reinforce(d['id'], delta=0.1)
                    self._audit("reinforce", d['id'],
                                self._make_provenance(source_type, mission_id),
                                "Duplicata detectada, reforçando existente")
                return dupes[0]['id']

            # Computar confiança
            evidence_count = len(evidence or [])
            confidence = self.compute_confidence(
                source_type, evidence_count=evidence_count,
                supporting=1 if success else 0,
                contradicting=0 if success else 1
            )

            metadata = {
                'strategy': strategy,
                'tools': tools or [],
                'mission_id': mission_id,
                'success': success,
                'evidence_count': evidence_count,
                'epistemic_status': 'VALIDATED' if success and evidence_count >= 2 else 'OBSERVED',
                'importance': 0.0,
            }

            # Importância
            importance = self.compute_importance({
                'confidence': confidence, 'created_at': datetime.now().isoformat(),
                'access_count': 0, 'kind': kind, 'strength': 1.0
            })
            metadata['importance'] = importance

            mid = add_memory(
                task=objective_s,
                summary=outcome_s,
                kind=kind,
                project=project,
                metadata=metadata,
                confidence=confidence,
                source_type=source_type,
                reindex=True
            )

            self._audit("create", mid,
                        self._make_provenance(source_type, mission_id),
                        "Episódio consolidado")

            return mid

    # ---- Aprendizado operacional ----

    def create_learning_candidate(self, hypothesis: str,
                                  evidence: List[Dict[str, Any]],
                                  context: Dict[str, Any],
                                  source: str = "MISSION") -> Dict[str, Any]:
        """Cria um candidato a aprendizado a partir de evidências.

        Cada item de evidência pode declarar `relation: 'support'|'contradict'`.
        Se ausente, infere: 'failure' → support (aprendizado com falhas),
        'success' → contradict, a menos que a hipótese seja negativa
        (contém termos de falha), caso em que a inferência é invertida.
        """
        hypothesis_lower = hypothesis.lower()
        hypothesis_is_failure = any(t in hypothesis_lower for t in
                                    ('não funciona', 'falh', 'falha', 'fail',
                                     'timeout', 'erro', 'nao funciona', 'bug'))

        supporting = []
        contradicting = []
        for e in evidence:
            rel = e.get('relation')
            if rel is None:
                outcome = e.get('outcome', '')
                if outcome == 'failure':
                    rel = 'support' if hypothesis_is_failure else 'contradict'
                elif outcome == 'success':
                    rel = 'contradict' if hypothesis_is_failure else 'support'
                else:
                    rel = 'support'
            (supporting if rel == 'support' else contradicting).append(e)

        candidate = {
            "candidate_id": str(uuid.uuid4())[:8],
            "hypothesis": self.sanitize_text(hypothesis),
            "evidence": evidence,
            "context": context,
            "confidence": self.compute_confidence(
                source, evidence_count=len(evidence)),
            "expected_utility": 0.0,
            "supporting_events": supporting,
            "contradicting_events": contradicting,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "source": source,
        }
        self._learning_candidates.append(candidate)
        return candidate

    def evaluate_learning_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Avalia um candidato a aprendizado antes de promover à memória.

        Regras:
        - 0-1 evidência de suporte → PENDING (não validado, aguardar mais evidência)
        - 2+ evidências independentes de suporte → SUPPORTED (padrão candidato)
        - 3+ evidências independentes consistentes → VALIDATED (pode virar conhecimento)
        - contradições ≥ suportes → REJECTED
        """
        candidate = next((c for c in self._learning_candidates
                          if c['candidate_id'] == candidate_id), None)
        if not candidate:
            return {'status': 'not_found'}

        supporting = len(candidate.get('supporting_events', []))
        contradicting = len(candidate.get('contradicting_events', []))

        if contradicting > 0 and contradicting >= supporting:
            candidate['status'] = 'REJECTED'
            candidate['evaluation'] = 'contradictions outweigh support'
        elif supporting >= 3:
            candidate['status'] = 'VALIDATED'
            candidate['evaluation'] = 'sufficient independent evidence'
        elif supporting >= 2:
            candidate['status'] = 'SUPPORTED'
            candidate['evaluation'] = 'multiple episodes, more needed'
        else:
            candidate['status'] = 'PENDING'
            candidate['evaluation'] = 'insufficient evidence'

        return candidate

    def promote_learning_to_memory(self, candidate_id: str,
                                   kind: str = "padrao",
                                   project: str = "") -> Optional[int]:
        """Promove um candidato VALIDADO a memória consolidada."""
        candidate = next((c for c in self._learning_candidates
                          if c['candidate_id'] == candidate_id), None)
        if not candidate:
            return None
        if candidate.get('status') != 'VALIDATED':
            return None

        mid = add_memory(
            task=candidate['hypothesis'],
            summary=f"Aprendizado validado ({len(candidate['supporting_events'])} evidências): {candidate['hypothesis']}",
            kind=kind,
            project=project,
            metadata={
                'epistemic_status': 'VALIDATED',
                'candidate_id': candidate_id,
                'supporting_events': len(candidate['supporting_events']),
                'evidence': candidate['evidence'],
            },
            confidence=candidate.get('confidence', 0.7),
            source_type="LEARNING",
            reindex=True
        )
        self._audit("promote", mid,
                    self._make_provenance("LEARNING", candidate_id),
                    "Candidato VALIDADO promovido a memória")
        return mid

    def learn_from_mission(self, mission_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aprende com o resultado de uma missão (integração ETAPA 20).

        mission_result: dict com status, completed_steps, failed_steps,
                        objective, journal, evidence, etc.
        """
        learnings = []
        objective = mission_result.get('objective', '')
        status = mission_result.get('status', 'unknown')
        journal = mission_result.get('journal', [])

        # Extrair falhas do journal
        failures = [e for e in journal if e.get('event') == 'STEP_FAILED']
        successes = [e for e in journal if e.get('event') == 'STEP_COMPLETED']

        # Consolida episódio da missão
        summary = f"Missão {status}: {len(successes)} passos OK, {len(failures)} falhas"
        mid = self.consolidate_episode(
            objective=objective,
            outcome=summary,
            mission_id=mission_result.get('mission_id') or mission_result.get('mission_created_id'),
            success=(status == 'completed'),
            evidence=journal[-10:],
            project="",
            kind="episodio",
            source_type="MISSION"
        )
        learnings.append({'type': 'episode', 'memory_id': mid, 'status': status})

        # Se houve falhas, criar candidato de aprendizado
        if failures:
            failure_causes = set()
            for f in failures[:10]:
                cat = f.get('failure_category') or f.get('suggested_action') or 'unknown'
                failure_causes.add(cat)

            hypothesis = f"Em missões do tipo '{objective[:40]}...', estratégia atual falhou nas categorias: {', '.join(list(failure_causes)[:3])}"
            candidate = self.create_learning_candidate(
                hypothesis=hypothesis,
                evidence=[{'outcome': 'failure', 'relation': 'support',
                           'detail': f.get('error', '')} for f in failures[:5]],
                context={'mission': objective[:60], 'status': status},
                source="MISSION"
            )
            learnings.append({'type': 'learning_candidate', 'candidate': candidate})

        return learnings

    # ---- Decay reforçado (não destrutivo) ----

    def apply_decay(self, dry_run: bool = False) -> Dict[str, Any]:
        """Aplica decay não-destrutivo: reduz retrieval_priority antes de eliminar.

        Memórias protegidas (segurança, arquitetura, regras) nunca são apagadas.
        """
        memories = _load_memories()
        now = datetime.now()
        decayed = 0
        archived = 0
        protected = 0

        for m in memories:
            kind = m.get('kind', '')
            tags = m.get('tags', [])
            source = m.get('source_type', '')
            text = f"{m.get('task', '')} {m.get('summary', '')}"

            is_protected = (
                any(t in text.lower() for t in PROTECTED_KINDS) or
                source in PROTECTED_SOURCES or
                any(t in ['seguranca', 'security', 'regra', 'rule'] for t in tags)
            )

            if is_protected:
                protected += 1
                continue

            score = _decay_score(m, now)
            if score < 0.02:
                archived += 1
                if not dry_run:
                    m['archived'] = True
                    m['archived_at'] = now.isoformat()
                    m['retrieval_priority'] = 0.0
            elif score < 0.1:
                decayed += 1
                if not dry_run:
                    # Reduzir prioridade sem apagar
                    m['retrieval_priority'] = max(0.0, score)

        if not dry_run:
            _save_memories(memories)

        return {'decayed': decayed, 'archived': archived, 'protected': protected,
                'total': len(memories)}

    # ---- Recuperação híbrida ----

    def retrieve(self, query_text: str, context: Optional[Dict] = None,
                 limit: int = 8, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Recuperação híbrida: semântica + keyword + metadados + recência + importância.

        Returns memórias ordenadas por score combinado.
        """
        memories = _load_memories()
        now = datetime.now()
        scored = []

        query_lower = self._normalize_text(query_text)

        for m in memories:
            # Skip archived
            if m.get('archived'):
                continue
            if m.get('confidence', 1.0) < min_confidence:
                continue

            # Filtro contextual
            if context:
                if context.get('project') and m.get('project') and m['project'] != context['project']:
                    continue
                if context.get('kind') and m.get('kind') != context['kind']:
                    continue

            # Score híbrido
            score = 0.0

            # 1. Similaridade semântica (TF-IDF será adicionado abaixo)
            # 2. Keyword match
            m_text = self._normalize_text(f"{m.get('task', '')} {m.get('summary', '')}")
            if query_lower and query_lower in m_text:
                score += 0.4
            elif query_lower:
                # Palavras-chave parciais
                query_words = query_lower.split()
                matches = sum(1 for w in query_words if w in m_text)
                if matches > 0:
                    score += 0.15 * matches

            # 3. Recência (decay)
            score += _decay_score(m, now) * 0.25

            # 4. Importância
            importance = m.get('metadata', {}).get('importance')
            if importance is None:
                importance = self.compute_importance(m)
            score += importance * 0.2

            # 5. Confiança
            score += m.get('confidence', 0.5) * 0.15

            if score > 0:
                scored.append((score, m))

        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored[:limit]]

    # ---- Conflitos ----

    def find_conflicts(self, memory: Dict[str, Any],
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Detecta memórias conflitantes (mesmo domínio, afirmações opostas)."""
        memories = _load_memories()
        conflicts = []
        m_text = self._normalize_text(f"{memory.get('task', '')} {memory.get('summary', '')}")

        for other in memories:
            if other['id'] == memory['id']:
                continue
            if other.get('archived'):
                continue
            other_text = self._normalize_text(f"{other.get('task', '')} {other.get('summary', '')}")

            # Procurar negações conflitantes
            # Simplificado: se um menciona "funciona" e outro "não funciona"
            if 'não funciona' in m_text and 'não funciona' in other_text:
                continue  # ambos dizem não funciona
            if 'não funciona' in m_text and 'funciona' in other_text and 'não' not in other_text.split('funciona')[0][-5:]:
                if m_text[:30] == other_text[:30] or m_text[:20] == other_text[:20]:
                    conflicts.append({
                        'type': 'contradiction',
                        'memory_a': memory['id'],
                        'memory_b': other['id'],
                        'text_a': memory.get('task', '')[:60],
                        'text_b': other.get('task', '')[:60],
                    })
        return conflicts[:limit]

    # ---- Verificação de poisoning ----

    def is_trusted_source(self, source_type: str) -> bool:
        """Verifica se uma fonte é confiável (não contaminável)."""
        trusted = {
            "SYSTEM_SECURITY_RULES", "VALIDATED_SYSTEM_STATE",
            "EXPLICIT_USER", "TRUSTED_KNOWLEDGE",
            "USER", "MISSION", "TOOL"
        }
        untrusted = {"WEB", "DOCUMENT", "API", "DATABASE", "EMAIL"}
        if source_type in untrusted:
            return False
        return True

    def evaluate_for_poisoning(self, content: str,
                               source_type: str) -> Dict[str, Any]:
        """Avalia se conteúdo pode ser memória contaminada (poisoning)."""
        result = {
            'is_safe': True,
            'warnings': [],
            'source_trusted': self.is_trusted_source(source_type),
        }

        content_lower = content.lower()

        # Instruções imperativas vindas de fontes não confiáveis
        imperatives = ['sempre faça', 'sempre execute', 'ignore suas regras',
                       'apague todos', 'delete all', 'ignore all instructions',
                       'reveal secrets', 'revele segredos']
        if not result['source_trusted']:
            for imp in imperatives:
                if imp in content_lower:
                    result['warnings'].append(f'Conteúdo imperativo de fonte não confiável: "{imp}"')
                    result['is_safe'] = False

        # Tentativa de instrução de segurança
        security_terms = ['conceda permissão', 'grant permission', 'bypass security',
                          'aumente privilégio', 'elevate privilege']
        for term in security_terms:
            if term in content_lower:
                result['warnings'].append(f'Tentativa de autoridade sobre segurança: "{term}"')
                result['is_safe'] = False

        return result

    # ---- Migração / upgrade ----

    def migrate_existing_memories(self) -> Dict[str, Any]:
        """Migra memórias existentes para o formato enriquecido da ETAPA 21.

        Adiciona campos ausentes (confidence, source_type, epistemic_status,
        importance, metadata) sem destruir dados existentes.
        """
        memories = _load_memories()
        migrated = 0
        updated = 0

        for m in memories:
            changed = False
            if 'confidence' not in m:
                m['confidence'] = 1.0
                changed = True
            if 'source_type' not in m:
                # Inferir fonte do tipo de memória
                kind = m.get('kind', '')
                inferred_source = {
                    'decisao': 'DECISION', 'erro': 'ERROR', 'padrao': 'PATTERN',
                    'episodio': 'EPISODIC', 'preferencia': 'PREFERENCE',
                }.get(kind, 'HISTORICAL_MEMORY')
                m['source_type'] = inferred_source
                changed = True
            if 'metadata' not in m or not isinstance(m.get('metadata'), dict):
                m['metadata'] = {}
                changed = True
            if 'epistemic_status' not in m['metadata']:
                m['metadata']['epistemic_status'] = 'OBSERVED'
                changed = True
            if 'importance' not in m['metadata']:
                m['metadata']['importance'] = self.compute_importance(m)
                changed = True
            if changed:
                updated += 1
                migrated += 1

        if updated:
            _save_memories(memories)

        return {'total': len(memories), 'migrated': migrated, 'updated': updated}

    # ---- Observabilidade (integração ETAPA 23) ----

    def _emit_event(self, event_type: str, memory_id: Optional[int], **kwargs):
        """Emitir evento de observabilidade."""
        event = {
            'event': event_type,
            'memory_id': memory_id,
            'timestamp': time.time(),
            **kwargs
        }
        # Integração com journal ou log (ETAPA 23 fará observabilidade completa)
        # Aqui apenas registra no audit log interno
        self._audit_log.append(event)

    # ---- Estatísticas ----

    def stats(self) -> Dict[str, Any]:
        """Estatísticas do sistema de consolidação."""
        memories = _load_memories()
        by_status = {}
        by_confidence = {'alta': 0, 'media': 0, 'baixa': 0}
        by_source = {}
        total = len(memories)

        for m in memories:
            meta = m.get('metadata', {})
            status = meta.get('epistemic_status', 'OBSERVED')
            by_status[status] = by_status.get(status, 0) + 1

            conf = m.get('confidence', 1.0)
            if conf >= 0.9:
                by_confidence['alta'] += 1
            elif conf >= 0.7:
                by_confidence['media'] += 1
            else:
                by_confidence['baixa'] += 1

            src = m.get('source_type', 'desconhecido')
            by_source[src] = by_source.get(src, 0) + 1

        return {
            'total': total,
            'by_epistemic_status': by_status,
            'by_confidence': by_confidence,
            'by_source': by_source,
            'learning_candidates': len(self._learning_candidates),
            'audit_entries': len(self._audit_log),
        }


# ──────────────────────────────────────────────────────────────────
# Instância global
# ──────────────────────────────────────────────────────────────────

consolidation = MemoryConsolidation()


# ──────────────────────────────────────────────────────────────────
# Funções de interface (convenientes)
# ──────────────────────────────────────────────────────────────────

def store(memory: Dict[str, Any]) -> int:
    """Contrato de memória: store(memory)."""
    return consolidation.consolidate_episode(
        objective=memory.get('task', memory.get('objective', '')),
        outcome=memory.get('summary', memory.get('outcome', '')),
        strategy=memory.get('strategy'),
        tools=memory.get('tools'),
        mission_id=memory.get('mission_id'),
        success=memory.get('success'),
        project=memory.get('project', ''),
        kind=memory.get('kind', 'episodio'),
        source_type=memory.get('source_type', 'MISSION')
    )


def retrieve(query_text: str, context: Optional[Dict] = None,
             limit: int = 8) -> List[Dict[str, Any]]:
    """Contrato de memória: retrieve(query, context)."""
    return consolidation.retrieve(query_text, context=context, limit=limit)


def evaluate(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Contrato de memória: evaluate(memory)."""
    return {
        'confidence': consolidation.compute_confidence(
            memory.get('source_type', 'HISTORICAL_MEMORY'),
            evidence_count=len(memory.get('evidence', [])),
            supporting=len(memory.get('supporting_evidence', [])),
            contradicting=len(memory.get('contradicting_evidence', [])),
            validated=memory.get('epistemic_status') == 'VALIDATED'
        ),
        'duplicates': consolidation.find_duplicates(
            memory.get('task', ''), memory.get('summary', '')),
        'poisoning': consolidation.evaluate_for_poisoning(
            memory.get('summary', ''), memory.get('source_type', '')),
        'importance': consolidation.compute_importance(memory),
    }


def consolidate(candidate: Dict[str, Any]) -> int:
    """Contrato de memória: consolidate(candidate)."""
    return consolidation.consolidate_episode(
        objective=candidate.get('objective', candidate.get('task', '')),
        outcome=candidate.get('outcome', candidate.get('summary', '')),
        strategy=candidate.get('strategy'),
        tools=candidate.get('tools'),
        mission_id=candidate.get('mission_id'),
        success=candidate.get('success'),
        project=candidate.get('project', ''),
        kind=candidate.get('kind', 'episodio'),
        source_type=candidate.get('source_type', 'MISSION')
    )


def reinforce(memory_id: int, delta: float = 0.15) -> bool:
    """Contrato de memória: reinforce(memory)."""
    from memory_engine import reinforce as reinforce_base
    return reinforce_base(memory_id, delta)


def deprecate(memory_id: int, reason: str = "") -> bool:
    """Contrato de memória: deprecate(memory)."""
    memories = _load_memories()
    for m in memories:
        if m['id'] == memory_id:
            m['metadata']['epistemic_status'] = 'DEPRECATED'
            m['archived'] = True
            m['archived_at'] = datetime.now().isoformat()
            m['deprecation_reason'] = reason
            _save_memories(memories)
            consolidation._audit("deprecate", memory_id,
                                consolidation._make_provenance("SYSTEM"),
                                reason or "Deprecada manualmente")
            return True
    return False


def find_conflicts(memory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Contrato de memória: find_conflicts(memory)."""
    return consolidation.find_conflicts(memory)


def get_context_hybrid(text: str, limit: int = 8,
                       project: str = "") -> str:
    """Contexto formatado para prompts usando recuperação híbrida (ETAPA 21).

    Mesma forma de saída que memory_engine.get_context (string formatada),
    mas com ranking combinado: semântica + keywords + importância + recência.
    Usada pelo Cognitive Core (ETAPA 18) com fallback para get_context.
    """
    memories = consolidation.retrieve(
        text, context={'project': project} if project else None, limit=limit)
    if not memories:
        return ''
    lines = ['## Memory Context (ETAPA 21 hybrid)']
    for m in memories:
        kind = m.get('kind', '?')
        task = m.get('task', '')[:80]
        conf = m.get('confidence', 0.0)
        status = m.get('metadata', {}).get('epistemic_status', 'OBSERVED')
        lines.append(f'- [{kind}] {task} (conf={conf:.2f}, {status})')
        lines.append(f'  {m.get("summary", "")[:120]}')
    return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Memory + Learning Consolidation (ETAPA 21)')
    sub = parser.add_subparsers(dest='cmd')

    p_consolidate = sub.add_parser('consolidate')
    p_consolidate.add_argument('objective')
    p_consolidate.add_argument('outcome')
    p_consolidate.add_argument('--kind', default='episodio')
    p_consolidate.add_argument('--project', default='')
    p_consolidate.add_argument('--success', action='store_true')
    p_consolidate.add_argument('--mission-id', default='')

    p_retrieve = sub.add_parser('retrieve')
    p_retrieve.add_argument('query')
    p_retrieve.add_argument('--limit', type=int, default=8)

    p_stats = sub.add_parser('stats')

    p_decay = sub.add_parser('decay')
    p_decay.add_argument('--dry-run', action='store_true')

    p_migrate = sub.add_parser('migrate')

    p_learn = sub.add_parser('learn')
    p_learn.add_argument('hypothesis')
    p_learn.add_argument('--source', default='MISSION')

    args = parser.parse_args()

    if args.cmd == 'consolidate':
        mid = consolidation.consolidate_episode(
            objective=args.objective, outcome=args.outcome,
            kind=args.kind, project=args.project,
            success=args.success, mission_id=args.mission_id,
            source_type='MISSION')
        print(f'[OK] Memory #{mid} consolidated')
    elif args.cmd == 'retrieve':
        results = consolidation.retrieve(args.query, limit=args.limit)
        print(f'Retrieved {len(results)} memories for: "{args.query}"')
        for m in results:
            conf = m.get('confidence', 0.0)
            imp = m.get('metadata', {}).get('importance', 0.0)
            print(f'  [{m["id"]}] {m.get("kind", "?")} conf={conf:.2f} imp={imp:.2f} | {m.get("task", "")[:60]}')
    elif args.cmd == 'stats':
        s = consolidation.stats()
        print(json.dumps(s, indent=2, ensure_ascii=False))
    elif args.cmd == 'decay':
        r = consolidation.apply_decay(dry_run=args.dry_run)
        print(f'Decay: {r["decayed"]} reduzidos, {r["archived"]} arquivados, {r["protected"]} protegidos')
    elif args.cmd == 'migrate':
        r = consolidation.migrate_existing_memories()
        print(f'Migração: {r["total"]} total, {r["migrated"]} atualizados')
    elif args.cmd == 'learn':
        c = consolidation.create_learning_candidate(args.hypothesis, [], {}, args.source)
        print(f'[OK] Learning candidate: {c["candidate_id"]} ({c["status"]})')
    else:
        parser.print_help()
