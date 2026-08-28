"""Behavior Slices — Rastreio de Fluxos de Comportamento e Changesets.

Inspirado no Cartographer (miltonian/cartographer), adaptado ao EcoSystemUmGrau.
Permite registrar e consultar fluxos ordenados de execução (behavior flows)
e conjuntos de mudanças (changesets) para auditoria e entendimento de código.

Conceitos:
- Slice: fatia de comportamento (flow ou changeset)
- Step: passo no fluxo (entityId + label + changeType opcional)
- Evidence: âncoras de source (file:line + snippet) + confidence + provenance

Integração:
- Persiste junto ao memory_engine (sessions/memories)
- Usa mesma estrutura de tags, project, confidence
- Recuperável via query semântica existente

Uso:
    from behavior_slices import BehaviorSlices
    bs = BehaviorSlices()
    slice_id = bs.write_slice(
        name="Boot sequence",
        kind="flow",
        steps=[
            {"entityId": "runtime_boot", "label": "Verifica integridade"},
            {"entityId": "runtime_state", "label": "Restaura estado"},
            {"entityId": "memory_engine", "label": "Carrega memória"},
        ],
        evidence={"anchors": [...], "confidence": "proven", "provenance": "deterministic"}
    )
"""

import os
import json
import uuid
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
SLICES_DIR = os.path.join(RUNTIME_DIR, 'behavior_slices')
MEM_DIR = os.path.join(BASE, 'conhecimento', 'memoria')
SESSIONS_DIR = os.path.join(MEM_DIR, 'sessions')

sys.path.insert(0, SCRIPTS)

try:
    from memory_engine import _ensure_dirs as mem_ensure_dirs
    from memory_engine import add_memory
except ImportError:
    mem_ensure_dirs = None
    add_memory = None


class SliceKind(Enum):
    FLOW = "flow"
    CHANGESET = "changeset"


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    AFFECTED = "affected"


class ConfidenceLevel(Enum):
    PROVEN = "proven"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


class ProvenanceKind(Enum):
    DETERMINISTIC = "deterministic"
    INFERRED = "inferred"
    ANNOTATED = "annotated"


@dataclass
class SourceAnchor:
    filePath: str
    lineStart: int
    lineEnd: int
    snippet: str


@dataclass
class Evidence:
    anchors: List[SourceAnchor]
    confidence: ConfidenceLevel
    provenance: ProvenanceKind
    reasoning: Optional[str] = None
    tool: str = "agent"
    supportingFacts: List[str] = field(default_factory=list)
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SliceStep:
    entityId: str
    label: Optional[str] = None
    changeType: Optional[ChangeType] = None


@dataclass
class BehaviorSlice:
    id: str
    name: str
    description: Optional[str]
    kind: SliceKind
    steps: List[SliceStep]
    evidence: Evidence
    tags: List[str] = field(default_factory=list)
    project: str = ""
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())
    updatedAt: str = field(default_factory=lambda: datetime.now().isoformat())


