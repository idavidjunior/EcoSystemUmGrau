"""Source Registry — Catálogo de fontes de conhecimento técnico.

Carrega, busca e serve fontes do catálogo YAML para:
  - knowledge_graph: importa fontes como nodes com edges de proveniência
  - memory_engine: enriquece memórias com referências a fontes relevantes
  - auto_evolution / radar: sugere fontes para investigação

Princípios:
  - Fontes são pontos de partida, não verdade absoluta.
  - Qualidade = authority + evidence + reproducibility + freshness + relevance + utility.
  - Fail-soft: YAML ausente/corrompido não bloqueia ninguém.
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
CONFIG = os.path.join(BASE, 'config')
YAML_PATH = os.path.join(CONFIG, 'programming_sources.yaml')

sys.path.insert(0, SCRIPTS)


def _load_yaml(path: str = None) -> Dict[str, Any]:
    """Carrega o catálogo YAML. Fail-soft: retorna dict vazio em caso de erro."""
    path = path or YAML_PATH
    try:
        if not os.path.exists(path):
            return {'version': '0.0.0', 'sources': []}
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception:
        return {'version': '0.0.0', 'sources': []}


def _match_text(text: str, terms: List[str]) -> bool:
    """Verifica se TODOS os termos aparecem no texto (case-insensitive)."""
    lower = text.lower()
    return all(t.lower() in lower for t in terms)


def _reliability_sort_key(source: Dict) -> Tuple:
    """Chave de ordenação: reliability desc, depois authority_level (A>E)."""
    AUTH_ORDER = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    return (-source.get('reliability', 0), AUTH_ORDER.get(source.get('authority_level', 'E'), 5))


class SourceRegistry:
    """Registro em memória do catálogo de fontes."""

    def __init__(self, yaml_path: str = None):
        self._data = _load_yaml(yaml_path)
        self._sources: List[Dict] = self._data.get('sources', [])
        self._version = self._data.get('version', '0.0.0')
        # Índices para busca rápida
        self._by_id: Dict[str, Dict] = {}
        self._by_domain: Dict[str, List[Dict]] = {}
        self._by_authority: Dict[str, List[Dict]] = {}
        self._relevance_index: Dict[str, List[Dict]] = {}
        self._build_indexes()

    def _build_indexes(self):
        for s in self._sources:
            sid = s.get('id', '')
            if sid:
                self._by_id[sid] = s
            domain = s.get('domain', '').lower()
            if domain:
                self._by_domain.setdefault(domain, []).append(s)
            auth = s.get('authority_level', 'E')
            self._by_authority.setdefault(auth, []).append(s)
            for tag in s.get('relevance', []):
                self._relevance_index.setdefault(tag.lower(), []).append(s)

    @property
    def version(self) -> str:
        return self._version

    @property
    def count(self) -> int:
        return len(self._sources)

    def get_by_id(self, source_id: str) -> Optional[Dict]:
        """Busca fonte por ID exato."""
        return self._by_id.get(source_id)

    def get_by_domain(self, domain: str) -> List[Dict]:
        """Retorna todas as fontes de um domínio (ex: 'python', 'rust', 'devops')."""
        return list(self._by_domain.get(domain.lower(), []))

    def get_by_authority(self, level: str) -> List[Dict]:
        """Retorna fontes de um nível de autoridade (A-E)."""
        return list(self._by_authority.get(level.upper(), []))

    def search(
        self,
        query: str = None,
        domain: str = None,
        authority_level: str = None,
        tags: List[str] = None,
        category: str = None,
        min_reliability: float = 0.0,
        limit: int = 20,
    ) -> List[Dict]:
        """Busca flexível no catálogo.

        Combina filtros com AND. Resultados ordenados por reliability desc.
        """
        results = list(self._sources)

        if domain:
            results = [s for s in results if s.get('domain', '').lower() == domain.lower()]

        if authority_level:
            al = authority_level.upper()
            results = [s for s in results if s.get('authority_level', '') == al]

        if category:
            results = [s for s in results if s.get('category', '').upper() == category.upper()]

        if min_reliability > 0:
            results = [s for s in results if s.get('reliability', 0) >= min_reliability]

        if tags:
            def _has_all_tags(s):
                src_tags = {t.lower() for t in s.get('relevance', [])}
                return all(t.lower() in src_tags for t in tags)
            results = [s for s in results if _has_all_tags(s)]

        if query:
            terms = query.lower().split()
            results = [s for s in results if _match_text(
                f"{s.get('name', '')} {s.get('description', '')} "
                f"{' '.join(s.get('relevance', []))} {s.get('domain', '')}",
                terms
            )]

        results.sort(key=_reliability_sort_key)
        return results[:limit]

    def get_relevant_sources(self, topic: str, limit: int = 5) -> List[Dict]:
        """Dado um tópico livre, retorna as fontes mais relevantes.

        Usa matching de tags + domínio + texto livre.
        """
        topic_lower = topic.lower()
        words = topic_lower.split()
        domain_words = set()
        for w in words:
            domain_words.add(w)
            domain_words.add(w.rstrip('s'))

        # Tentar匹配 por tags de relevância primeiro
        tag_hits: Dict[str, int] = {}
        for tag, sources in self._relevance_index.items():
            if tag in topic_lower or topic_lower in tag:
                for s in sources:
                    sid = s.get('id', '')
                    tag_hits[sid] = tag_hits.get(sid, 0) + 1

        # Matching por domínio. Usa fronteira de palavra para não casar
        # domínios curtos como 'c' como substring de qualquer token ('database').
        for domain, sources in self._by_domain.items():
            if domain in domain_words:
                for s in sources:
                    sid = s.get('id', '')
                    tag_hits[sid] = tag_hits.get(sid, 0) + 2  # domínio tem peso maior

        # Matching por texto livre no nome/descrição.
        # Penaliza fontes de domínio "genérico" (c, general, git, vim) que casam
        # apenas por palavra solta (ex.: 'memory', 'security'), evitando ruído
        # quando o tópico não é daquele domínio.
        GENERIC_DOMAINS = {'c', 'general', 'git', 'vim', 'embedded'}
        for s in self._sources:
            text = f"{s.get('name', '')} {s.get('description', '')}".lower()
            matches = sum(1 for w in words if len(w) > 2 and w in text)
            if matches > 0:
                sid = s.get('id', '')
                weight = matches
                # Domínio genérico só pontua se o tópico claramente o mencionar.
                if s.get('domain', '').lower() in GENERIC_DOMAINS:
                    weight = matches if any(w in topic_lower for w in (s.get('domain', '').lower(), 'c programming')) else 0
                if weight > 0:
                    tag_hits[sid] = tag_hits.get(sid, 0) + weight

        # Ordenar por hits, depois reliability
        scored = []
        for sid, hits in tag_hits.items():
            src = self._by_id.get(sid)
            if src:
                scored.append((hits, src.get('reliability', 0), src))

        scored.sort(key=lambda x: (-x[0], -x[1]))
        return [s[2] for s in scored[:limit]]

    def get_top_authority(self, domain: str = None, limit: int = 10) -> List[Dict]:
        """Retorna as fontes de maior autoridade (A e B), opcionalmente filtrando por domínio."""
        results = self._sources
        if domain:
            results = [s for s in results if s.get('domain', '').lower() == domain.lower()]
        results = [s for s in results if s.get('authority_level', '') in ('A', 'B')]
        results.sort(key=_reliability_sort_key)
        return results[:limit]

    def import_to_knowledge_graph(self, kg, domains: List[str] = None) -> int:
        """Importa fontes como nodes no KnowledgeGraph.

        Cria nodes do tipo TECHNOLOGY com propriedades de fonte,
        e edges RELATES_TO entre fontes do mesmo domínio.

        Retorna o número de nodes importados.
        """
        from knowledge_graph import NodeType, EdgeType

        sources = self._sources
        if domains:
            sources = [s for s in sources if s.get('domain', '').lower() in [d.lower() for d in domains]]

        imported = 0
        domain_nodes: Dict[str, str] = {}  # domain -> node_id

        for s in sources:
            node_name = f"fonte:{s.get('id', '')}"
            properties = {
                'source_url': s.get('url', ''),
                'source_type': s.get('source_type', ''),
                'authority_level': s.get('authority_level', ''),
                'evidence_level': s.get('evidence_level', ''),
                'reliability': s.get('reliability', 0),
                'category': s.get('category', ''),
                'country': s.get('country', ''),
                'language': s.get('language', ''),
                'description': s.get('description', ''),
                'status': s.get('status', 'seed'),
            }
            tags = [s.get('domain', '')] + s.get('relevance', [])

            node = kg.add_node(
                type=NodeType.TECHNOLOGY,
                name=node_name,
                properties=properties,
                tags=tags,
                source='source_registry',
                confidence=s.get('reliability', 0.5),
            )
            imported += 1

            # Criar edge de domínio se ainda não existe
            domain = s.get('domain', '').lower()
            if domain and domain not in domain_nodes:
                domain_node = kg.add_node(
                    type=NodeType.CONCEPT,
                    name=f"dominio:{domain}",
                    properties={'type': 'programming_domain'},
                    tags=[domain],
                    source='source_registry',
                )
                domain_nodes[domain] = domain_node.id

            # Edge BELONGS_TO domínio
            if domain and domain in domain_nodes:
                kg.add_edge(
                    source_id=node.id,
                    target_id=domain_nodes[domain],
                    type=EdgeType.BELONGS_TO,
                    source='source_registry',
                    confidence=0.9,
                )

        return imported

    def enrich_memory_metadata(self, topic: str) -> Dict[str, Any]:
        """Retorna metadados de fontes relevantes para enriquecer uma memória.

        Retorna dict com:
          - source_refs: lista de {id, name, url, authority_level, reliability}
          - recommended_for_verification: True se existem fontes A/B para o tópico
          - domain: domínio detectado
        """
        relevant = self.get_relevant_sources(topic, limit=3)
        source_refs = []
        for s in relevant:
            source_refs.append({
                'id': s.get('id', ''),
                'name': s.get('name', ''),
                'url': s.get('url', ''),
                'authority_level': s.get('authority_level', ''),
                'reliability': s.get('reliability', 0),
            })

        has_authority = any(s.get('authority_level') in ('A', 'B') for s in relevant)

        # Detectar domínio
        domain = None
        for s in relevant:
            d = s.get('domain', '')
            if d:
                domain = d
                break

        return {
            'source_refs': source_refs,
            'recommended_for_verification': has_authority,
            'domain': domain,
        }

    def stats(self) -> Dict[str, Any]:
        """Estatísticas do catálogo."""
        domains = {}
        authorities = {}
        statuses = {}
        for s in self._sources:
            d = s.get('domain', '?')
            domains[d] = domains.get(d, 0) + 1
            a = s.get('authority_level', '?')
            authorities[a] = authorities.get(a, 0) + 1
            st = s.get('status', '?')
            statuses[st] = statuses.get(st, 0) + 1

        return {
            'version': self._version,
            'total': len(self._sources),
            'domains': domains,
            'authorities': authorities,
            'statuses': statuses,
        }


def main():
    """CLI simples para consultas ao catálogo."""
    import argparse
    parser = argparse.ArgumentParser(description='Source Registry — consulta ao catálogo de fontes')
    sub = parser.add_subparsers(dest='cmd')

    p_stats = sub.add_parser('stats', help='Estatísticas do catálogo')

    p_search = sub.add_parser('search', help='Buscar fontes')
    p_search.add_argument('query', nargs='?', default='', help='Termo de busca')
    p_search.add_argument('--domain', default=None, help='Filtrar por domínio')
    p_search.add_argument('--authority', default=None, help='Filtrar por autoridade (A-E)')
    p_search.add_argument('--limit', type=int, default=10, help='Limite de resultados')

    p_top = sub.add_parser('top', help='Top fontes por autoridade')
    p_top.add_argument('--domain', default=None, help='Domínio')
    p_top.add_argument('--limit', type=int, default=10, help='Limite')

    p_relevant = sub.add_parser('relevant', help='Fontes relevantes para um tópico')
    p_relevant.add_argument('topic', help='Tópico livre')
    p_relevant.add_argument('--limit', type=int, default=5, help='Limite')

    p_list_domains = sub.add_parser('domains', help='Listar domínios disponíveis')

    args = parser.parse_args()
    reg = SourceRegistry()

    if args.cmd == 'stats':
        st = reg.stats()
        print(f"Source Registry v{st['version']} — {st['total']} fontes")
        print(f"Domínios: {', '.join(f'{k}({v})' for k, v in sorted(st['domains'].items(), key=lambda x: -x[1]))}")
        print(f"Autoridade: {', '.join(f'{k}={v}' for k, v in sorted(st['authorities'].items()))}")
        print(f"Status: {', '.join(f'{k}={v}' for k, v in sorted(st['statuses'].items()))}")

    elif args.cmd == 'search':
        results = reg.search(query=args.query, domain=args.domain,
                              authority_level=args.authority, limit=args.limit)
        if not results:
            print("Nenhuma fonte encontrada.")
        for s in results:
            print(f"  [{s.get('authority_level')}] {s.get('id')} — {s.get('name')} "
                  f"({s.get('domain')}, rel={s.get('reliability', 0):.2f})")

    elif args.cmd == 'top':
        results = reg.get_top_authority(domain=args.domain, limit=args.limit)
        for s in results:
            print(f"  [{s.get('authority_level')}] {s.get('id')} — {s.get('name')} "
                  f"({s.get('domain')}, rel={s.get('reliability', 0):.2f})")

    elif args.cmd == 'relevant':
        results = reg.get_relevant_sources(args.topic, limit=args.limit)
        if not results:
            print("Nenhuma fonte relevante encontrada.")
        for s in results:
            print(f"  [{s.get('authority_level')}] {s.get('id')} — {s.get('name')} "
                  f"({s.get('domain')}, rel={s.get('reliability', 0):.2f})")

    elif args.cmd == 'domains':
        domains = sorted(set(s.get('domain', '?') for s in reg._sources))
        print(f"Domínios ({len(domains)}): {', '.join(domains)}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
