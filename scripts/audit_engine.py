"""Audit Engine - Trilha de evidências estruturada por decisão.

Fornece:
- Registro imutável de decisões com evidências
- Cadeia de custódia (hash chaining)
- Correlação de eventos (decisão → ação → resultado)
- Queries auditáveis (quem, o quê, quando, por quê, evidência)
- Relatórios de conformidade
- Integração com Kernel, Council, Mission Planner, Security Engine
"""

import os
import sys
import json
import hashlib
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
AUDIT_DIR = os.path.join(RUNTIME_DIR, 'audit')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class DecisionType(Enum):
    ARCHITECTURAL = "architectural"
    TECHNICAL = "technical"
    SECURITY = "security"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    ETHICAL = "ethical"


class EvidenceType(Enum):
    CODE = "code"
    DOCUMENT = "document"
    LOG = "log"
    METRIC = "metric"
    TEST_RESULT = "test_result"
    EXTERNAL_REF = "external_ref"
    HUMAN_INPUT = "human_input"
    AGENT_OUTPUT = "agent_output"
    TOOL_RESULT = "tool_result"


@dataclass
class Evidence:
    id: str
    type: EvidenceType
    source: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    previous_hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        type_val = self.type.value if hasattr(self.type, 'value') else self.type
        data = f"{self.id}{type_val}{self.source}{self.content}{self.timestamp}{self.previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class Decision:
    id: str
    type: DecisionType
    title: str
    description: str
    context: str
    rationale: str
    alternatives_considered: List[str] = field(default_factory=list)
    criteria_used: List[str] = field(default_factory=list)
    decision_maker: str = "system"  # system, human, council, agent
    agents_involved: List[str] = field(default_factory=list)
    status: str = "proposed"  # proposed, approved, rejected, superseded
    evidence_ids: List[str] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    decided_at: str = ""
    superseded_by: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    id: str
    decision_id: str
    action: str  # created, evidence_added, approved, rejected, superseded, queried
    actor: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    hash_chain: str = ""