class BehaviorSlices:
    """Gerenciador de behavior slices."""

    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(SLICES_DIR, exist_ok=True)
        os.makedirs(SESSIONS_DIR, exist_ok=True)

    def _get_slices_file(self, project: str = "") -> str:
        proj_suffix = f"_{project}" if project else ""
        return os.path.join(SLICES_DIR, f'slices{proj_suffix}.json')

    def _load_slices(self, project: str = "") -> List[BehaviorSlice]:
        path = self._get_slices_file(project)
        if not os.path.exists(path):
            return []
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            slices = []
            for item in data:
                ev = item['evidence']
                slices.append(BehaviorSlice(
                    id=item['id'],
                    name=item['name'],
                    description=item.get('description'),
                    kind=SliceKind(item['kind']),
                    steps=[SliceStep(**s) for s in item['steps']],
                    evidence=Evidence(
                        anchors=[SourceAnchor(**a) for a in ev['anchors']],
                        confidence=ConfidenceLevel(ev['confidence']),
                        provenance=ProvenanceKind(ev['provenance']),
                        reasoning=ev.get('reasoning'),
                        tool=ev.get('tool', 'agent'),
                        supportingFacts=ev.get('supportingFacts', []),
                        createdAt=ev.get('createdAt', datetime.now().isoformat()),
                    ),
                    tags=item.get('tags', []),
                    project=item.get('project', ''),
                    createdAt=item.get('createdAt', ''),
                    updatedAt=item.get('updatedAt', ''),
                ))
            return slices
        except Exception as e:
            print(f"[BehaviorSlices] Erro ao carregar: {e}")
            return []

    def _save_slices(self, slices: List[BehaviorSlice], project: str = ""):
        path = self._get_slices_file(project)
        self._ensure_dirs()
        tmp = path + '.tmp'
        try:
            data = []
            for s in slices:
                d = asdict(s)
                d['kind'] = s.kind.value
                d['evidence'] = {
                    'anchors': [asdict(a) for a in s.evidence.anchors],
                    'confidence': s.evidence.confidence.value,
                    'provenance': s.evidence.provenance.value,
                    'reasoning': s.evidence.reasoning,
                    'tool': s.evidence.tool,
                    'supportingFacts': s.evidence.supportingFacts,
                    'createdAt': s.evidence.createdAt,
                }
                d['steps'] = [asdict(step) for step in s.steps]
                data.append(d)
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[BehaviorSlices] Erro ao salvar: {e}")
            try:
                os.remove(tmp)
            except Exception:
                pass

    def write_slice(
        self,
        name: str,
        kind: SliceKind,
        steps: List[Dict[str, Any]],
        evidence: Dict[str, Any],
        description: str = None,
        tags: List[str] = None,
        project: str = "",
    ) -> str:
        """Registra ou atualiza um behavior slice.

        Args:
            name: Nome curto (ex: "Boot sequence", "PR #123: Add auth")
            kind: SliceKind.FLOW ou SliceKind.CHANGESET
            steps: Lista de dicts com entityId, label?, changeType?
            evidence: Dict com anchors[], confidence, provenance, reasoning?, tool?, supportingFacts?
            description: Descrição do que o slice representa
            tags: Tags para busca
            project: Projeto associado

        Returns:
            slice_id
        """
        slices = self._load_slices(project)
        now = datetime.now().isoformat()

        # Parse evidence
        ev_data = evidence
        anchors = []
        for a in ev_data.get('anchors', []):
            anchors.append(SourceAnchor(**a))
        ev = Evidence(
            anchors=anchors,
            confidence=ConfidenceLevel(ev_data.get('confidence', 'speculative')),
            provenance=ProvenanceKind(ev_data.get('provenance', 'inferred')),
            reasoning=ev_data.get('reasoning'),
            tool=ev_data.get('tool', 'agent'),
            supportingFacts=ev_data.get('supportingFacts', []),
        )

        # Parse steps
        parsed_steps = []
        for s in steps:
            step_data = {
                'entityId': s['entityId'],
                'label': s.get('label'),
            }
            if s.get('changeType'):
                step_data['changeType'] = ChangeType(s['changeType'])
            parsed_steps.append(SliceStep(**step_data))

        slice_id = f"slice:{name.lower().replace(' ', '_')}:{str(uuid.uuid4())[:8]}"

        # Check if exists (by name+project)
        existing_idx = None
        for i, existing in enumerate(slices):
            if existing.name == name and existing.project == project:
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing
            existing = slices[existing_idx]
            existing.steps = parsed_steps
            existing.evidence = ev
            existing.description = description or existing.description
            existing.tags = tags or existing.tags
            existing.updatedAt = now
            slices[existing_idx] = existing
        else:
            # Create new
            new_slice = BehaviorSlice(
                id=slice_id,
                name=name,
                description=description,
                kind=kind,
                steps=parsed_steps,
                evidence=ev,
                tags=tags or [],
                project=project,
                createdAt=now,
                updatedAt=now,
            )
            slices.append(new_slice)

        self._save_slices(slices, project)

        # Also persist to memory_engine for semantic search integration
        if add_memory:
            try:
                task = f"Behavior slice: {name} ({kind.value})"
                summary = description or f"{len(steps)} steps: " + " -> ".join([s['entityId'] for s in steps[:5]])
                all_tags = ['behavior-slice', kind.value] + (tags or [])
                add_memory(
                    task=task,
                    summary=summary,
                    kind='padrao',
                    project=project,
                    tags=all_tags,
                    confidence=0.9,
                    source_type='inferido',
                    metadata={
                        'slice_id': slice_id,
                        'slice_kind': kind.value,
                        'steps_count': len(steps),
                        'evidence_confidence': ev.confidence.value,
                        'evidence_provenance': ev.provenance.value,
                    },
                )
            except Exception as e:
                print(f"[BehaviorSlices] Aviso: falha ao sincronizar com memory_engine: {e}")

        return slice_id

    def query_slices(
        self,
        project: str = "",
        entity_id: str = None,
        kind: SliceKind = None,
        min_confidence: ConfidenceLevel = None,
        limit: int = 50,
    ) -> List[BehaviorSlice]:
        """Consulta slices com filtros."""
        slices = self._load_slices(project)

        if entity_id:
            slices = [s for s in slices if any(step.entityId == entity_id for step in s.steps)]

        if kind:
            slices = [s for s in slices if s.kind == kind]

        if min_confidence:
            conf_rank = {c: i for i, c in enumerate(ConfidenceLevel)}
            min_rank = conf_rank[min_confidence]
            slices = [s for s in slices if conf_rank[s.evidence.confidence] >= min_rank]

        slices.sort(key=lambda s: s.updatedAt, reverse=True)
        return slices[:limit]

    def get_slice(self, slice_id: str, project: str = "") -> Optional[BehaviorSlice]:
        """Obtém slice por ID."""
        slices = self._load_slices(project)
        for s in slices:
            if s.id == slice_id:
                return s
        return None

    def list_slices(self, project: str = "") -> List[BehaviorSlice]:
        """Lista todos os slices."""
        return self._load_slices(project)

    def delete_slice(self, slice_id: str, project: str = "") -> bool:
        """Remove um slice."""
        slices = self._load_slices(project)
        original_len = len(slices)
        slices = [s for s in slices if s.id != slice_id]
        if len(slices) < original_len:
            self._save_slices(slices, project)
            return True
        return False

    def get_stats(self, project: str = "") -> Dict[str, Any]:
        """Estatísticas dos slices."""
        slices = self._load_slices(project)
        flows = [s for s in slices if s.kind == SliceKind.FLOW]
        changesets = [s for s in slices if s.kind == SliceKind.CHANGESET]

        conf_dist = {}
        for c in ConfidenceLevel:
            conf_dist[c.value] = sum(1 for s in slices if s.evidence.confidence == c)

        prov_dist = {}
        for p in ProvenanceKind:
            prov_dist[p.value] = sum(1 for s in slices if s.evidence.provenance == p)

        return {
            'total': len(slices),
            'flows': len(flows),
            'changesets': len(changesets),
            'confidence_distribution': conf_dist,
            'provenance_distribution': prov_dist,
            'project': project or 'all',
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Behavior Slices CLI')
    sub = parser.add_subparsers(dest='cmd')

    p_write = sub.add_parser('write')
    p_write.add_argument('name')
    p_write.add_argument('kind', choices=['flow', 'changeset'])
    p_write.add_argument('steps', help='JSON array of steps: [{"entityId": "x", "label": "y", "changeType": "added"}]')
    p_write.add_argument('evidence', help='JSON evidence: {"anchors": [...], "confidence": "proven", "provenance": "deterministic"}')
    p_write.add_argument('--description', default='')
    p_write.add_argument('--tags', default='')
    p_write.add_argument('--project', default='')

    p_query = sub.add_parser('query')
    p_query.add_argument('--project', default='')
    p_query.add_argument('--entity', default=None)
    p_query.add_argument('--kind', choices=['flow', 'changeset'], default=None)
    p_query.add_argument('--min-confidence', choices=['proven', 'high', 'medium', 'low', 'speculative'], default=None)
    p_query.add_argument('--limit', type=int, default=20)

    p_get = sub.add_parser('get')
    p_get.add_argument('slice_id')
    p_get.add_argument('--project', default='')

    p_list = sub.add_parser('list')
    p_list.add_argument('--project', default='')

    p_delete = sub.add_parser('delete')
    p_delete.add_argument('slice_id')
    p_delete.add_argument('--project', default='')

    p_stats = sub.add_parser('stats')
    p_stats.add_argument('--project', default='')

    args = parser.parse_args()

    bs = BehaviorSlices()

    if args.cmd == 'write':
        steps = json.loads(args.steps)
        evidence = json.loads(args.evidence)
        tags = args.tags.split(',') if args.tags else []
        slice_id = bs.write_slice(
            name=args.name,
            kind=SliceKind(args.kind),
            steps=steps,
            evidence=evidence,
            description=args.description,
            tags=tags,
            project=args.project,
        )
        print(f'[OK] Slice criado/atualizado: {slice_id}')

    elif args.cmd == 'query':
        kind = SliceKind(args.kind) if args.kind else None
        min_conf = ConfidenceLevel(args.min_confidence) if args.min_confidence else None
        results = bs.query_slices(
            project=args.project,
            entity_id=args.entity,
            kind=kind,
            min_confidence=min_conf,
            limit=args.limit,
        )
        for s in results:
            print(f"  {s.id} [{s.kind.value}] {s.name} ({len(s.steps)} steps) conf={s.evidence.confidence.value} prov={s.evidence.provenance.value}")

    elif args.cmd == 'get':
        s = bs.get_slice(args.slice_id, args.project)
        if s:
            print(json.dumps(asdict(s), ensure_ascii=False, indent=2, default=str))
        else:
            print(f'Slice não encontrado: {args.slice_id}')

    elif args.cmd == 'list':
        slices = bs.list_slices(args.project)
        for s in slices:
            print(f"  {s.id} [{s.kind.value}] {s.name} ({len(s.steps)} steps)")

    elif args.cmd == 'delete':
        if bs.delete_slice(args.slice_id, args.project):
            print(f'[OK] Slice removido: {args.slice_id}')
        else:
            print(f'[ERR] Slice não encontrado: {args.slice_id}')

    elif args.cmd == 'stats':
        print(json.dumps(bs.get_stats(args.project), ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    sys.exit(main())