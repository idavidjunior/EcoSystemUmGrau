"""Learning Engine - Aprendizado contínuo automático do Ecossistema.

Captura aprendizados de forma automática a partir de:
- Execuções de tarefas (sucessos, falhas, gargalos)
- Decisões e suas consequências
- Padrões recorrentes e antipadrões
- Métricas de desempenho (tempo, erros, custo)
- Interações com ferramentas e agentes

Persiste em:
- knowledge_graph.py (nodes + edges)
- memory_engine.py (memories.json)
- conhecimento/aprendizados/ (markdown com frontmatter)
- runtime/learning/learning_state.json (estado interno)
"""

import os
import sys
import json
import re
import uuid
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
LEARNING_DIR = os.path.join(RUNTIME_DIR, 'learning')
APRENDIZADOS_DIR = os.path.join(BASE, 'conhecimento', 'aprendizados')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class LearningKind(Enum):
    DECISAO = "decisao"
    ERRO = "erro"
    PADRAO = "padrao"
    EPISODIO = "episodio"
    LIcaO = "licao"
    MELHORIA = "melhoria"
    ANTIPADRAO = "antipadrao"
    METRICA = "metrica"


class LearningSource(Enum):
    TASK = "task"
    TOOL = "tool"
    AGENT = "agent"
    COUNCIL = "council"
    MISSION = "mission"
    AUDIT = "audit"
    SECURITY = "security"
    USER = "user"
    RUNTIME = "runtime"
    MANUAL = "manual"


@dataclass
class LearningRecord:
    id: str
    title: str
    summary: str
    kind: LearningKind
    source: LearningSource
    tags: List[str] = field(default_factory=list)
    project: str = ""
    context: str = ""
    decision: str = ""
    impact: str = ""
    evidence_id: str = ""
    related: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    confidence: float = 0.8
    weight: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSample:
    id: str
    metric_name: str
    value: float
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))


