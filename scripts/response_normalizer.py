#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""response_normalizer.py — Camada final de normalização de resposta (SPEC 1.0).

Orquestra as peças existentes (não duplica) e adiciona as etapas que faltam:

Reuso (import direto, nunca subprocess duplicado):
  - validar_idioma.calcular_score_pt          -> padrão linguístico pt-BR
  - validar_resposta.validar_e_corrigir       -> gate pt-BR + correção
  - validar_bajulacao.detectar_bajulacao      -> antibajulação

Etapas próprias:
  - tipo de interação (pergunta, implementação, erro, investigação, ...)
  - complexidade (tamanho + frases longas)
  - estrutura adaptativa (resumo -> entendimento -> técnico)
  - remoção de redundância (frases repetidas, espaços duplos)
  - estados de evidência (CONFIRMADO / PROVÁVEL / HIPÓTESE / NÃO VERIFICADO)
  - verificação de transparência (marcadores de incerteza)

Uso:
  python scripts/response_normalizer.py "texto"
  echo "texto" | python scripts/response_normalizer.py --stdin
  python scripts/response_normalizer.py --json '{"texto": "...", "tipo": "erro"}'

Saída JSON: {ok, texto, score_pt, tipo, complexidade, estrutura, acoes, ...}
Exit: 0 = normalizado/ok, 1 = houve correção aplicada, 2 = erro
"""
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validar_idioma import calcular_score_pt  # noqa: E402
from validar_resposta import validar_e_corrigir  # noqa: E402
from validar_bajulacao import detectar_bajulacao  # noqa: E402

# Marcadores de evidência reconhecidos (SPEC 3.1)
EVIDENCIA = ("CONFIRMADO", "PROVÁVEL", "HIPÓTESE", "NÃO VERIFICADO",
             "FALHOU", "INCOMPLETO", "IMPLEMENTADO", "TESTADO", "VALIDADO",
             "PRODUÇÃO", "PLANEJADO", "EM EXECUÇÃO", "CONCLUÍDO", "PARCIAL",
             "BLOQUEADO", "PENDENTE", "CANCELADO")

# Palavras de incerteza que indicam hipótese/pendência de verificação
INCERTEZA = re.compile(
    r'\b(?:provavelmente|possivelmente|talvez|aparentemente|possivelmente|'
    r'nao confirmad[oa]|ainda nao|hipotese|suspeito que|acho que|pode ser|'
    r'pode ter|nao verificad[oa]|precisamos testar|sem dados suficientes|'
    r'precisa (?:de )?validac|precisa (?:de )?teste|impera que)\b',
    re.IGNORECASE,
)

# Padrões de início que indicam o tipo da interação
TIPO_PADROES = [
    ("erro", re.compile(r'\b(erro|falhou|falha|crash|exception|quebrou|bug)\b', re.IGNORECASE)),
    ("implementacao", re.compile(r'\b(implement|criei|criado|alterei|alterado|escrevi|adicionei|refatorei|colei|construi)\b', re.IGNORECASE)),
    ("atualizacao", re.compile(r'\b(atualizei|atualizado|mudei|mudou|atualizacao|versao|upgrade)\b', re.IGNORECASE)),
    ("investigacao", re.compile(r'\b(investigu|investigando|diagnostic|analisei|estou analisando|evidencias|procurando causa)\b', re.IGNORECASE)),
    ("decisao", re.compile(r'\b(decidi|decisao|escolhi|optei|trade-off|arquitetura)\b', re.IGNORECASE)),
    ("pergunta", re.compile(r'\?$', re.MULTILINE)),
]

# Redundância estrutural (frases enchimento da IA, preâmbulos vazios)
PREAMBULOS = re.compile(
    r'^\s*(claro!|claro|com certeza!?|certo!?|vamos lá|ok!?|perfeito!?|'
    r'vou ajudar|deixa eu ver|deixa eu analisar|deixa eu pensar|'
    r'excelente conhecimento|ótima pergunta|boa pergunta|'
    r'entendi|entendido|anotado|sem problemas)\s*[.!]?\s*$',
    re.IGNORECASE,
)


def detectar_tipo(texto: str) -> str:
    """Infere o tipo da interação por heurísticas simples."""
    if not texto or not texto.strip():
        return "desconhecido"
    for tipo, padrao in TIPO_PADROES:
        if padrao.search(texto):
            return tipo
    return "comunicacao"


def medir_complexidade(texto: str) -> dict:
    """Mede tamanho e proporção de frases longas (SPEC 6)."""
    if not texto or not texto.strip():
        return {"nivel": "simples", "palavras": 0, "frases": 0, "frases_longas": 0, "frase_media": 0}
    palavras = re.findall(r"\S+", texto)
    frases = [f for f in re.split(r"[.!?]+", texto) if f.strip()]
    longas = sum(1 for f in frases if len(f.split()) > 30)
    media = round(len(palavras) / len(frases), 1) if frases else 0
    if len(palavras) < 40 and media <= 15:
        nivel = "simples"
    elif len(palavras) < 150 and media <= 20:
        nivel = "media"
    else:
        nivel = "complexa"
    return {"nivel": nivel, "palavras": len(palavras), "frases": len(frases),
            "frases_longas": longas, "frase_media": media}


def remover_redundancia(texto: str) -> tuple:
    """Remove repetições mecânicas e preâmbulos vazios (SPEC 10.1 passo 8)."""
    if not texto:
        return texto, []
    acoes = []
    # Remove linhas úteis de preâmbulo ('Claro!', 'Vou ajudar.', etc.)
    linhas = [PREAMBULOS.sub("", ln).rstrip() for ln in texto.splitlines()]
    # Remove linhas vazias duplicadas (máx 1)
    limpo = []
    vazio_pre = False
    for ln in linhas:
        if not ln.strip():
            if vazio_pre:
                continue
            vazio_pre = True
        else:
            vazio_pre = False
        limpo.append(ln)
    novo = "\n".join(limpo).strip()
    if novo != texto.strip():
        acoes.append("preambulo/linhas vazias removidas")
    # Colapsa espaços duplos residuais
    final = re.sub(r"[ \t]{2,}", " ", novo)
    if final != novo:
        acoes.append("espacos duplos colapsados")
    return final, acoes


def detectar_evidencia(texto: str) -> dict:
    """Separa fatos de hipóteses presentes no texto (SPEC 3.1/4)."""
    marcadores = [e for e in EVIDENCIA if re.search(rf"\b{re.escape(e)}\b", texto, re.IGNORECASE)]
    incertezas = sorted(set(m.lower() for m in INCERTEZA.findall(texto)))
    return {"marcadores_estado": marcadores, "termos_incerteza": incertezas}


def selecionar_estrutura(tipo: str, complexidade: str) -> str:
    """Escolhe a estrutura adaptativa (SPEC 4/6): resumo, entendimento, técnico."""
    if complexidade == "simples":
        return "direta"
    if tipo == "erro":
        return "problema/causa/impacto/correcao/situacao"
    if tipo == "implementacao":
        return "status/alteracao/motivo/validacao/resultado/pendencias"
    if tipo == "decisao":
        return "problema/opcoes/tradeoffs/decisao/motivo/impacto/riscos"
    if tipo == "investigacao":
        return "pergunta/evidencias/conclusao/duvidas/proximo_passo"
    if tipo == "atualizacao":
        return "o_que_mudou/por_que/resultado/impacto"
    return "resumo/o_que_aconteceu/o_que_foi_feito/resultado/proximo_passo"


def normalizar_resposta(texto: str, tipo: str | None = None) -> dict:
    """Pipeline final de normalização: reusa peças + etapas próprias.

    Returns:
        dict com ok, texto, score_pt, tipo, complexidade, estrutura,
        evidencia, acoes, bajulacao, validacao.
    """
    original = texto or ""
    texto_final = original
    acoes = []

    # 1. Padrão linguístico (reuso do gate pt-BR existente)
    try:
        validacao = validar_e_corrigir(texto_final)
        acoes.extend(
            [f"pt-br: {validacao.get('acao')}"] if validacao.get("acao") not in ("aprovado", "vazio")
            else []
        )
        if validacao.get("texto") and validacao.get("acao") != "vazio":
            texto_final = validacao["texto"]
        score_pt = validacao.get("score", 0)
    except Exception as e:  # fail-soft: nunca derruba a resposta
        validacao = {"ok": True, "acao": "erro_interno", "score": 0}
        score_pt = 0
        acoes.append(f"validador indisponivel ({e})")

    # 2. Tipo de interação e complexidade
    tipo_final = tipo or detectar_tipo(texto_final or original)
    complexidade = medir_complexidade(texto_final or original)

    # 3. Antibajulação (reuso do detector existente)
    try:
        bajulacao = detectar_bajulacao(texto_final or original)
        if not bajulacao.get("ok", True):
            acoes.append(f"bajulacao detectada: {', '.join(bajulacao.get('encontrados', []))}")
    except Exception:
        bajulacao = {"ok": True, "encontrados": [], "score": 0}

    # 4. Remoção de redundância
    texto_final, acoes_red = remover_redundancia(texto_final or original)
    acoes.extend(acoes_red)

    # 5. Evidência e transparência (detecção, nunca altera fatos)
    evidencia = detectar_evidencia(texto_final)

    # 6. Estrutura adaptativa
    estrutura = selecionar_estrutura(tipo_final, complexidade["nivel"])

    return {
        "ok": True,
        "texto": texto_final,
        "original": original,
        "score_pt": round(float(score_pt), 2) if score_pt else 0.0,
        "tipo": tipo_final,
        "complexidade": complexidade,
        "estrutura": estrutura,
        "evidencia": evidencia,
        "bajulacao": bajulacao,
        "acoes": acoes,
        "validacao": validacao,
    }


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        try:
            data = json.loads(sys.argv[2])
        except (IndexError, json.JSONDecodeError):
            print(json.dumps({"ok": False, "erro": "JSON inválido"}, ensure_ascii=False))
            return 2
        texto = data.get("texto", "")
        tipo = data.get("tipo")
    elif len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        texto = sys.stdin.read()
        tipo = None
    elif len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
        tipo = None
    else:
        print("Uso: python response_normalizer.py \"texto\" | --stdin | --json '{\"texto\": ...}'")
        return 2

    resultado = normalizar_resposta(texto, tipo)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())