"""Knowledge Graph - Memória relacional estruturada para o Ecossistema.

Substitui arquivos planos por grafo de conhecimento com:
- Entidades (nodes) com tipos e propriedades
- Relacionamentos (edges) tipados e direcionados
- Consultas em linguagem natural → Cypher-like
- Índices semânticos e textuais
- Versionamento e proveniência
- Integração com memory_engine existente
"""

import os
import sys
import json
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME_DIR = os.path.join(BASE, 'runtime')
KG_DIR = os.path.join(RUNTIME_DIR, 'knowledge_graph')
sys.path.insert(0, SCRIPTS)


class NodeType(Enum):
    CONCEPT = "concept"
    PROJECT = "project"
    TASK = "task"
    DECISION = "decision"
    PATTERN = "pattern"
    TOOL = "tool"
    AGENT = "agent"
    FILE = "file"
    PERSON = "person"
    TECHNOLOGY = "technology"
    ERROR = "error"
    SOLUTION = "solution"


class EdgeType(Enum):
    RELATES_TO = "relates_to"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    CAUSED_BY = "caused_by"
    SOLVES = "solves"
    IMPLEMENTS = "implements"
    USES = "uses"
    CREATED_BY = "created_by"
    MODIFIED_BY = "modified_by"
    REFERENCES = "references"
    CONTRADICTS = "contradicts"
    EVOLVES_FROM = "evolves_from"
    TAGGED_WITH = "tagged_with"
    BELONGS_TO = "belongs_to"


@dataclass
class KGNode:
    id: str
    type: NodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    version: int = 1
    source: str = "manual"  # manual, auto, imported
    confidence: float = 1.0


@dataclass
class KGEdge:
    id: str
    source_id: str
    target_id: str
    type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    source: str = "manual"
    confidence: float = 1.0


@dataclass
class KGQueryResult:
    nodes: List[KGNode]
    edges: List[KGEdge]
    paths: List[List[str]] = field(default_factory=list)


