#!/usr/bin/env python3
"""
Preditor de Padroes de Uso - Jarvis
Extrai padroes do historico de conversa e antecipa comandos provaveis.

Funcionalidades:
1. Extrai temas recorrentes das perguntas do usuario
2. Identifica horarios de pico de uso
3. Detecta comandos repetidos (alta frequencia)
4. Gera sugestoes de antecipacao
5. Salva predicoes em predicao_uso.json para a bridge usar

Uso:
    python scripts/preditor_uso.py           # Analisa e salva predicoes
    python scripts/preditor_uso.py --report  # Mostra relatorio detalhado
    python scripts/preditor_uso.py --top 5    # Top 5 padroes
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HISTORICO = RAIZ / "conversa_unica.json"
PREDICAO = RAIZ / "scripts" / "predicao_uso.json"
BRIDGE_ESTADO = RAIZ / "scripts" / "bridge_estado.json"

# Categorias de intenção (palavras-chave -> categoria)
CATEGORIAS = {
    "clima": ["clima", "temperatura", "chover", "sol", "chuva", "previsao"],
    "hora": ["horas", "hora", "que horas", "agora"],
    "tv": ["tv", "televisao", "aumenta", "diminui", "volume", "liga", "desliga", "canal"],
    "rede": ["wi-fi", "wifi", "roteador", "rede", "celular", "conectado", "dispositivo"],
    "git": ["git", "commit", "push", "pull", "branch", "merge"],
    "build": ["build", "compilar", "instalar", "apk", "gradle"],
    "pronuncia": ["pronuncia", "pronuncie", "fala", "fale", "voz"],
    "memoria": ["memoria", "lembrar", "esquecer", "contexto", "historico"],
    "saudacao": ["bom dia", "boa tarde", "boa noite", "oi", "ola", "tudo bem"],
    "status": ["status", "como esta", "humor", "voce bem", "online"],
    "ecossistema": ["ecossistema", "sistema", "jarvis", "um grau"],
    "tv_apps": ["netflix", "youtube", "prime", "disney", "spotify", "app"],
    "roteador": ["roteador", "vivo", "senha", "admin", "painel"],
    "aprendizado": ["aprender", "estudar", "conhecimento", "evoluir"],
}


def carregar_historico():
    """Carrega o historico de conversa."""
    if not HISTORICO.exists():
        return []
    try:
        with open(HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar historico: {e}")
        return []


def extrair_perguntas(historico):
    """Extrai apenas as entradas do usuario."""
    perguntas = []
    for entrada in historico:
        if isinstance(entrada, str) and entrada.startswith("Usu"):
            # Limpa o prefixo "Usuario: " (pode ter encoding estranho)
            texto = re.sub(r"^Usu[^\s]*\s*:\s*", "", entrada)
            pergunta = texto.strip()
            if pergunta and len(pergunta) > 2:
                perguntas.append(pergunta.lower())
    return perguntas


def classificar_categoria(pergunta):
    """Classifica uma pergunta em uma categoria."""
    for categoria, palavras in CATEGORIAS.items():
        for palavra in palavras:
            if palavra in pergunta:
                return categoria
    return "outros"


def analisar_padroes(perguntas):
    """Analisa padroes nas perguntas do usuario."""
    # 1. Frequencia por categoria
    freq_categorias = Counter()
    for p in perguntas:
        cat = classificar_categoria(p)
        freq_categorias[cat] += 1

    # 2. Perguntas mais repetidas (similares)
    similares = Counter()
    for p in perguntas:
        # Normaliza: remove acentos e espaços extras
        norm = re.sub(r"[^\w\s]", "", p)
        norm = re.sub(r"\s+", " ", norm).strip()
        if len(norm) > 5:
            similares[norm] += 1

    # 3. Ultimas N perguntas (para contexto recente)
    recentes = perguntas[-20:] if len(perguntas) >= 20 else perguntas
    freq_recentes = Counter()
    for p in recentes:
        cat = classificar_categoria(p)
        freq_recentes[cat] += 1

    # 4. Horario da ultima atividade
    horario_ultima = None
    if BRIDGE_ESTADO.exists():
        try:
            with open(BRIDGE_ESTADO, "r", encoding="utf-8") as f:
                estado = json.load(f)
                horario_ultima = estado.get("ultima_conexao", "")
        except Exception:
            pass

    # 5. Detectar sequencias (a -> b frequentemente)
    sequencias = Counter()
    for i in range(len(perguntas) - 1):
        cat_a = classificar_categoria(perguntas[i])
        cat_b = classificar_categoria(perguntas[i + 1])
        if cat_a != "outros" and cat_b != "outros":
            sequencias[f"{cat_a} -> {cat_b}"] += 1

    return {
        "total_perguntas": len(perguntas),
        "freq_categorias": dict(freq_categorias.most_common(10)),
        "freq_recentes": dict(freq_recentes.most_common(5)),
        "perguntas_repetidas": {
            p: c for p, c in similares.most_common(5) if c > 1
        },
        "sequencias_comuns": dict(sequencias.most_common(5)),
        "horario_ultima_atividade": horario_ultima,
        "ultima_pergunta": perguntas[-1] if perguntas else "",
    }


def gerar_predicao(padroes):
    """Gera predicoes baseadas nos padroes encontrados."""
    predicoes = []

    # Categoria mais frequente historicamente
    if padroes["freq_categorias"]:
        top_cat = list(padroes["freq_categorias"].keys())[0]
        predicoes.append({
            "tipo": "categoria_frequente",
            "categoria": top_cat,
            "frequencia": padroes["freq_categorias"][top_cat],
            "confianca": "alta" if padroes["freq_categorias"][top_cat] >= 5 else "media",
            "sugestao": f"Usuario costuma pedir coisas relacionadas a {top_cat}",
        })

    # Categoria mais frequente recentemente (ultimo 20)
    if padroes["freq_recentes"]:
        top_recente = list(padroes["freq_recentes"].keys())[0]
        if top_recente != list(padroes["freq_categorias"].keys())[0] if padroes["freq_categorias"] else True:
            predicoes.append({
                "tipo": "tendencia_recente",
                "categoria": top_recente,
                "frequencia": padroes["freq_recentes"][top_recente],
                "confianca": "media",
                "sugestao": f"Tendencia recente: {top_recente}",
            })

    # Sequencia comum (a -> b)
    for seq, count in padroes["sequencias_comuns"].items():
        if count >= 2:
            predicoes.append({
                "tipo": "sequencia",
                "padrao": seq,
                "frequencia": count,
                "confianca": "media",
                "sugestao": f"Apos falar de {seq.split(' -> ')[0]}, costuma falar de {seq.split(' -> ')[1]}",
            })

    # Perguntas repetidas
    for p, count in padroes["perguntas_repetidas"].items():
        predicoes.append({
            "tipo": "pergunta_repetida",
            "pergunta": p[:80],
            "frequencia": count,
            "confianca": "alta",
            "sugestao": f"Pergunta recorrente: {p[:60]}",
        })

    return predicoes


def salvar_predicao(padroes, predicoes):
    """Salva as predicoes em arquivo JSON."""
    dados = {
        "gerado_em": datetime.now().isoformat(),
        "padroes": padroes,
        "predicoes": predicoes,
        "total_predicoes": len(predicoes),
    }
    with open(PREDICAO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return PREDICAO


def main():
    historico = carregar_historico()
    if not historico:
        print("Nenhum historico encontrado.")
        return

    perguntas = extrair_perguntas(historico)
    if not perguntas:
        print("Nenhuma pergunta encontrada no historico.")
        return

    padroes = analisar_padroes(perguntas)
    predicoes = gerar_predicao(padroes)
    caminho = salvar_predicao(padroes, predicoes)

    if "--report" in sys.argv:
        print(f"=== RELATORIO DE PADROES DE USO ===")
        print(f"Total de perguntas analisadas: {padroes['total_perguntas']}")
        print(f"\nCategorias mais frequentes (historico):")
        for cat, freq in padroes["freq_categorias"].items():
            print(f"  {cat}: {freq}")
        print(f"\nCategorias mais frequentes (recente):")
        for cat, freq in padroes["freq_recentes"].items():
            print(f"  {cat}: {freq}")
        print(f"\nSequencias comuns (A -> B):")
        for seq, count in padroes["sequencias_comuns"].items():
            print(f"  {seq}: {count}")
        print(f"\nPerguntas repetidas:")
        for p, count in padroes["perguntas_repetidas"].items():
            print(f"  ({count}x) {p[:70]}")
        print(f"\nPredicoes geradas: {len(predicoes)}")
        for pred in predicoes:
            print(f"  [{pred['confianca']}] {pred['sugestao']}")
        print(f"\nSalvo em: {caminho}")
    elif "--top" in sys.argv:
        idx = sys.argv.index("--top") + 1
        n = int(sys.argv[idx]) if idx < len(sys.argv) else 5
        print(f"Top {n} padroes:")
        for pred in predicoes[:n]:
            print(f"  [{pred['confianca']}] {pred['sugestao']}")
    else:
        print(f"Padroes analisados. {len(predicoes)} predicoes geradas em {caminho}")


if __name__ == "__main__":
    main()
