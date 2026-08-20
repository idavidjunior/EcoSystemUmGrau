#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validar_resposta.py — Gate de validação pt-BR antes de cada resposta.

Uso:
  python scripts/validar_resposta.py "texto a validar"
  python scripts/validar_resposta.py --json '{"texto": "..."}'
  echo "texto" | python scripts/validar_resposta.py --stdin

Exit: 0 = pt-BR válido, 1 = traduzido/ajustado, 2 = erro
Saída JSON: {"ok": bool, "texto": str, "original": str, "score": float, "acao": str}
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validar_idioma import calcular_score_pt, PALAVRAS_PT, CARACTERES_PT

# NVIDIA API para tradução quando dicionário falha
def _traduzir_via_llm(texto: str) -> str:
    """Traduz texto para pt-BR usando NVIDIA API."""
    api_key = None
    env_path = ROOT / "scripts" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("NVIDIA_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    if not api_key:
        api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return ""

    prompt = (
        "Traduza o seguinte texto para português brasileiro (pt-BR). "
        "Retorne APENAS o texto traduzido, sem explicações, sem aspas, sem formatação.\n\n"
        f"Texto: {texto}"
    )
    payload = json.dumps({
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.1,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            traduzido = data["choices"][0]["message"]["content"].strip()
            # Remove aspas se o LLM colocou
            traduzido = traduzido.strip('"').strip("'").strip("`")
            return traduzido
    except Exception:
        return ""

# Dicionário de tradução comum pt-BR → inglês (reverso para detecção)
# Palavras/frases inglesas frequentes que o agente pode gerar
TRADUCOES = {
    "the": "o", "a": "um", "an": "um", "is": "é", "are": "são", "was": "era",
    "were": "eram", "be": "ser", "been": "sido", "being": "sendo",
    "have": "ter", "has": "tem", "had": "tinha", "do": "fazer", "does": "faz",
    "did": "fez", "will": "vai", "would": "faria", "could": "poderia",
    "should": "deveria", "may": "pode", "might": "poderia", "must": "deve",
    "can": "pode", "shall": "vai", "not": "não", "no": "não", "yes": "sim",
    "and": "e", "or": "ou", "but": "mas", "if": "se", "then": "então",
    "else": "senão", "when": "quando", "where": "onde", "why": "por que",
    "how": "como", "what": "o quê", "which": "qual", "who": "quem",
    "this": "isto", "that": "isso", "these": "estes", "those": "aqueles",
    "it": "ele", "its": "seu", "my": "meu", "your": "seu", "his": "dele",
    "her": "dela", "our": "nosso", "their": "deles",
    "i": "eu", "you": "você", "he": "ele", "she": "ela", "we": "nós",
    "they": "eles", "me": "me", "him": "ele", "us": "nós", "them": "eles",
    "in": "em", "on": "em", "at": "em", "to": "para", "for": "para",
    "with": "com", "from": "de", "by": "por", "of": "de", "about": "sobre",
    "into": "em", "through": "através", "during": "durante", "before": "antes",
    "after": "depois", "above": "acima", "below": "abaixo",
    "here": "aqui", "there": "lá", "now": "agora", "then": "então",
    "very": "muito", "just": "apenas", "also": "também", "too": "também",
    "only": "apenas", "even": "até", "still": "ainda", "already": "já",
    "back": "volta", "come": "vir", "go": "ir", "get": "obter",
    "make": "fazer", "take": "pegar", "give": "dar", "tell": "dizer",
    "work": "trabalhar", "seem": "parecer", "feel": "sentir",
    "try": "tentar", "leave": "sair", "call": "chamar",
    "good": "bom", "new": "novo", "first": "primeiro", "last": "último",
    "long": "longo", "great": "grande", "little": "pequeno",
    "own": "próprio", "other": "outro", "old": "velho",
    "right": "certo", "big": "grande", "high": "alto", "low": "baixo",
    "different": "diferente", "small": "pequeno", "large": "grande",
    "next": "próximo", "early": "cedo", "young": "jovem",
    "important": "importante", "few": "poucos", "public": "público",
    "bad": "mau", "same": "mesmo", "able": "capaz",
    "hello": "olá", "hi": "olá", "hey": "ei",
    "thanks": "obrigado", "thank you": "obrigado",
    "please": "por favor", "sorry": "desculpe",
    "okay": "ok", "ok": "ok",
    "however": "no entanto", "therefore": "portanto",
    "more": "mais", "less": "menos", "much": "muito",
    "some": "alguns", "many": "muitos", "all": "todos",
    "each": "cada", "every": "cada", "no": "nenhum",
    "nothing": "nada", "something": "algo", "everything": "tudo",
    "someone": "alguém", "everyone": "todos", "nobody": "ninguém",
    "because": "porque", "since": "desde", "while": "enquanto",
    "although": "embora", "unless": "a menos que",
    "until": "até", "once": "uma vez",
    "i'm": "estou", "you're": "você é", "he's": "ele é",
    "she's": "ela é", "it's": "é", "we're": "nós somos",
    "they're": "eles são", "i've": "eu tenho", "you've": "você tem",
    "we've": "nós temos", "they've": "eles têm",
    "i'll": "eu vou", "you'll": "você vai", "he'll": "ele vai",
    "she'll": "ela vai", "we'll": "nós vamos", "they'll": "eles vão",
    "i'd": "eu faria", "you'd": "você faria", "he'd": "ele faria",
    "she'd": "ela faria", "we'd": "nós faríamos", "they'd": "eles fariam",
    "isn't": "não é", "aren't": "não são", "wasn't": "não era",
    "weren't": "não eram", "hasn't": "não tem", "haven't": "não tenho",
    "won't": "não vai", "wouldn't": "não faria",
    "can't": "não pode", "couldn't": "não poderia",
    "shouldn't": "não deveria", "mustn't": "não deve",
    "don't": "não", "doesn't": "não", "didn't": "não",
    "let me": "deixe-me", "let's": "vamos",
    "going to": "vai", "want to": "querer",
    "need to": "precisar", "have to": "ter que",
    "going": "indo", "doing": "fazendo", "making": "fazendo",
    "working": "trabalhando", "trying": "tentando",
    "thinking": "pensando", "saying": "dizendo",
    "looking": "procurando", "using": "usando",
    "using the": "usando o", "based on": "baseado em",
    "in order to": "para", "so that": "para que",
    "as well as": "assim como", "in addition to": "além de",
    "the following": "o seguinte", "for example": "por exemplo",
    "in this case": "neste caso", "in other words": "outras palavras",
    "on the other hand": "por outro lado",
    "in fact": "na verdade", "as a result": "como resultado",
    "note that": "note que", "please note": "observe",
    "it is important": "é importante", "it is necessary": "é necessário",
    "i will": "eu vou", "i can": "eu posso", "i have": "eu tenho",
    "we need": "precisamos", "we should": "devemos",
    "you need": "você precisa", "you should": "você deve",
    "this is": "isto é", "that is": "isso é",
    "there is": "existe", "there are": "existem",
    "here is": "aqui está", "here are": "aqui estão",
    "let me know": "me avise", "feel free": "sinta-se à vontade",
    "don't worry": "não se preocupe", "no problem": "sem problema",
    "great job": "bom trabalho", "well done": "bem feito",
    "good luck": "boa sorte", "take care": "se cuide",
    "see you": "até logo", "bye": "tchau",
}

# Padrões de início de frase que indicam inglês
PADROES_INGLES = re.compile(
    r'^(here\'?s?|let me|let\'?s|i\'?ll|i will|we need|you can|'
    r'the |this is |that is |there is |note that |please |'
    r'sure|of course|absolutely|certainly|definitely|'
    r'okay|right|well|so|now|then|'
    r'how can|what is|where is|why is|when did)',
    re.IGNORECASE
)


def detectar_idioma_texto(texto: str) -> str:
    """Detecta se o texto é pt-BR ou inglês com base em heurísticas."""
    if not texto or not texto.strip():
        return "pt-BR"

    score_pt = calcular_score_pt(texto)

    # Conta palavras que são exclusivamente inglesas
    palavras = re.findall(r'\b[a-zA-Z]+\b', texto.lower())
    if not palavras:
        return "pt-BR"

    # Palavras que são apenas inglesas (não existem em pt-BR)
    palavras_ing = sum(1 for p in palavras if p in TRADUCOES and p not in PALAVRAS_PT)
    ratio_ing = palavras_ing / len(palavras) if palavras else 0

    # Verifica padrões de início de frase
    tem_padrao_ing = bool(PADROES_INGLES.search(texto.strip()))

    # Conta contrações inglesas (can't, won't, it's, etc.)
    contracoes = len(re.findall(r"\b\w+'\w+\b", texto))

    if score_pt >= 30:
        return "pt-BR"
    elif ratio_ing > 0.3 or (tem_padrao_ing and contracoes > 0):
        return "en"
    elif score_pt < 15 and ratio_ing > 0.1:
        return "en"
    else:
        return "pt-BR"


def traduzir_pt_br(texto: str) -> str:
    """Traduz texto inglês simples para pt-BR usando dicionário local.

    Para traduções complexas, retorna o texto original com aviso.
    """
    if not texto:
        return texto

    resultado = texto

    # Substitui contrações e frases compostas primeiro (ordem importa)
    for ing, pt in sorted(TRADUCOES.items(), key=lambda x: -len(x[0])):
        # Substitui palavra inteira (boundary-aware)
        resultado = re.sub(
            r'\b' + re.escape(ing) + r'\b',
            pt,
            resultado,
            flags=re.IGNORECASE
        )

    # Corrige capitalização após tradução
    resultado = resultado.strip()

    return resultado


def validar_e_corrigir(texto: str, threshold: float = 30.0) -> dict:
    """Valida texto e corrige se necessário.

    Returns:
        dict com ok, texto (final), original, score, acao, idioma_detectado
    """
    if not texto or not texto.strip():
        return {
            "ok": True,
            "texto": texto,
            "original": texto,
            "score": 0,
            "acao": "vazio",
            "idioma_detectado": "pt-BR",
        }

    score = calcular_score_pt(texto)
    idioma = detectar_idioma_texto(texto)

    if score >= threshold:
        return {
            "ok": True,
            "texto": texto,
            "original": texto,
            "score": round(score, 2),
            "acao": "aprovado",
            "idioma_detectado": idioma,
        }

    # Texto não é pt-BR — tenta traduzir via LLM
    texto_traduzido = _traduzir_via_llm(texto)
    if texto_traduzido:
        score_traduzido = calcular_score_pt(texto_traduzido)
        if score_traduzido >= threshold:
            return {
                "ok": True,
                "texto": texto_traduzido,
                "original": texto,
                "score": round(score_traduzido, 2),
                "acao": "traduzido_llm",
                "idioma_detectado": idioma,
            }

    # LLM falhou — retorna original com aviso
    return {
        "ok": False,
        "texto": texto,
        "original": texto,
        "score": round(score, 2),
        "acao": "reprovado",
        "idioma_detectado": idioma,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        data = json.loads(sys.argv[2])
        texto = data.get("texto", "")
    elif len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        texto = sys.stdin.read()
    elif len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
    else:
        print("Uso: python validar_resposta.py \"texto\" ou --json '{\"texto\": \"...\"}'")
        sys.exit(2)

    resultado = validar_e_corrigir(texto)

    # Saída JSON para integração no pipeline
    print(json.dumps(resultado, ensure_ascii=False))

    if resultado["ok"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