class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, KGNode] = {}
        self.edges: Dict[str, KGEdge] = {}
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self.node_index: Dict[str, Set[str]] = defaultdict(set)  # type -> node_ids
        self.name_index: Dict[str, Set[str]] = defaultdict(set)  # lowercase name -> node_ids
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> node_ids
        self.edge_index: Dict[str, List[str]] = defaultdict(list)  # edge_type -> edge_ids
        self._lock = threading.RLock()
        self._load()

    def _get_storage_paths(self):
        return {
            'nodes': os.path.join(KG_DIR, 'nodes.json'),
            'edges': os.path.join(KG_DIR, 'edges.json'),
            'meta': os.path.join(KG_DIR, 'meta.json'),
        }

    def _ensure_dirs(self):
        os.makedirs(KG_DIR, exist_ok=True)

    def _load(self):
        self._ensure_dirs()
        paths = self._get_storage_paths()
        try:
            if os.path.exists(paths['nodes']):
                with open(paths['nodes'], encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    node = KGNode(
                        id=item['id'],
                        type=NodeType(item['type']),
                        name=item['name'],
                        properties=item.get('properties', {}),
                        tags=item.get('tags', []),
                        created_at=item.get('created_at', ''),
                        updated_at=item.get('updated_at', ''),
                        version=item.get('version', 1),
                        source=item.get('source', 'manual'),
                        confidence=item.get('confidence', 1.0),
                    )
                    self._add_node_internal(node)
            if os.path.exists(paths['edges']):
                with open(paths['edges'], encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    edge = KGEdge(
                        id=item['id'],
                        source_id=item['source_id'],
                        target_id=item['target_id'],
                        type=EdgeType(item['type']),
                        properties=item.get('properties', {}),
                        weight=item.get('weight', 1.0),
                        created_at=item.get('created_at', ''),
                        source=item.get('source', 'manual'),
                        confidence=item.get('confidence', 1.0),
                    )
                    self._add_edge_internal(edge)
        except Exception as e:
            print(f"[KG] Erro ao carregar: {e}")

    def _save(self):
        self._ensure_dirs()
        paths = self._get_storage_paths()
        try:
            tmp_nodes = paths['nodes'] + '.tmp'
            tmp_edges = paths['edges'] + '.tmp'
            nodes_data = []
            for n in self.nodes.values():
                d = asdict(n)
                d['type'] = n.type.value
                nodes_data.append(d)
            edges_data = []
            for e in self.edges.values():
                d = asdict(e)
                d['type'] = e.type.value
                edges_data.append(d)
            with open(tmp_nodes, 'w', encoding='utf-8') as f:
                json.dump(nodes_data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_nodes, paths['nodes'])
            with open(tmp_edges, 'w', encoding='utf-8') as f:
                json.dump(edges_data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_edges, paths['edges'])
            meta = {
                'updated_at': datetime.now().isoformat(timespec='seconds'),
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
            }
            with open(paths['meta'], 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[KG] Erro ao salvar: {e}")

    def _add_node_internal(self, node: KGNode):
        self.nodes[node.id] = node
        self.node_index[node.type.value].add(node.id)
        self.name_index[node.name.lower()].add(node.id)
        for tag in node.tags:
            self.tag_index[tag.lower()].add(node.id)

    def _add_edge_internal(self, edge: KGEdge):
        self.edges[edge.id] = edge
        self.adjacency[edge.source_id].append(edge.target_id)
        self.reverse_adjacency[edge.target_id].append(edge.source_id)
        self.edge_index[edge.type.value].append(edge.id)

    def _remove_node_internal(self, node_id: str):
        node = self.nodes.pop(node_id, None)
        if node:
            self.node_index[node.type.value].discard(node_id)
            self.name_index[node.name.lower()].discard(node_id)
            for tag in node.tags:
                self.tag_index[tag.lower()].discard(node_id)
            for target in self.adjacency.pop(node_id, []):
                self.reverse_adjacency[target].remove(node_id)
            for source in self.reverse_adjacency.pop(node_id, []):
                self.adjacency[source].remove(node_id)
            edges_to_remove = []
            for eid, edge in self.edges.items():
                if edge.source_id == node_id or edge.target_id == node_id:
                    edges_to_remove.append(eid)
            for eid in edges_to_remove:
                self._remove_edge_internal(eid)

    def _remove_edge_internal(self, edge_id: str):
        edge = self.edges.pop(edge_id, None)
        if edge:
            self.adjacency[edge.source_id].remove(edge.target_id)
            self.reverse_adjacency[edge.target_id].remove(edge.source_id)
            self.edge_index[edge.type.value].remove(edge_id)

    def add_node(
        self,
        type: NodeType,
        name: str,
        properties: Dict[str, Any] = None,
        tags: List[str] = None,
        source: str = "manual",
        confidence: float = 1.0,
        node_id: str = None,
        created_at: str = None,
    ) -> KGNode:
        with self._lock:
            node_id = node_id or str(uuid.uuid4())[:12]
            existing = self.find_by_name(name)
            if existing:
                node = existing[0]
                node.properties.update(properties or {})
                node.tags = list(set(node.tags + (tags or [])))
                node.updated_at = datetime.now().isoformat(timespec='seconds')
                node.version += 1
                self._save()
                return node
            node = KGNode(
                id=node_id,
                type=type,
                name=name,
                properties=properties or {},
                tags=tags or [],
                source=source,
                confidence=confidence,
                created_at=created_at or datetime.now().isoformat(timespec='seconds'),
            )
            self._add_node_internal(node)
            self._save()
            return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        type: EdgeType,
        properties: Dict[str, Any] = None,
        weight: float = 1.0,
        source: str = "manual",
        confidence: float = 1.0,
        edge_id: str = None,
    ) -> Optional[KGEdge]:
        with self._lock:
            if source_id not in self.nodes or target_id not in self.nodes:
                return None
            for eid, edge in self.edges.items():
                if edge.source_id == source_id and edge.target_id == target_id and edge.type == type:
                    edge.properties.update(properties or {})
                    edge.weight = weight
                    edge.confidence = confidence
                    self._save()
                    return edge
            edge_id = edge_id or str(uuid.uuid4())[:12]
            edge = KGEdge(
                id=edge_id,
                source_id=source_id,
                target_id=target_id,
                type=type,
                properties=properties or {},
                weight=weight,
                source=source,
                confidence=confidence,
            )
            self._add_edge_internal(edge)
            self._save()
            return edge

    def get_node(self, node_id: str) -> Optional[KGNode]:
        return self.nodes.get(node_id)

    def find_by_name(self, name: str, exact: bool = False) -> List[KGNode]:
        name_lower = name.lower()
        if exact:
            ids = self.name_index.get(name_lower, set())
        else:
            ids = set()
            for indexed_name, node_ids in self.name_index.items():
                if name_lower in indexed_name:
                    ids.update(node_ids)
        return [self.nodes[i] for i in ids if i in self.nodes]

    def find_by_type(self, type: NodeType) -> List[KGNode]:
        return [self.nodes[i] for i in self.node_index.get(type.value, set()) if i in self.nodes]

    def find_by_tag(self, tag: str) -> List[KGNode]:
        return [self.nodes[i] for i in self.tag_index.get(tag.lower(), set()) if i in self.nodes]

    def get_neighbors(self, node_id: str, edge_type: EdgeType = None, direction: str = "out") -> List[KGNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        if direction == "out":
            neighbor_ids = self.adjacency.get(node_id, [])
        elif direction == "in":
            neighbor_ids = self.reverse_adjacency.get(node_id, [])
        else:
            neighbor_ids = list(set(self.adjacency.get(node_id, []) + self.reverse_adjacency.get(node_id, [])))
        if edge_type:
            filtered = []
            for nid in neighbor_ids:
                for eid in self.edge_index.get(edge_type.value, []):
                    edge = self.edges.get(eid)
                    if edge and ((edge.source_id == node_id and edge.target_id == nid) or
                                 (edge.target_id == node_id and edge.source_id == nid)):
                        filtered.append(nid)
                        break
            neighbor_ids = filtered
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def get_edges_between(self, source_id: str, target_id: str) -> List[KGEdge]:
        result = []
        for eid in self.edge_index.get('relates_to', []):
            edge = self.edges.get(eid)
            if edge and edge.source_id == source_id and edge.target_id == target_id:
                result.append(edge)
        return result

    def query(
        self,
        node_type: NodeType = None,
        name_contains: str = None,
        tags: List[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> List[KGNode]:
        candidates = set(self.nodes.keys())
        if node_type:
            candidates &= self.node_index.get(node_type.value, set())
        if name_contains:
            name_matches = set()
            for indexed_name, node_ids in self.name_index.items():
                if name_contains.lower() in indexed_name:
                    name_matches.update(node_ids)
            candidates &= name_matches
        if tags:
            for tag in tags:
                candidates &= self.tag_index.get(tag.lower(), set())
        results = []
        for nid in candidates:
            node = self.nodes.get(nid)
            if node and node.confidence >= min_confidence:
                results.append(node)
        results.sort(key=lambda n: (-n.confidence, n.updated_at), reverse=True)
        return results[:limit]

    def search(self, query: str, limit: int = 20) -> KGQueryResult:
        tokens = [t for t in query.lower().split() if len(t) > 2]
        node_scores = defaultdict(float)
        for token in tokens:
            for name, ids in self.name_index.items():
                if token in name:
                    for nid in ids:
                        node_scores[nid] += 2.0
            for tag, ids in self.tag_index.items():
                if token in tag:
                    for nid in ids:
                        node_scores[nid] += 1.5
            for nid, node in self.nodes.items():
                for key, value in node.properties.items():
                    if token in str(value).lower():
                        node_scores[nid] += 1.0
        top_ids = sorted(node_scores.keys(), key=lambda x: -node_scores[x])[:limit]
        nodes = [self.nodes[nid] for nid in top_ids if nid in self.nodes]
        edges = []
        for node in nodes:
            for neighbor_id in self.adjacency.get(node.id, []):
                if neighbor_id in top_ids:
                    for eid in self.edge_index.get('relates_to', []):
                        edge = self.edges.get(eid)
                        if edge and edge.source_id == node.id and edge.target_id == neighbor_id:
                            edges.append(edge)
                            break
        return KGQueryResult(nodes=nodes, edges=edges)

    def suggest_sources(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Sugere fontes autoritativas relevantes para uma consulta.

        Usa o source_registry para levantar pontos de partida confiáveis,
        complementando os nodes do grafo. Fail-soft: sem registry disponível,
        retorna lista vazia (a busca do grafo continua funcionando).
        """
        try:
            from source_registry import SourceRegistry
            reg = SourceRegistry()
            sources = reg.get_relevant_sources(query, limit=limit)
            return [
                {
                    'id': s.get('id', ''),
                    'name': s.get('name', ''),
                    'url': s.get('url', ''),
                    'authority_level': s.get('authority_level', ''),
                    'reliability': s.get('reliability', 0),
                    'domain': s.get('domain', ''),
                }
                for s in sources
            ]
        except Exception:
            return []



    def shortest_path(self, source_id: str, target_id: str, max_depth: int = 4) -> List[List[str]]:
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        from collections import deque
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        paths = []
        while queue and len(paths) < 10:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            if current == target_id:
                paths.append(path)
                continue
            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return paths

    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> KGQueryResult:
        all_ids = set(node_ids)
        current_ids = set(node_ids)
        for _ in range(depth):
            next_ids = set()
            for nid in current_ids:
                next_ids.update(self.adjacency.get(nid, []))
                next_ids.update(self.reverse_adjacency.get(nid, []))
            all_ids.update(next_ids)
            current_ids = next_ids
        nodes = [self.nodes[nid] for nid in all_ids if nid in self.nodes]
        edges = []
        for eid, edge in self.edges.items():
            if edge.source_id in all_ids and edge.target_id in all_ids:
                edges.append(edge)
        return KGQueryResult(nodes=nodes, edges=edges)

    def import_from_memory_engine(self) -> int:
        try:
            import memory_engine
            memories = memory_engine.query(limit=500)
            count = 0
            type_map = {
                'decisao': NodeType.DECISION,
                'padrao': NodeType.PATTERN,
                'erro': NodeType.ERROR,
                'episodio': NodeType.CONCEPT,
                'preferencia': NodeType.CONCEPT,
                'tarefa': NodeType.TASK,
                'projeto': NodeType.PROJECT,
            }
            for m in memories:
                kind = m.get('kind', 'concept')
                node_type = type_map.get(kind, NodeType.CONCEPT)
                node = self.add_node(
                    type=node_type,
                    name=m.get('task', 'Sem título')[:100],
                    properties={
                        'summary': m.get('summary', ''),
                        'project': m.get('project', ''),
                        'memory_id': m.get('id', ''),
                    },
                    tags=m.get('tags', []),
                    source='memory_engine',
                    confidence=0.8,
                    node_id=f"mem_{m.get('id', '')}",
                )
                count += 1
            return count
        except Exception as e:
            print(f"[KG] Erro ao importar de memory_engine: {e}")
            return 0

    def export_to_json(self) -> Dict[str, Any]:
        return {
            'nodes': [asdict(n) for n in self.nodes.values()],
            'edges': [asdict(e) for e in self.edges.values()],
            'stats': {
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
                'types': {t.value: len(ids) for t, ids in self.node_index.items()},
            },
        }

    def stats(self) -> Dict[str, Any]:
        return {
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'node_types': {k: len(v) for k, v in self.node_index.items()},
            'edge_types': {k: len(v) for k, v in self.edge_index.items()},
            'tags': len(self.tag_index),
        }


kg = KnowledgeGraph()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Knowledge Graph CLI')
    sub = parser.add_subparsers(dest='cmd')

    p_add_node = sub.add_parser('add-node')
    p_add_node.add_argument('type', choices=[t.value for t in NodeType])
    p_add_node.add_argument('name')
    p_add_node.add_argument('--props', default='{}')
    p_add_node.add_argument('--tags', default='')
    p_add_node.add_argument('--source', default='manual')

    p_add_edge = sub.add_parser('add-edge')
    p_add_edge.add_argument('source')
    p_add_edge.add_argument('target')
    p_add_edge.add_argument('type', choices=[t.value for t in EdgeType])
    p_add_edge.add_argument('--props', default='{}')
    p_add_edge.add_argument('--weight', type=float, default=1.0)

    p_find = sub.add_parser('find')
    p_find.add_argument('query')
    p_find.add_argument('--type', default=None)
    p_find.add_argument('--tags', default='')
    p_find.add_argument('--limit', type=int, default=20)

    p_search = sub.add_parser('search')
    p_search.add_argument('query')
    p_search.add_argument('--limit', type=int, default=20)

    p_neighbors = sub.add_parser('neighbors')
    p_neighbors.add_argument('node_id')
    p_neighbors.add_argument('--type', default=None)
    p_neighbors.add_argument('--direction', choices=['out', 'in', 'both'], default='out')

    p_path = sub.add_parser('path')
    p_path.add_argument('source')
    p_path.add_argument('target')
    p_path.add_argument('--max-depth', type=int, default=4)

    p_import = sub.add_parser('import-memories')
    p_stats = sub.add_parser('stats')
    p_export = sub.add_parser('export')
    p_export.add_argument('output')

    args = parser.parse_args()

    if args.cmd == 'add-node':
        node = kg.add_node(
            type=NodeType(args.type),
            name=args.name,
            properties=json.loads(args.props),
            tags=args.tags.split(',') if args.tags else [],
            source=args.source,
        )
        print(f"Created node: {node.id} ({node.type.value}) {node.name}")

    elif args.cmd == 'add-edge':
        edge = kg.add_edge(
            source_id=args.source,
            target_id=args.target,
            type=EdgeType(args.type),
            properties=json.loads(args.props),
            weight=args.weight,
        )
        if edge:
            print(f"Created edge: {edge.id} {args.source} -[{args.type}]-> {args.target}")
        else:
            print("Failed: source or target not found")

    elif args.cmd == 'find':
        tags = args.tags.split(',') if args.tags else None
        node_type = NodeType(args.type) if args.type else None
        results = kg.query(node_type=node_type, name_contains=args.query, tags=tags, limit=args.limit)
        for n in results:
            print(f"  {n.id} [{n.type.value}] {n.name} (conf={n.confidence}) tags={n.tags}")

    elif args.cmd == 'search':
        result = kg.search(args.query, args.limit)
        print(f"Nodes ({len(result.nodes)}):")
        for n in result.nodes:
            print(f"  {n.id} [{n.type.value}] {n.name}")
        print(f"Edges ({len(result.edges)}):")
        for e in result.edges:
            print(f"  {e.source_id} -[{e.type.value}]-> {e.target_id}")

    elif args.cmd == 'neighbors':
        edge_type = EdgeType(args.type) if args.type else None
        neighbors = kg.get_neighbors(args.node_id, edge_type, args.direction)
        for n in neighbors:
            print(f"  {n.id} [{n.type.value}] {n.name}")

    elif args.cmd == 'path':
        paths = kg.shortest_path(args.source, args.target, args.max_depth)
        for i, path in enumerate(paths):
            print(f"Path {i+1}: {' -> '.join(path)}")

    elif args.cmd == 'import-memories':
        count = kg.import_from_memory_engine()
        print(f"Imported {count} memories from memory_engine")

    elif args.cmd == 'stats':
        print(json.dumps(kg.stats(), indent=2, ensure_ascii=False))

    elif args.cmd == 'export':
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(kg.export_to_json(), f, ensure_ascii=False, indent=2)
        print(f"Exported to {args.output}")

    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())