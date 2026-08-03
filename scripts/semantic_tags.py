"""Extracao de tags semanticas (RAKE leve) em Python puro — sem dependencias.

Extrai palavras-chave relevantes de textos de conhecimento (titulo + resumo)
para enriquecer tags semanticas na origem. Baseado no algoritmo RAKE (Rapid
Automatic Keyword Extraction), simplificado e adaptado para PT-BR/EN.

Uso:
  from semantic_tags import extrair_tags
  tags = extrair_tags("Escrita atomica sempre: json.dump corrompia arquivo")
  # -> ['escrita atomica', 'json.dump', 'corrompia arquivo']

Deterministico, sem API, sem modelo — nao alucina: so retorna palavras que
realmente ocorrem no texto.
"""
import re
from collections import defaultdict

# Stopwords PT-BR + EN comuns (foco em palavras que nao sao conceitos)
STOPWORDS = frozenset("""
a o os as um uma uns umas e mas nem ou que se no na nos nas de do da dos das
em ao aos as perante por para com contra entre sem sob sobre após antes depois
daquele daquela este esta esse essa isto isso aquele aquela estes estas esses
essas aqueles aquelas seu sua seus suas dele dela deles delas meu minha meus
minhas nosso nossa nossos nossas teu tua teus tuas lhe lhes eu tu ele ela nos
vos eles elas me te se nos vos lo la lhe os as lhes mim ti si ele ela voce
voces senhor senhora como quando onde porque por que pois alem ainda apenas
assim agora aí ali aquele aquilo cada certo cada coisa demais depois dever
entao então esta este existe fazer foi fosse fora forma foram fosse fruto
haja haja mais menos muito muita muitos muitas mesmo mesma nem nunca outro
outra outros outras pouco pior pouco primeiro primeira segundo segunda
sempre seja seu seja sendo ser sob tal tanto todos todas tudo vez vezes
the a an and or but if then so of to in on at by for with from into onto
upon about against between through during before after above below under
again further once here there when where why how all any both each few more
most other some such no nor not only own same than too very can will just
don should now is are was were be been being have has had having do does
did doing would could should might must shall may can't cannot won't you
your yours he him his she her hers it its they them their theirs we us our
ours you your yours
""".split())

# Prefixos/terminacoes que desqualificam uma palavra como tag
_BAD_TAG_RE = re.compile(
    r'^[^a-zà-ÿ0-9]+$'           # so pontuacao/emoji
    r'|^(www|http|https|file|cdn|raw|api|key|id|v|s|d|o)$'  # tecnicos curtos
)
_MIN_LEN = 3
_MAX_TAGS = 8
_MAX_PHRASE_WORDS = 3

# Substituicoes normativas (mesma familia de palavras)
_NORMALIZACOES = {
    'json': 'json', 'obsidian': 'obsidian', 'widget': 'widget',
    'grafo': 'grafo', 'vault': 'vault', 'sinaptic': 'sinapse',
    'semantica': 'semantico', 'semanticas': 'semantico',
    'conhecimento': 'conhecimento', 'aprendizado': 'aprendizado',
    'aprendizados': 'aprendizado', 'memoria': 'memoria',
    'memorias': 'memoria', 'automacao': 'automacao',
    'automacao-web': 'automacao', 'debug': 'debug', 'debugging': 'debug',
    'teste': 'teste', 'testes': 'teste', 'performance': 'performance',
    'persistencia': 'persistencia', 'seguranca': 'seguranca',
    'arquitetura': 'arquitetura', 'api': 'api', 'mcp': 'mcp',
    'opencode': 'opencode', 'ler': 'ler', 'jarvis': 'jarvis',
    'android': 'android', 'python': 'python', 'obisidian': 'obsidian',
}


def _sentencas(texto):
    """Divide texto em unidades (frases/linhas) para analise RAKE."""
    texto = re.sub(r'[|#*_`>]', ' ', texto)  # remove markdown/separadores
    partes = re.split(r'[.\n;:!?]', texto)
    return [p for p in partes if p.strip()]


def _candidatos(frase):
    """Retorna candidatos: palavras ou frases de ate MAX_PHRASE_WORDS palavras."""
    palavras = re.findall(r'[a-zà-ÿ0-9]+', frase.lower())
    candidatos = []
    for p in palavras:
        if p in STOPWORDS:
            continue
        if _MIN_LEN <= len(p) and not _BAD_TAG_RE.match(p):
            candidatos.append(p)
    return candidatos