class AuditEngine:
    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.evidence: Dict[str, Evidence] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.max_audit_log = 5000
        self._lock = threading.RLock()
        self._last_hash = "0" * 16
        self._load()

    def _get_storage_paths(self):
        return {
            'decisions': os.path.join(AUDIT_DIR, 'decisions.json'),
            'evidence': os.path.join(AUDIT_DIR, 'evidence.json'),
            'audit_log': os.path.join(AUDIT_DIR, 'audit_log.json'),
        }

    def _ensure_dirs(self):
        os.makedirs(AUDIT_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        paths = self._get_storage_paths()
        try:
            if os.path.exists(paths['decisions']):
                with open(paths['decisions'], encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    self.decisions[item['id']] = Decision(**item)
            if os.path.exists(paths['evidence']):
                with open(paths['evidence'], encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                for item in data:
                    self.evidence[item['id']] = Evidence(**item)
            if os.path.exists(paths['audit_log']):
                with open(paths['audit_log'], encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                self.audit_log = data
                if self.audit_log:
                    self._last_hash = self.audit_log[-1].get('hash_chain', '0' * 16)
        except Exception as e:
            print(f"[AuditEngine] Erro ao carregar: {e}")

    def _save(self):
        self._ensure_dirs()
        paths = self._get_storage_paths()
        try:
            def serialize_decision(d):
                data = asdict(d)
                data['type'] = d.type.value if hasattr(d.type, 'value') else d.type
                return data

            def serialize_evidence(e):
                data = asdict(e)
                data['type'] = e.type.value if hasattr(e.type, 'value') else e.type
                return data

            tmp_d = paths['decisions'] + '.tmp'
            with open(tmp_d, 'w', encoding='utf-8') as f:
                json.dump([serialize_decision(d) for d in self.decisions.values()], f, ensure_ascii=False, indent=2)
            os.replace(tmp_d, paths['decisions'])

            tmp_e = paths['evidence'] + '.tmp'
            with open(tmp_e, 'w', encoding='utf-8') as f:
                json.dump([serialize_evidence(e) for e in self.evidence.values()], f, ensure_ascii=False, indent=2)
            os.replace(tmp_e, paths['evidence'])

            tmp_a = paths['audit_log'] + '.tmp'
            with open(tmp_a, 'w', encoding='utf-8') as f:
                json.dump(self.audit_log[-self.max_audit_log:], f, ensure_ascii=False, indent=2)
            os.replace(tmp_a, paths['audit_log'])
        except Exception as e:
            print(f"[AuditEngine] Erro ao salvar: {e}")

    def _compute_hash_chain(self, entry: AuditEntry) -> str:
        data = f"{entry.id}{entry.decision_id}{entry.action}{entry.actor}{entry.timestamp}{self._last_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _record_audit(self, decision_id: str, action: str, actor: str, details: Dict = None):
        entry = AuditEntry(
            id=str(uuid.uuid4())[:12],
            decision_id=decision_id,
            action=action,
            actor=actor,
            details=details or {},
        )
        entry.hash_chain = self._compute_hash_chain(entry)
        self._last_hash = entry.hash_chain
        self.audit_log.append(asdict(entry))
        if len(self.audit_log) > self.max_audit_log:
            self.audit_log = self.audit_log[-self.max_audit_log:]

    def create_decision(
        self,
        type: DecisionType,
        title: str,
        description: str,
        context: str,
        rationale: str,
        decision_maker: str = "system",
        agents_involved: List[str] = None,
        alternatives: List[str] = None,
        criteria: List[str] = None,
        tags: List[str] = None,
    ) -> Decision:
        decision_id = str(uuid.uuid4())[:12]
        decision = Decision(
            id=decision_id,
            type=type,
            title=title,
            description=description,
            context=context,
            rationale=rationale,
            decision_maker=decision_maker,
            agents_involved=agents_involved or [],
            alternatives_considered=alternatives or [],
            criteria_used=criteria or [],
            tags=tags or [],
        )
        with self._lock:
            self.decisions[decision_id] = decision
            self._record_audit(decision_id, "created", decision_maker, {
                'type': type.value,
                'title': title,
            })
            self._save()
        return decision

    def add_evidence(
        self,
        decision_id: str,
        type: EvidenceType,
        source: str,
        content: str,
        metadata: Dict = None,
    ) -> Evidence:
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        evidence_id = str(uuid.uuid4())[:12]
        previous_hash = self.evidence[decision.evidence_ids[-1]].hash if decision.evidence_ids else self._last_hash

        evidence = Evidence(
            id=evidence_id,
            type=type,
            source=source,
            content=content,
            metadata=metadata or {},
            previous_hash=previous_hash,
        )

        with self._lock:
            self.evidence[evidence_id] = evidence
            decision.evidence_ids.append(evidence_id)
            decision.metadata['last_evidence_at'] = evidence.timestamp
            self._record_audit(decision_id, "evidence_added", source, {
                'evidence_id': evidence_id,
                'type': type.value,
            })
            self._save()
        return evidence

    def approve_decision(self, decision_id: str, actor: str, notes: str = "") -> bool:
        decision = self.decisions.get(decision_id)
        if not decision:
            return False
        if decision.status != "proposed":
            return False
        decision.status = "approved"
        decision.decided_at = datetime.now().isoformat(timespec='seconds')
        self._record_audit(decision_id, "approved", actor, {'notes': notes})
        self._save()
        return True

    def reject_decision(self, decision_id: str, actor: str, reason: str) -> bool:
        decision = self.decisions.get(decision_id)
        if not decision:
            return False
        decision.status = "rejected"
        decision.decided_at = datetime.now().isoformat(timespec='seconds')
        decision.metadata['rejection_reason'] = reason
        self._record_audit(decision_id, "rejected", actor, {'reason': reason})
        self._save()
        return True

    def supersede_decision(self, old_id: str, new_id: str, actor: str) -> bool:
        old = self.decisions.get(old_id)
        new = self.decisions.get(new_id)
        if not old or not new:
            return False
        old.status = "superseded"
        old.superseded_by = new_id
        new.related_decisions.append(old_id)
        self._record_audit(old_id, "superseded", actor, {'superseded_by': new_id})
        self._record_audit(new_id, "supersedes", actor, {'supersedes': old_id})
        self._save()
        return True

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        return self.decisions.get(decision_id)

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        return self.evidence.get(evidence_id)

    def get_decision_with_evidence(self, decision_id: str) -> Dict[str, Any]:
        decision = self.decisions.get(decision_id)
        if not decision:
            return {}
        evidence_list = [self.evidence[eid] for eid in decision.evidence_ids if eid in self.evidence]
        return {
            'decision': asdict(decision),
            'evidence': [asdict(e) for e in evidence_list],
            'evidence_count': len(evidence_list),
        }

    def query_decisions(
        self,
        type: DecisionType = None,
        status: str = None,
        tags: List[str] = None,
        agent: str = None,
        since: str = None,
        limit: int = 50,
    ) -> List[Decision]:
        results = []
        for d in self.decisions.values():
            if type and d.type != type:
                continue
            if status and d.status != status:
                continue
            if tags and not any(t in d.tags for t in tags):
                continue
            if agent and agent not in d.agents_involved and d.decision_maker != agent:
                continue
            if since and d.created_at < since:
                continue
            results.append(d)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def get_audit_trail(self, decision_id: str) -> List[Dict[str, Any]]:
        return [entry for entry in self.audit_log if entry.get('decision_id') == decision_id]

    def verify_integrity(self) -> Dict[str, Any]:
        """Verifica integridade da cadeia de hash."""
        issues = []
        last_hash = "0" * 16
        for i, entry in enumerate(self.audit_log):
            expected = hashlib.sha256(
                f"{entry['id']}{entry['decision_id']}{entry['action']}{entry['actor']}{entry['timestamp']}{last_hash}".encode()
            ).hexdigest()[:16]
            if entry.get('hash_chain') != expected:
                issues.append(f"Entry {i} ({entry['id']}): hash chain broken")
            last_hash = entry.get('hash_chain', '')

        # Verify evidence chain
        for eid, ev in self.evidence.items():
            expected = ev._compute_hash()
            if ev.hash != expected:
                issues.append(f"Evidence {eid}: hash mismatch (got {ev.hash}, expected {expected})")

        return {
            'audit_log_entries': len(self.audit_log),
            'evidence_count': len(self.evidence),
            'decisions_count': len(self.decisions),
            'integrity_ok': len(issues) == 0,
            'issues': issues,
        }

    def generate_report(self, decision_id: str = None, since: str = None) -> str:
        lines = ["=== AUDIT REPORT ==="]
        if decision_id:
            data = self.get_decision_with_evidence(decision_id)
            if not data:
                return f"Decision {decision_id} not found"
            d = data['decision']
            lines.append(f"\nDecision: {d['title']} ({d['id']})")
            lines.append(f"Type: {d['type']} | Status: {d['status']}")
            lines.append(f"Maker: {d['decision_maker']} | Agents: {', '.join(d['agents_involved']) or 'none'}")
            lines.append(f"Created: {d['created_at']} | Decided: {d['decided_at'] or 'pending'}")
            lines.append(f"\nRationale: {d['rationale']}")
            lines.append(f"\nEvidence ({data['evidence_count']}):")
            for ev in data['evidence']:
                lines.append(f"  [{ev['type']}] {ev['source']} @ {ev['timestamp'][:19]}")
                lines.append(f"    Hash: {ev['hash']} (prev: {ev['previous_hash']})")
                lines.append(f"    {ev['content'][:120]}...")
            trail = self.get_audit_trail(decision_id)
            lines.append(f"\nAudit Trail ({len(trail)} entries):")
            for entry in trail:
                lines.append(f"  {entry['timestamp'][:19]} | {entry['action']} | {entry['actor']}")
        else:
            decisions = list(self.decisions.values())
            if since:
                decisions = [d for d in decisions if d.created_at >= since]
            lines.append(f"\nTotal Decisions: {len(decisions)}")
            by_status = defaultdict(int)
            by_type = defaultdict(int)
            for d in decisions:
                by_status[d.status] += 1
                by_type[d.type.value] += 1
            lines.append(f"By Status: {dict(by_status)}")
            lines.append(f"By Type: {dict(by_type)}")

        integrity = self.verify_integrity()
        lines.append(f"\nIntegrity: {'OK' if integrity['integrity_ok'] else 'BROKEN'}")
        if integrity['issues']:
            for issue in integrity['issues']:
                lines.append(f"  ISSUE: {issue}")

        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        return {
            'decisions': len(self.decisions),
            'evidence': len(self.evidence),
            'audit_entries': len(self.audit_log),
            'by_status': {k: v for k, v in defaultdict(int, [(d.status, 1) for d in self.decisions.values()]).items()},
            'by_type': {k: v for k, v in defaultdict(int, [(d.type.value, 1) for d in self.decisions.values()]).items()},
            'integrity': self.verify_integrity()['integrity_ok'],
        }


audit = AuditEngine()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Audit Engine - Evidence trail')
    sub = parser.add_subparsers(dest='cmd')

    p_decide = sub.add_parser('decide')
    p_decide.add_argument('type', choices=[t.value for t in DecisionType])
    p_decide.add_argument('title')
    p_decide.add_argument('description')
    p_decide.add_argument('context')
    p_decide.add_argument('rationale')
    p_decide.add_argument('--maker', default='system')
    p_decide.add_argument('--agents', default='')
    p_decide.add_argument('--alternatives', default='')
    p_decide.add_argument('--criteria', default='')
    p_decide.add_argument('--tags', default='')

    p_evidence = sub.add_parser('evidence')
    p_evidence.add_argument('decision_id')
    p_evidence.add_argument('type', choices=[t.value for t in EvidenceType])
    p_evidence.add_argument('source')
    p_evidence.add_argument('content')
    p_evidence.add_argument('--meta', default='{}')

    p_approve = sub.add_parser('approve')
    p_approve.add_argument('decision_id')
    p_approve.add_argument('actor')
    p_approve.add_argument('--notes', default='')

    p_reject = sub.add_parser('reject')
    p_reject.add_argument('decision_id')
    p_reject.add_argument('actor')
    p_reject.add_argument('reason')

    p_show = sub.add_parser('show')
    p_show.add_argument('decision_id')

    p_query = sub.add_parser('query')
    p_query.add_argument('--type', choices=[t.value for t in DecisionType])
    p_query.add_argument('--status')
    p_query.add_argument('--tags', default='')
    p_query.add_argument('--agent')
    p_query.add_argument('--since')
    p_query.add_argument('--limit', type=int, default=20)

    p_trail = sub.add_parser('trail')
    p_trail.add_argument('decision_id')

    p_verify = sub.add_parser('verify')

    p_report = sub.add_parser('report')
    p_report.add_argument('--decision')
    p_report.add_argument('--since')

    p_stats = sub.add_parser('stats')

    args = parser.parse_args()

    if args.cmd == 'decide':
        d = audit.create_decision(
            type=DecisionType(args.type),
            title=args.title,
            description=args.description,
            context=args.context,
            rationale=args.rationale,
            decision_maker=args.maker,
            agents_involved=args.agents.split(',') if args.agents else [],
            alternatives=args.alternatives.split(',') if args.alternatives else [],
            criteria=args.criteria.split(',') if args.criteria else [],
            tags=args.tags.split(',') if args.tags else [],
        )
        print(f"Decision created: {d.id} - {d.title}")

    elif args.cmd == 'evidence':
        ev = audit.add_evidence(
            args.decision_id,
            EvidenceType(args.type),
            args.source,
            args.content,
            json.loads(args.meta),
        )
        print(f"Evidence added: {ev.id} ({ev.type.value}) hash={ev.hash}")

    elif args.cmd == 'approve':
        ok = audit.approve_decision(args.decision_id, args.actor, args.notes)
        print(f"Approved: {ok}")

    elif args.cmd == 'reject':
        ok = audit.reject_decision(args.decision_id, args.actor, args.reason)
        print(f"Rejected: {ok}")

    elif args.cmd == 'show':
        data = audit.get_decision_with_evidence(args.decision_id)
        if data:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("Not found")

    elif args.cmd == 'query':
        tags = args.tags.split(',') if args.tags else None
        dtype = DecisionType(args.type) if args.type else None
        results = audit.query_decisions(type=dtype, status=args.status, tags=tags, agent=args.agent, since=args.since, limit=args.limit)
        for d in results:
            print(f"{d.id} | {d.type.value} | {d.status} | {d.title[:50]} | {d.decision_maker}")

    elif args.cmd == 'trail':
        trail = audit.get_audit_trail(args.decision_id)
        for entry in trail:
            print(f"{entry['timestamp'][:19]} | {entry['action']} | {entry['actor']} | {entry.get('details', {})}")

    elif args.cmd == 'verify':
        result = audit.verify_integrity()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == 'report':
        print(audit.generate_report(args.decision, args.since))

    elif args.cmd == 'stats':
        print(json.dumps(audit.stats(), indent=2, ensure_ascii=False))

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())