# -*- coding: utf-8 -*-
"""cluster_mapper.py — Mapeamento poderoso de notas/nós para clusters.

Em vez de um dict estático CLUSTERS + match exato, este módulo implementa um
algoritmo que:

APRENDE
  1. Normaliza e "dedup" tags/fontes (colapso de underscore, duplicatas
     concatenadas pelo slugify/RAKE, variações de caixa/pontuação).
  2. Constrói um perfil por cluster: palavras-chave e co-ocorrências reais
     observadas nas notas de cada cluster (categoria, fontes, nomes).
  3. Detecta sinônimos/variantes: se duas tags aparecem sempre juntas na mesma
     nota de um cluster, vira candidato de associação.

OUSSA
  4. Se uma tag/fonte não casa com o mapeamento explícito, tenta associação
     aprendida (co-ocorrência com notas já mapeadas) e só então 'geral'.
  5. Sugere clusters novos: se um grupo de fontes distintas aparece sempre
     junto e não pertence a nenhum cluster conhecido, propõe um novo cluster
     (relatório, sem alterar a base sozinho — o algoritmo "ousa" mas reporta).

O mapeamento aprendido pode ser persistido (JSON) e reutilizado, tornando o
sistema melhor a cada execução (memória de mapeamento).

API:
  mapper = ClusterMapper()
  mapper.treinar(notas)              # notas: list[dict(slug, tags, categoria, cluster_bruto, fontes)]
  cl = mapper.resolver(tags, fontes) # -> 'android' | 'ler' | ... | 'geral'
  mapper.exportar_aprendizado()      # dict serializável
  mapper.carregar_aprendizado(d)
"""

import os
import re
import json
from collections import Counter, defaultdict

# Palavras-chave genéricas de categoria/emoção que NÃO são fonte de projeto.
GENERIC = frozenset({
    'padrao', 'decisao', 'bug', 'cognitivo', 'heuristica', 'framework',
    'missao', 'hub', 'geral', 'general', 'episodio', 'fonte', 'status',
    'projeto', 'sdk', 'app', 'grafo', 'widget', 'erro', 'resolucao',
    'dominio', 'nativo', 'pure', 'scan', 'proativo', 'scan proativo',
    '2026 scan proativo', '2026', 'aprendizado', 'learning', 'labels',
})