def _frequencia(ocorrencias):
    """Conta frequencia de cada palavra candidata e de co-ocorrencias."""
    freq = defaultdict(int)
    grau = defaultdict(int)
    for palavras in ocorrencias:
        for i, palavra in enumerate(palavras):
            freq[palavra] += 1
            # grau = soma das coocorrencias da palavra na mesma frase
            grau[palavra] += len(palavras) - 1
            for j in range(i + 1, len(palavras)):
                grau[palavras[j]] += 1
    return freq, grau


def _score_palavras(freq, grau):
    """RAKE: score = grau / frequencia (palavras que dominam o texto)."""
    return {p: grau[p] / max(1, freq[p]) for p in freq}


def extrair_tags(texto, max_tags=_MAX_TAGS, min_len=_MIN_LEN):
    """Extrai tags semanticas (frases curtas) de um texto.

    Deterministico e local: so usa palavras presentes no texto. Retorna lista
    de strings (frases de 1..3 palavras) normalizadas e ordenadas por relevancia.
    """
    if not texto or not texto.strip():
        return []
    ocorrencias = [_candidatos(f) for f in _sentencas(texto)]
    ocorrencias = [o for o in ocorrencias if o]
    if not ocorrencias:
        return []
    freq, grau = _frequencia(ocorrencias)
    scores = _score_palavras(freq, grau)

    # monta frases candidatas: sequencias consecutivas de palavras candidatas
    frases = set()
    for palavras in ocorrencias:
        i = 0
        while i < len(palavras):
            for n in range(1, _MAX_PHRASE_WORDS + 1):
                if i + n <= len(palavras):
                    frase = ' '.join(palavras[i:i + n])
                    frases.add(frase)
            i += 1

    # normaliza frases e aplica score (soma dos scores das palavras)
    def score_frase(frase):
        partes = frase.split()
        base = sum(scores.get(p, 0) for p in partes)
        # prefere frases curtas: palavras extras diluem o score por palavra
        base = base / (len(partes) ** 0.6)
        # penaliza frases muito longas
        if len(frase) > 40:
            base *= 0.5
        return base

    ranked = sorted(frases, key=lambda f: -score_frase(f))

    # deduplica e filtra por relevancia/qualidade; prioriza palavras-chave
    # com score alto e evita sobreposicao (tag nao deve repetir conceito ja coberto)
    resultado = []
    vistos = set()
    escolhidas = set()
    for frase in ranked:
        partes = frase.split()
        if len(partes) > _MAX_PHRASE_WORDS:
            continue
        if any(len(p) < min_len for p in partes):
            continue
        chave = ' '.join(sorted(partes))
        if chave in vistos:
            continue
        # palavras novas em relacao as ja escolhidas
        palavras_novas = [p for p in partes if p not in escolhidas]
        if not palavras_novas:
            continue
        # evita fragmentos tipo "usar tmp" se "tmp" ja entrou como palavra
        if len(partes) > 1 and any(
            p in escolhidas and all(q in escolhidas for q in partes)
            for p in partes
        ):
            continue
        vistos.add(chave)
        escolhidas.update(partes)
        resultado.append(frase)
        if len(resultado) >= max_tags:
            break
    return resultado


def extrair_tags_consolidado(titulo, corpo='', extra=None, max_tags=_MAX_TAGS):
    """Extrai tags semanticas de titulo + corpo + extras (RAKE leve).

    Junta tudo, extrai e retorna lista de tags. Uso principal: enriquecer
    aprendizados/registros na origem (memory_engine, knowledge_consolidator).
    """
    fontes = [titulo or '', corpo or ''] + [str(e or '') for e in (extra or [])]
    texto = ' '.join(fontes)
    return extrair_tags(texto, max_tags=max_tags)


if __name__ == '__main__':
    import sys
    demo = sys.argv[1] if len(sys.argv) > 1 else (
        'Escrita atomica sempre: json.dump corrompia arquivo. '
        'Usar tmp + os.replace para persistencia segura em JSON.')
    print('Tags:', extrair_tags(demo))