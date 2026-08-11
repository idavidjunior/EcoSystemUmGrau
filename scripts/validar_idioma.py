"""validar_idioma.py — Valida se um texto está em Português do Brasil (pt-BR).

Uso:
  python scripts/validar_idioma.py "texto a validar"
  echo "texto" | python scripts/validar_idioma.py --stdin

Exit: 0 = pt-BR, 1 = não-pt-BR, 2 = erro
"""
import re
import sys

# Palavras comuns em português (artigos, preposições, conjunções, pronomes)
PALAVRAS_PT = {
    # Artigos
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    # Preposições
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sob", "entre", "até", "desde",
    # Conjunções
    "e", "ou", "mas", "porém", "contudo", "todavia", "entretanto",
    "que", "se", "pois", "porque", "como", "quando", "onde",
    # Pronomes
    "eu", "tu", "ele", "ela", "nós", "vocês", "eles", "elas",
    "me", "te", "se", "nos", "vos", "meu", "teu", "seu", "sua",
    # Verbos comuns
    "é", "está", "são", "tem", "pode", "deve", "fazer", "dizer",
    "ir", "vir", "dar", "ver", "saber", "querer", "poder",
    "ter", "ser", "estar", "haver", "ficar", "trazer", "levar",
    # Adjetivos/advérbios comuns
    "bom", "mau", "grande", "pequeno", "novo", "velho",
    "muito", "pouco", "mais", "menos", "também", "já",
    # Expressões
    "não", "sim", "obrigado", "por favor", "desculpe",
}

# Caracteres específicos do português (acentos, cedilha, til)
CARACTERES_PT = set("ãõáàâéêíóôúçÃÕÁÀÂÉÊÍÓÔÚÇ")

# Padrões de palavras pt-BR (terminações comuns)
SUFIXOS_PT = ["ção", "ções", "mente", "oso", "osa", "ável", "ível", "inho", "inha"]


def calcular_score_pt(texto: str) -> float:
    """Calcula um score de 0 a 100 indicando probabilidade de ser pt-BR."""
    if not texto or not texto.strip():
        return 0.0

    texto_lower = texto.lower()
    palavras = re.findall(r'\b\w+\b', texto_lower)

    if not palavras:
        return 0.0

    # 1. Score por palavras conhecidas (peso: 50%)
    palavras_pt = sum(1 for p in palavras if p in PALAVRAS_PT)
    score_palavras = (palavras_pt / len(palavras)) * 100

    # 2. Score por caracteres pt-BR (peso: 30%)
    chars_total = len(texto)
    chars_pt = sum(1 for c in texto if c in CARACTERES_PT)
    score_chars = (chars_pt / max(chars_total, 1)) * 100 * 10  # multiplicar para dar peso

    # 3. Score por sufixos pt-BR (peso: 20%)
    sufixos = sum(1 for p in palavras if any(p.endswith(s) for s in SUFIXOS_PT))
    score_sufixos = (sufixos / len(palavras)) * 100

    # Peso final
    score_final = (score_palavras * 0.5) + (min(score_chars, 100) * 0.3) + (score_sufixos * 0.2)

    return min(score_final, 100.0)


def validar_idioma(texto: str, threshold: float = 30.0) -> dict:
    """Valida se o texto está em pt-BR.

    Args:
        texto: Texto a validar
        threshold: Score mínimo para considerar pt-BR (padrão: 30)

    Returns:
        dict com 'ok' (bool), 'score' (float), 'idioma' (str)
    """
    score = calcular_score_pt(texto)
    ok = score >= threshold

    return {
        "ok": ok,
        "score": round(score, 2),
        "idioma": "pt-BR" if ok else "desconhecido",
        "threshold": threshold,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        texto = sys.stdin.read()
    elif len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
    else:
        print("Uso: python validar_idioma.py \"texto\" ou echo \"texto\" | python validar_idioma.py --stdin")
        sys.exit(2)

    resultado = validar_idioma(texto)

    if resultado["ok"]:
        print(f"[OK] pt-BR detectado (score: {resultado['score']})")
        sys.exit(0)
    else:
        print(f"[FALHA] Não-pt-BR detectado (score: {resultado['score']}, threshold: {resultado['threshold']})")
        sys.exit(1)


if __name__ == "__main__":
    main()