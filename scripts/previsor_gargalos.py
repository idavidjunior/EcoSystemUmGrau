#!/usr/bin/env python3
"""
Previsor de Gargalos - Jarvis
Monitora sinais do ecossistema e prevê gargalos antes que aconteçam.

Funcionalidades:
1. Monitora tempo de resposta da bridge (lentidao)
2. Verifica uso de disco e memoria (esgotamento)
3. Detecta restarts frequentes do watchdog (instabilidade)
4. Verifica tamanho do historico (saturacao)
5. Alerta sobre arquivos de log crescendo demais
6. Gera.predicoes de gargalo com nivel de confianca

Uso:
    python scripts/previsor_gargalos.py           # Analisa e salva
    python scripts/previsor_gargalos.py --report  # Relatorio detalhado
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "scripts"
PREDICAO = SCRIPTS / "predicao_gargalos.json"
HISTORICO = RAIZ / "conversa_unica.json"
BRIDGE_ESTADO = SCRIPTS / "bridge_estado.json"
BRIDGE_HISTORICO = SCRIPTS / "bridge_historico.json"
LOG_DIR = RAIZ / "ler-runtime" / "logs"
CONHECIMENTO = RAIZ / "ler-runtime" / "CONHECIMENTO.md"

# Limiares
LIMIAR_DISCO_MB = 500  # Avisar se algum arquivo > 500MB
LIMIAR_HISTORICO_ENTRADAS = 450  # Avisar se approaching 500 (max)
LIMIAR_RESTARTS = 3  # Mais de 3 restarts em 1h = instavel
LIMIAR_LOG_MB = 50  # Logs > 50MB


def tamanho_arquivo_mb(caminho):
    """Retorna tamanho do arquivo em MB."""
    try:
        return os.path.getsize(caminho) / (1024 * 1024)
    except Exception:
        return 0


def verificar_disco():
    """Verifica arquivos grandes no ecossistema."""
    alertas = []
    # Verifica arquivos conhecidos que podem crescer
    arquivos_monitorar = [
        HISTORICO,
        CONHECIMENTO,
        SCRIPTS / "memory_engine.py",
        RAIZ / "ler-runtime" / "knowledge" / "knowledge_graph.json",
    ]
    for arq in arquivos_monitorar:
        if arq.exists():
            tam = tamanho_arquivo_mb(arq)
            if tam > LIMIAR_DISCO_MB:
                alertas.append({
                    "tipo": "disco",
                    "arquivo": str(arq.relative_to(RAIZ)),
                    "tamanho_mb": round(tam, 2),
                    "limiar_mb": LIMIAR_DISCO_MB,
                    "risco": "alto",
                    "mensagem": f"{arq.name} tem {tam:.1f}MB - acima do limiar",
                })
    return alertas


def verificar_historico():
    """Verifica se o historico esta se aproximando do limite."""
    alertas = []
    if HISTORICO.exists():
        try:
            with open(HISTORICO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            total = len(dados)
            if total > LIMIAR_HISTORICO_ENTRADAS:
                alertas.append({
                    "tipo": "saturacao_historico",
                    "entradas": total,
                    "limite": 500,
                    "risco": "medio",
                    "mensagem": f"Historico com {total} entradas - proximo do limite de 500",
                })
        except Exception:
            pass
    return alertas


def verificar_logs():
    """Verifica se ha logs crescendo demais."""
    alertas = []
    if LOG_DIR.exists():
        for arq in LOG_DIR.glob("*.log"):
            tam = tamanho_arquivo_mb(arq)
            if tam > LIMIAR_LOG_MB:
                alertas.append({
                    "tipo": "log_grande",
                    "arquivo": str(arq.relative_to(RAIZ)),
                    "tamanho_mb": round(tam, 2),
                    "risco": "medio",
                    "mensagem": f"Log {arq.name} tem {tam:.1f}MB",
                })
    return alertas


def verificar_restart_watchdog():
    """Verifica restarts frequentes do watchdog (instabilidade)."""
    alertas = []
    if BRIDGE_HISTORICO.exists():
        try:
            with open(BRIDGE_HISTORICO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if not dados:
                return alertas

            # Conta restarts na ultima hora
            agora = time.time()
            uma_hora_atras = agora - 3600
            restarts_recentes = [
                d for d in dados
                if isinstance(d, dict)
                and d.get("timestamp")
                and isinstance(d["timestamp"], (int, float))
                and d["timestamp"] > uma_hora_atras
                and "restart" in d.get("descricao", "").lower()
            ]
            if len(restarts_recentes) >= LIMIAR_RESTARTS:
                alertas.append({
                    "tipo": "instabilidade",
                    "restarts_1h": len(restarts_recentes),
                    "limiar": LIMIAR_RESTARTS,
                    "risco": "alto",
                    "mensagem": f"{len(restarts_recentes)} restarts em 1 hora - ponte instavel",
                })
        except Exception:
            pass
    return alertas


def verificar_scripts_temp():
    """Verifica arquivos temporarios de debug acumulando."""
    alertas = []
    arquivos_debug = list(SCRIPTS.glob("_*.py")) + list(SCRIPTS.glob("dbg_*.py")) + list(SCRIPTS.glob("diag_*.py")) + list(SCRIPTS.glob("patch_*.py")) + list(SCRIPTS.glob("add_*.py"))
    if len(arquivos_debug) > 50:
        alertas.append({
            "tipo": "acumulo_debug",
            "quantidade": len(arquivos_debug),
            "risco": "baixo",
            "mensagem": f"{len(arquivos_debug)} arquivos de debug/acesso - considerar limpeza",
        })
    return alertas


def verificar_memoria_engine():
    """Verifica se o arquivo de memoria esta muito grande."""
    alertas = []
    mem_file = RAIZ / "ler-runtime" / "memory" / "memories.json"
    if mem_file.exists():
        tam = tamanho_arquivo_mb(mem_file)
        if tam > 10:
            alertas.append({
                "tipo": "memoria_grande",
                "arquivo": str(mem_file.relative_to(RAIZ)),
                "tamanho_mb": round(tam, 2),
                "risco": "medio",
                "mensagem": f"Memoria com {tam:.1f}MB - pode precisar de poda",
            })
    return alertas


def prever_completo():
    """Executa todas as verificacoes e gera predicoes."""
    todas_verificacoes = [
        ("disco", verificar_disco),
        ("historico", verificar_historico),
        ("logs", verificar_logs),
        ("restarts", verificar_restart_watchdog),
        ("debug", verificar_scripts_temp),
        ("memoria", verificar_memoria_engine),
    ]

    alertas = []
    for nome, func in todas_verificacoes:
        try:
            resultado = func()
            if resultado:
                alertas.extend(resultado)
        except Exception as e:
            alertas.append({
                "tipo": "erro_verificacao",
                "modulo": nome,
                "risco": "baixo",
                "mensagem": f"Erro ao verificar {nome}: {e}",
            })

    # Ordena por risco
    ordem_risco = {"alto": 0, "medio": 1, "baixo": 2}
    alertas.sort(key=lambda x: ordem_risco.get(x.get("risco", "baixo"), 3))

    return alertas


def salvar_predicao(alertas):
    """Salva as predicoes em arquivo."""
    dados = {
        "gerado_em": datetime.now().isoformat(),
        "total_alertas": len(alertas),
        "alertas": alertas,
        "sistema_saudavel": len(alertas) == 0,
    }
    with open(PREDICAO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return PREDICAO


def main():
    alertas = prever_completo()
    caminho = salvar_predicao(alertas)

    if "--report" in sys.argv:
        print("=== PREVISAO DE GARGALOS ===")
        print(f"Verificado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total de alertas: {len(alertas)}")
        if not alertas:
            print("Sistema saudavel. Nenhum gargalo previsto.")
        else:
            for a in alertas:
                print(f"  [{a['risco'].upper()}] {a['tipo']}: {a['mensagem']}")
        print(f"\nSalvo em: {caminho}")
    else:
        if alertas:
            print(f"{len(alertas)} alertas detectados.")
            for a in alertas:
                print(f"  [{a['risco']}] {a['mensagem']}")
        else:
            print("Sistema saudavel. Nenhum gargalo previsto.")
        print(f"Predicao salva em: {caminho}")


if __name__ == "__main__":
    main()
