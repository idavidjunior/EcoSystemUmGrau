"""detect_english_words.py — Detecta palavras em inglês no meio do texto PT-BR
e aplica SSML <lang xml:lang="en-US"> para pronúncia correta no TTS.

Complementa o pronunciar_termos.py (glossário técnico) detectando
palavras inglesas genéricas via lista de frequência + heurísticas.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_FREQ_PATH = ROOT / "config" / "english_freq.json"

# Cache
_EN_FREQ_SET = None
_EN_REGEX = None


def _carregar_lista_frequencia():
    """Carrega conjunto de palavras inglesas comuns (top 5000-10000)."""
    global _EN_FREQ_SET
    if _EN_FREQ_SET is not None:
        return _EN_FREQ_SET

    try:
        with open(EN_FREQ_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _EN_FREQ_SET = set(data.get("words", []))
    except Exception:
        # Fallback mínimo: palavras inglesas muito comuns
        _EN_FREQ_SET = {
            "the", "and", "you", "for", "with", "this", "that", "have",
            "from", "they", "will", "would", "could", "should", "about",
            "your", "into", "when", "what", "there", "their", "been",
            "more", "very", "after", "just", "like", "over", "then",
            "also", "its", "our", "them", "these", "than", "only",
            "error", "warning", "info", "debug", "config", "server",
            "client", "api", "database", "function", "variable", "class",
            "module", "import", "export", "default", "async", "await",
            "try", "catch", "finally", "throw", "return", "null",
            "undefined", "boolean", "string", "number", "object",
            "array", "promise", "callback", "event", "listener"
        }
    return _EN_FREQ_SET


def _eh_palavra_inglesa(token: str) -> bool:
    """Heurística: palavra parece inglesa (sem acentos, só ASCII letras)."""
    if not token:
        return False
    if not re.match(r"^[A-Za-z]+$", token):
        return False
    # Palavras muito curtas (1-3 letras) são stop words ambíguas
    if len(token) <= 3:
        return False
    # Se tem maiúscula no meio (camelCase/PascalCase), provável termo técnico
    if re.search(r"[a-z][A-Z]", token):
        return True
    # Se é TUDO maiúscula (acrônimo), provável termo técnico
    if token.isupper() and len(token) >= 2:
        return True
    # Verifica na lista de frequência (apenas palavras >= 4 letras)
    return token.lower() in _carregar_lista_frequencia()


def detectar_palavras_inglesas(texto: str):
    """Detecta palavras em inglês no texto (além do glossário técnico).

    Retorna lista de (palavra, inicio, fim) ordenada por posição.
    """
    # Primeiro, pegar termos do glossário técnico (já tratados em pronunciar_termos)
    # Aqui focamos em palavras inglesas genéricas não técnicas
    tokens = re.finditer(r"\b[A-Za-z][A-Za-z0-9']*\b", texto)
    encontrados = []
    for m in tokens:
        token = m.group()
        if _eh_palavra_inglesa(token):
            encontrados.append((token, m.start(), m.end()))

    # Remover sobreposições (manter a primeira ocorrência)
    filtrados = []
    ultima_pos = -1
    for palavra, ini, fim in sorted(encontrados, key=lambda x: x[1]):
        if ini >= ultima_pos:
            filtrados.append((palavra, ini, fim))
            ultima_pos = fim
    return filtrados


def marcar_ingles_ssml(texto: str) -> str:
    """Marca palavras inglesas detectadas com SSML lang tag.

    NÃO marca termos já cobertos pelo glossário técnico (pronunciar_termos).
    """
    # Carregar termos do glossário para evitar duplicação
    try:
        from pronunciar_termos import identificar_termos
        termos_glossario = identificar_termos(texto)
        glossario_ranges = [(ini, fim) for _, ini, fim in termos_glossario]
    except Exception:
        glossario_ranges = []

    def _sobrepoe_glossario(ini, fim):
        for g_ini, g_fim in glossario_ranges:
            if not (fim <= g_ini or ini >= g_fim):
                return True
        return False

    palavras_en = detectar_palavras_inglesas(texto)
    if not palavras_en:
        return texto

    resultado = []
    pos_atual = 0
    for palavra, ini, fim in palavras_en:
        if _sobrepoe_glossario(ini, fim):
            continue
        resultado.append(texto[pos_atual:ini])
        resultado.append(f'<lang xml:lang="en-US">{palavra}</lang>')
        pos_atual = fim
    resultado.append(texto[pos_atual:])
    return "".join(resultado)


def pipeline_completo_tts(texto: str) -> str:
    """Pipeline completo: glossário técnico + detecção automática inglês.

    1. pronunciar_termos.marcar_para_tts (glossário técnico)
    2. marcar_ingles_ssml (palavras inglesas genéricas)
    """
    try:
        from pronunciar_termos import marcar_para_tts
        texto = marcar_para_tts(texto, formato="ssml")
    except Exception:
        pass
    return marcar_ingles_ssml(texto)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Uso: python detect_english_words.py \"texto com English words\"")
        sys.exit(1)
    texto = " ".join(sys.argv[1:])
    print("=== ORIGINAL ===")
    print(texto)
    print("\n=== COM SSML INGLÊS (auto-detect) ===")
    print(marcar_ingles_ssml(texto))
    print("\n=== PIPELINE COMPLETO (glossário + auto) ===")
    print(pipeline_completo_tts(texto))


if __name__ == "__main__":
    main()