class LearningEngine:
    def __init__(self):
        self.records: Dict[str, LearningRecord] = {}
        self.metrics: List[MetricSample] = []
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.recent_similar: List[str] = []
        self.max_records = 2000
        self.max_metrics = 5000
        self._lock = threading.RLock()
        self._load()

    def _get_storage_path(self):
        return os.path.join(LEARNING_DIR, 'learning_state.json')

    def _ensure_dirs(self):
        os.makedirs(LEARNING_DIR, exist_ok=True)
        os.makedirs(APRENDIZADOS_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                for item in data.get('records', []):
                    self.records[item['id']] = LearningRecord(
                        id=item['id'],
                        title=item['title'],
                        summary=item['summary'],
                        kind=LearningKind(item['kind']),
                        source=LearningSource(item['source']),
                        tags=item.get('tags', []),
                        project=item.get('project', ''),
                        context=item.get('context', ''),
                        decision=item.get('decision', ''),
                        impact=item.get('impact', ''),
                        evidence_id=item.get('evidence_id', ''),
                        related=item.get('related', []),
                        created_at=item.get('created_at', ''),
                        confidence=item.get('confidence', 0.8),
                        weight=item.get('weight', 1.0),
                        meta=item.get('meta', {}),
                    )
                for item in data.get('metrics', []):
                    self.metrics.append(MetricSample(
                        id=item['id'],
                        metric_name=item['metric_name'],
                        value=item['value'],
                        context=item.get('context', {}),
                        timestamp=item.get('timestamp', ''),
                    ))
                self.pattern_counts = defaultdict(int, data.get('pattern_counts', {}))
            except Exception as e:
                print(f"[LearningEngine] Erro ao carregar: {e}")

    def _save(self):
        self._ensure_dirs()
        path = self._get_storage_path()
        try:
            tmp = path + '.tmp'
            data = {
                'records': [asdict(r) for r in list(self.records.values())[-self.max_records:]],
                'metrics': [asdict(m) for m in self.metrics[-self.max_metrics:]],
                'pattern_counts': dict(self.pattern_counts),
                'updated_at': datetime.now().isoformat(timespec='seconds'),
            }
            for d in data['records']:
                d['kind'] = d['kind'].value if hasattr(d['kind'], 'value') else d['kind']
                d['source'] = d['source'].value if hasattr(d['source'], 'value') else d['source']
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[LearningEngine] Erro ao salvar: {e}")

    def learn(
        self,
        title: str,
        summary: str,
        kind: LearningKind,
        source: LearningSource = LearningSource.TASK,
        tags: List[str] = None,
        project: str = "",
        context: str = "",
        decision: str = "",
        impact: str = "",
        evidence_id: str = "",
        related: List[str] = None,
        confidence: float = 0.8,
        persist_memory: bool = True,
        persist_markdown: bool = True,
    ) -> LearningRecord:
        record_id = hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        record = LearningRecord(
            id=record_id,
            title=title,
            summary=summary,
            kind=kind,
            source=source,
            tags=tags or [],
            project=project,
            context=context,
            decision=decision,
            impact=impact,
            evidence_id=evidence_id,
            related=related or [],
            confidence=confidence,
        )
        with self._lock:
            self.records[record_id] = record
            for tag in record.tags:
                self.pattern_counts[tag] += 1
            self._save()

        # Persist to knowledge graph
        try:
            self._persist_to_kg(record)
        except Exception as e:
            print(f"[LearningEngine] KG persist falhou: {e}")

        # Persist to memory engine
        if persist_memory:
            self._persist_to_memory(record)

        # Persist to markdown
        if persist_markdown:
            self._persist_to_markdown(record)

        return record

    def _persist_to_kg(self, record: LearningRecord):
        try:
            from knowledge_graph import kg, NodeType, EdgeType
            node_type_map = {
                LearningKind.DECISAO: NodeType.DECISION,
                LearningKind.PADRAO: NodeType.PATTERN,
                LearningKind.ERRO: NodeType.ERROR,
                LearningKind.ANTIPADRAO: NodeType.ERROR,
                LearningKind.MELHORIA: NodeType.SOLUTION,
                LearningKind.LIcaO: NodeType.CONCEPT,
                LearningKind.METRICA: NodeType.CONCEPT,
                LearningKind.EPISODIO: NodeType.CONCEPT,
            }
            node = kg.add_node(
                type=node_type_map.get(record.kind, NodeType.CONCEPT),
                name=record.title[:100],
                properties={
                    'summary': record.summary,
                    'source': record.source.value,
                    'impact': record.impact,
                    'learning_id': record.id,
                },
                tags=record.tags,
                source=f"learning_{record.source.value}",
                confidence=record.confidence,
                node_id=f"learn_{record.id}",
                created_at=record.created_at,
            )
            # Link to project if exists
            if record.project:
                projects = kg.find_by_name(record.project)
                if projects:
                    kg.add_edge(projects[0].id, node.id, EdgeType.RELATES_TO, weight=record.weight)
        except Exception as e:
            raise

    def _persist_to_memory(self, record: LearningRecord):
        try:
            import memory_engine
            memory_engine.add_memory(
                task=record.title[:200],
                summary=record.summary[:500],
                kind=record.kind.value,
                project=record.project,
                tags=record.tags,
                confidence=record.confidence,
            )
        except Exception as e:
            print(f"[LearningEngine] memory persist falhou: {e}")

    def _persist_to_markdown(self, record: LearningRecord):
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            safe_title = re.sub(r'[^\w\-]+', '-', record.title).strip('-')[:60]
            fname = os.path.join(APRENDIZADOS_DIR, f"{date_str}-{safe_title}.md")
            content = f"""---
tipo: {record.kind.value}
tags: [{', '.join(record.tags)}]
data: {record.created_at}
contexto: {record.context}
decisao: {record.decision}
impacto: {record.impact}
fonte: {record.source.value}
projeto: {record.project}
confianca: {record.confidence}
---

# {record.title}

{record.summary}
"""
            tmp = fname + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(content)
            os.replace(tmp, fname)
        except Exception as e:
            print(f"[LearningEngine] markdown persist falhou: {e}")

    def record_metric(self, metric_name: str, value: float, context: Dict = None) -> MetricSample:
        sample = MetricSample(
            id=str(uuid.uuid4())[:12],
            metric_name=metric_name,
            value=value,
            context=context or {},
        )
        with self._lock:
            self.metrics.append(sample)
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
            self._save()
        return sample

    def detect_patterns(self) -> List[Dict[str, Any]]:
        """Detecta padrões recorrentes a partir das métricas."""
        patterns = []
        if not self.metrics:
            return patterns

        # Group metrics by name
        by_name = defaultdict(list)
        for m in self.metrics:
            by_name[m.metric_name].append(m)

        for name, samples in by_name.items():
            if len(samples) < 3:
                continue
            values = [s.value for s in samples]
            avg = sum(values) / len(values)
            trend = self._compute_trend(values)
            patterns.append({
                'metric': name,
                'samples': len(samples),
                'avg': round(avg, 3),
                'trend': trend,
                'first': samples[0].timestamp,
                'last': samples[-1].timestamp,
            })

        patterns.sort(key=lambda p: -p['samples'])
        return patterns[:20]

    def _compute_trend(self, values: List[float]) -> str:
        if len(values) < 3:
            return "insufficient_data"
        first_half = sum(values[:len(values)//2]) / max(1, len(values)//2)
        second_half = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)
        delta = second_half - first_half
        if delta > 0.05 * first_half:
            return "increasing"
        if delta < -0.05 * first_half:
            return "decreasing"
        return "stable"

    def auto_learn_from_tool(self, tool_name: str, duration_ms: float, success: bool,
                             error: str = "", tags: List[str] = None) -> Optional[LearningRecord]:
        """Aprende automaticamente a partir de uma execução de ferramenta."""
        self.record_metric(f"tool_{tool_name}_duration", duration_ms, {'success': success})

        # Registra padrão de sucesso/erro
        pattern_key = f"tool_{tool_name}_{'ok' if success else 'error'}"
        self.pattern_counts[pattern_key] += 1
        count = self.pattern_counts[pattern_key]

        # Aprende se erro recorrente ou operação lenta
        if not success and count >= 2:
            return self.learn(
                title=f"Falha recorrente em {tool_name}",
                summary=f"Tool {tool_name} falhou {count} vezes. Último erro: {error}",
                kind=LearningKind.ERRO,
                source=LearningSource.TOOL,
                tags=tags or ['tool', tool_name],
                context=f"Duration: {duration_ms:.0f}ms",
                decision="Investigar e corrigir falha recorrente",
                impact="Falhas recorrentes degradam confiabilidade",
                confidence=min(0.9, 0.5 + count * 0.1),
            )
        elif duration_ms > 5000 and success:
            return self.learn(
                title=f"Operação lenta: {tool_name}",
                summary=f"{tool_name} levou {duration_ms:.0f}ms (acima de 5s).",
                kind=LearningKind.MELHORIA,
                source=LearningSource.TOOL,
                tags=tags or ['performance', tool_name],
                context=f"Duration: {duration_ms:.0f}ms",
                decision="Otimizar ou paralelizar",
                impact="Latência alta impacta tempo total de tarefa",
                confidence=0.6,
            )
        return None

    def auto_learn_from_mission(self, mission_id: str, task_id: str, status: str,
                                result: str = "", learnings: List[str] = None) -> Optional[LearningRecord]:
        """Aprende automaticamente a partir de execução de missão."""
        if status in ('completed', 'failed'):
            return self.learn(
                title=f"Missão {mission_id} - {status}",
                summary=f"Task {task_id} {status}. {result}",
                kind=LearningKind.EPISODIO if status == 'completed' else LearningKind.ERRO,
                source=LearningSource.MISSION,
                tags=['mission', mission_id, status],
                context=f"Mission: {mission_id}, Task: {task_id}",
                decision=f"Task {task_id} concluída" if status == 'completed' else f"Task {task_id} falhou",
                impact=result[:200] if result else "",
                confidence=0.9 if status == 'completed' else 0.7,
                related=learnings or [],
            )
        return None

    def auto_learn_from_security(self, event_type: str, threat_level: str, source: str,
                                 description: str) -> LearningRecord:
        """Aprende automaticamente a partir de eventos de segurança."""
        return self.learn(
            title=f"Evento de segurança: {event_type}",
            summary=description,
            kind=LearningKind.ERRO if threat_level in ('high', 'critical') else LearningKind.EPISODIO,
            source=LearningSource.SECURITY,
            tags=['security', event_type, threat_level, source],
            context=f"Threat level: {threat_level}, Source: {source}",
            decision="Implementar mitigação ou monitorar",
            impact="Segurança do ecossistema",
            confidence=0.9,
        )

    def auto_learn_from_council(self, deliberation_id: str, topic: str, consensus: bool,
                                recommendation: str) -> LearningRecord:
        """Aprende automaticamente a partir de deliberações do conselho."""
        return self.learn(
            title=f"Deliberação: {topic[:80]}",
            summary=f"Consensus: {consensus}. {recommendation[:300]}",
            kind=LearningKind.DECISAO,
            source=LearningSource.COUNCIL,
            tags=['council', deliberation_id, 'consensus' if consensus else 'no-consensus'],
            context=f"Deliberation: {deliberation_id}",
            decision=recommendation[:200],
            impact="Decisão coletiva dos agentes",
            confidence=0.9 if consensus else 0.5,
        )

    def query(self, kind: LearningKind = None, tag: str = None, project: str = None,
              limit: int = 20, since: str = None) -> List[LearningRecord]:
        results = []
        for r in self.records.values():
            if kind and r.kind != kind:
                continue
            if tag and tag not in r.tags:
                continue
            if project and r.project != project:
                continue
            if since and r.created_at < since:
                continue
            results.append(r)
        results.sort(key=lambda r: (r.created_at, r.weight), reverse=True)
        return results[:limit]

    def get_insights(self, limit: int = 10) -> List[str]:
        """Gera insights acionáveis a partir dos aprendizados."""
        insights = []

        # Recorrentes (erros que se repetem)
        repeated_errors = {}
        for r in self.records.values():
            if r.kind == LearningKind.ERRO:
                key = r.title.split(' falhou')[0] if ' falhou' in r.title else r.title
                repeated_errors[key] = repeated_errors.get(key, 0) + 1
        for title, count in sorted(repeated_errors.items(), key=lambda x: -x[1])[:3]:
            insights.append(f"Erro recorrente: {title} ({count}x) - considere corrigir a causa raiz")

        # Padrões de métricas
        for p in self.detect_patterns()[:3]:
            insights.append(f"Tendência {p['trend']}: {p['metric']} média={p['avg']} ({p['samples']} amostras)")

        # Tags mais comuns
        top_tags = sorted(self.pattern_counts.items(), key=lambda x: -x[1])[:5]
        if top_tags:
            insights.append("Tags mais comuns: " + ", ".join(f"{t}({c})" for t, c in top_tags))

        return insights[:limit]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            by_kind = defaultdict(int)
            by_source = defaultdict(int)
            for r in self.records.values():
                by_kind[r.kind.value] += 1
                by_source[r.source.value] += 1
            return {
                'records': len(self.records),
                'metrics': len(self.metrics),
                'by_kind': dict(by_kind),
                'by_source': dict(by_source),
                'patterns': len(self.pattern_counts),
            }


engine = LearningEngine()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Learning Engine - Aprendizado contínuo')
    sub = parser.add_subparsers(dest='cmd')

    p_learn = sub.add_parser('learn')
    p_learn.add_argument('title')
    p_learn.add_argument('summary')
    p_learn.add_argument('kind', choices=[k.value for k in LearningKind])
    p_learn.add_argument('--source', choices=[s.value for s in LearningSource], default='manual')
    p_learn.add_argument('--tags', default='')
    p_learn.add_argument('--project', default='')
    p_learn.add_argument('--context', default='')
    p_learn.add_argument('--decision', default='')
    p_learn.add_argument('--impact', default='')
    p_learn.add_argument('--evidence', default='')
    p_learn.add_argument('--confidence', type=float, default=0.8)
    p_learn.add_argument('--no-memory', action='store_true')
    p_learn.add_argument('--no-markdown', action='store_true')

    p_metric = sub.add_parser('metric')
    p_metric.add_argument('name')
    p_metric.add_argument('value', type=float)
    p_metric.add_argument('--context', default='{}')

    p_query = sub.add_parser('query')
    p_query.add_argument('--kind', choices=[k.value for k in LearningKind])
    p_query.add_argument('--tag')
    p_query.add_argument('--project')
    p_query.add_argument('--limit', type=int, default=20)

    p_patterns = sub.add_parser('patterns')
    p_insights = sub.add_parser('insights')
    p_stats = sub.add_parser('stats')

    args = parser.parse_args()

    if args.cmd == 'learn':
        r = engine.learn(
            title=args.title,
            summary=args.summary,
            kind=LearningKind(args.kind),
            source=LearningSource(args.source),
            tags=args.tags.split(',') if args.tags else [],
            project=args.project,
            context=args.context,
            decision=args.decision,
            impact=args.impact,
            evidence_id=args.evidence,
            confidence=args.confidence,
            persist_memory=not args.no_memory,
            persist_markdown=not args.no_markdown,
        )
        print(f"Learned: {r.id} [{r.kind.value}] {r.title}")
        print(f"  Persisted to: KG, memory, markdown")

    elif args.cmd == 'metric':
        context = json.loads(args.context) if args.context else {}
        m = engine.record_metric(args.name, args.value, context)
        print(f"Metric recorded: {m.id} {m.metric_name}={m.value}")

    elif args.cmd == 'query':
        kind = LearningKind(args.kind) if args.kind else None
        results = engine.query(kind=kind, tag=args.tag, project=args.project, limit=args.limit)
        for r in results:
            print(f"{r.id} [{r.kind.value}|{r.source.value}] {r.title[:60]} conf={r.confidence}")

    elif args.cmd == 'patterns':
        for p in engine.detect_patterns():
            print(f"  {p['metric']}: samples={p['samples']}, avg={p['avg']}, trend={p['trend']}")

    elif args.cmd == 'insights':
        for insight in engine.get_insights():
            print(f"  • {insight}")

    elif args.cmd == 'stats':
        print(json.dumps(engine.stats(), indent=2, ensure_ascii=False))

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())