def norm(s):
    """Normaliza fonte/tag: minúsculas, sem pontuação/espaços."""
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def dedupe(norm_s):
    """Se a string normalizada é repetição de si mesma (ex: 'xx' -> 'x',
    'androidpuresdkandroidpuresdk'), reduz para a forma mínima."""
    n = len(norm_s)
    for k in range(1, n // 2 + 1):
        if n % k == 0 and norm_s == norm_s[:k] * (n // k):
            return norm_s[:k]
    return norm_s


class ClusterMapper:
    """Algoritmo de mapeamento nota/nó -> cluster, com aprendizado."""

    # clusters "conhecidos de antemão" (semântica do ecossistema)
    CLUSTERS = {
        'android': ['android-pure-sdk', 'android_pure_sdk', 'androidpuresdk',
                    'android-pure-sdkandroid-pure-sdk', 'androidpure', 'pure sdk'],
        'mp3player': ['mp3player', 'mp3player-metadata-rescue',
                      'mp3player-metadata-rescuemp3player-metadata-rescue',
                      'metadata', 'rescue', 'musicbrainz', 'itunes'],
        'ler': ['ler', 'ler_arquitetura', 'ler_auditoria', 'ler_memory',
                'ler_aprendizado', 'lerarquitetura', 'lerauditoria',
                'leraprendizado', 'lerler', 'learning'],
        'navegacao': ['treinamento_navegacao', 'treinamentonavegacao',
                      'session', 'sessionsession', 'navegacao', 'web_navigation',
                      'web-navigation'],
        'ecossistema': ['ecossistema-opencode', 'ecosistema-opencode',
                        'opencode', 'sessao_seguranca', 'sessao_servermanager',
                        'sessao_rustdesk', 'sessao_providermanager',
                        'sessao_migracao_config', 'sessao_limpeza_auth',
                        'sessao_seguranca', 'provider_mcp_debug',
                        'provider_mcp_server', 'provider_mcp_server.py',
                        'provider_mcp_server.py:52-55', 'workspace_organization',
                        'sessaoseguranca', 'sessaoservermanager', 'sessaorustdesk',
                        'sessaoprovidermanager', 'sessaomigracaoconfig',
                        'sessaolimpezaauth', 'providermcpdebug', 'providermcpserver',
                        'workspaceorganization', 'mcp', 'ecossistema',
                        'ecosystemumgrau', 'ecosystem', 'jarvis', 'config',
                        'habilidades', 'skill', 'opencodeopencode'],
        'cognicao': ['meta_cognition', 'metacognicao', 'metacognition'],
    }

    def __init__(self, extra_clusters=None):
        self.clusters = {k: list(v) for k, v in self.CLUSTERS.items()}
        if extra_clusters:
            for k, v in extra_clusters.items():
                self.clusters.setdefault(k, []).extend(v if isinstance(v, list) else [v])

        # índice normalizado: norm(fonte) -> cluster
        self._norm_idx = {}
        for cl, fontes in self.clusters.items():
            for f in fontes:
                n = dedupe(norm(f))
                if n:
                    self._norm_idx[n] = cl

        # aprendizado: palavra/fonte normalizada -> contador de clusters onde aparece
        self._aprendizado = defaultdict(Counter)
        # co-ocorrência: par de fontes na mesma nota -> contagem (para sugerir)
        self._cooc = defaultdict(Counter)
        self._fontes = Counter()   # fonte bruta -> n de notas
        self._notas_treino = 0
        self._sugestoes = {}

    # ------------------------------------------------------------------
    def treinar(self, notas):
        """Aprende associações a partir das notas reais.

        notas: iterable de dicts com chaves:
          - tags: list[str] (tags do frontmatter)
          - fonte: str (source bruta, opcional)
          - categoria: str (categoria da nota, ex 'bugs')
          - cl_bruto: str (cluster já resolvido por match exato, ou '')
        """
        for nota in notas:
            tags = [str(t) for t in (nota.get('tags') or [])]
            fonte = str(nota.get('fonte') or nota.get('source') or '')
            cl = str(nota.get('cl_bruto') or '')
            if not cl:
                # resolve com o que já conhecemos (sem aprendizado ainda)
                cl = self.resolver(tags, fonte, usar_aprendizado=False)
            tokens = set()
            for t in list(tags) + ([fonte] if fonte else []):
                n = dedupe(norm(t))
                if n and n not in GENERIC and len(n) >= 3:
                    tokens.add(n)
            for t in tokens:
                self._aprendizado[t][cl] += 1
            for a in tokens:
                for b in tokens:
                    if a < b:
                        self._cooc[a][b] += 1
                        self._cooc[b][a] += 1
            if fonte:
                self._fontes[fonte] += 1
            self._notas_treino += 1
        self._sugerir_novos_clusters()
        return self

    def _sugerir_novos_clusters(self):
        """OUSAR: detecta grupos coesos de fontes que não pertencem a cluster
        conhecido e sugere um cluster novo (não altera a base sozinho)."""
        for f, n_f in self._fontes.items():
            if n_f < 3:
                continue
            nf = dedupe(norm(f))
            if nf in self._norm_idx:
                continue
            co = self._cooc.get(nf, Counter())
            if co:
                top = co.most_common(1)[0]
                self._sugestoes.setdefault('coesos', {})[f] = {
                    'n_notas': n_f,
                    'junto_com': top[0],
                    'frequencia': top[1],
                }

    def resolver(self, tags, fonte='', usar_aprendizado=True):
        """Resolve o cluster de uma nota. Estratégia em cascata:
        1) match exato normalizado (índice); 2) substring de fonte conhecida
        dentro da tag; 3) associação aprendida (co-ocorrência ponderada);
        4) 'geral'."""
        tokens = []
        for t in list(tags) + ([fonte] if fonte else []):
            n = dedupe(norm(t))
            if n:
                tokens.append(n)

        # 1) exato
        for n in tokens:
            if n in self._norm_idx:
                return self._norm_idx[n]

        # 2) substring: alguma fonte conhecida está dentro do token normalizado
        #    (cobre 'androidpuresdk', 'lerauditoria' etc. sem estar no índice)
        for n in tokens:
            if len(n) < 4:
                continue
            for k, cl in self._norm_idx.items():
                if len(k) >= 4 and k in n:
                    return cl

        # 3) aprendizado: soma pesos das associações de todos os tokens
        if usar_aprendizado:
            scores = Counter()
            for n in tokens:
                if n in GENERIC or len(n) < 3:
                    continue
                for cl, peso in self._aprendizado[n].items():
                    scores[cl] += peso
            if scores:
                cl_best, peso_best = scores.most_common(1)[0]
                if peso_best >= 2:
                    return cl_best
                # ousa: melhor candidato com peso 1 mas consistente
                if len(scores) == 1 and peso_best >= 1:
                    return cl_best
        return 'geral'

    def exportar_aprendizado(self):
        return {
            'aprendizado': {k: dict(v) for k, v in self._aprendizado.items()},
            'cooc': {k: dict(v) for k, v in self._cooc.items()},
            'fontes': dict(self._fontes),
            'sugestoes': self._sugestoes,
            'n_notas': self._notas_treino,
        }

    def carregar_aprendizado(self, d):
        d = d or {}
        for k, v in (d.get('aprendizado') or {}).items():
            self._aprendizado[k] = Counter(v)
        for k, v in (d.get('cooc') or {}).items():
            self._cooc[k] = Counter(v)
        self._fontes = Counter(d.get('fontes') or {})
        self._sugestoes = d.get('sugestoes') or {}
        self._notas_treino = d.get('n_notas') or 0
        return self

    def relatorio(self):
        linhas = [f'ClusterMapper: {self._notas_treino} notas de treino']
        for cl in sorted(self.clusters):
            pesos = []
            for t, c in self._aprendizado.items():
                if c.get(cl, 0) >= 2:
                    pesos.append(f'{t}:{c[cl]}')
            pesos.sort(key=lambda x: -int(x.split(":")[1]))
            if pesos:
                linhas.append(f'  {cl}: {", ".join(pesos[:6])}')
        if self._sugestoes:
            linhas.append('Sugestoes de clusters novos (ousadia):')
            for f, info in self._sugestoes.get('coesos', {}).items():
                linhas.append(f'  "{f}" x{info["n_notas"]} (junto: {info["junto_com"]})')
        return '\n'.join(linhas)


def treinar_e_resolver(notas, caminho_aprendizado=None):
    """Atalho: treina, opcionalmente persiste o aprendizado, e devolve o mapper."""
    mapper = ClusterMapper()
    mapper.treinar(notas)
    if caminho_aprendizado:
        os.makedirs(os.path.dirname(caminho_aprendizado), exist_ok=True)
        with open(caminho_aprendizado, 'w', encoding='utf-8') as f:
            json.dump(mapper.exportar_aprendizado(), f, ensure_ascii=False, indent=1)
    return mapper


if __name__ == '__main__':
    demo = [
        {'tags': ['bug', 'android-pure-sdk'], 'fonte': 'android-pure-sdk', 'categoria': 'bugs'},
        {'tags': ['bug', 'androidpuresdk'], 'fonte': '', 'categoria': 'bugs'},
        {'tags': ['bug', 'android-pure-sdkandroid-pure-sdk'], 'fonte': '', 'categoria': 'bugs'},
        {'tags': ['bug', 'mp3player-metadata-rescue'], 'fonte': '', 'categoria': 'bugs'},
        {'tags': ['bug', 'lerauditoria'], 'fonte': '', 'categoria': 'bugs'},
        {'tags': ['bug', 'treinamentonavegacao'], 'fonte': '', 'categoria': 'bugs'},
    ]
    m = ClusterMapper()
    m.treinar(demo)
    print(m.relatorio())
    for t, f in [(['androidpuresdk'], ''), (['lerauditoria'], ''),
                 (['treinamentonavegacao'], ''), (['mp3player'], ''),
                 (['metacognicao'], ''), (['foo'], '')]:
        print(f'  resolver({t}) -> {m.resolver(t, f)}')
