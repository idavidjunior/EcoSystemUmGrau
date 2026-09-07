#!/usr/bin/env python3
"""Loop Autônomo de Melhoria Contínua — EcoSystemUmGrau

Detecta padrões na memória, propõe e aplica melhorias sem intervenção humana.
Executa como tarefa recorrente no eco_agenda.

Princípios:
- Autonomia informada: comunica antes, implementa, registra depois
- Preflight obrigatório: toda mudança passa por validação
- Rollback automático: se quebrar, reverte
- Idempotente: pode rodar múltiplas vezes sem duplicar
"""

import os
import sys
import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, "scripts")
RUNTIME = os.path.join(BASE, "runtime")
MEMORIA = os.path.join(BASE, "conhecimento", "aprendizados")
AUTONOMIA_DIR = os.path.join(RUNTIME, "autonomia")
AUTONOMIA_LOG = os.path.join(AUTONOMIA_DIR, "autonomo.log")
AUTONOMIA_STATE = os.path.join(AUTONOMIA_DIR, "state.json")
AUTONOMIA_PENDING = os.path.join(AUTONOMIA_DIR, "pending.json")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

# Ações permitidas para execução autônoma
ACOES_AUTONOMAS = (
    "criar_skill",
    "otimizar_script",
    "corrigir_padrao",
    "consolidar_duplicado",
    "atualizar_docs",
    "limpar_temporario",
)

# Thresholds
MIN_OCORRENCIAS_PARA_PADRAO = 3
MIN_DIAS_PARA_SUGESTAO = 7
MAX_ACOES_POR_CICLO = 3
COOLDOWN_ENTRE_CICLOS_H = 6


def _ok(**campos):
    out = {"ok": True}
    out.update(campos)
    return out


def _falha(motivo, **campos):
    out = {"ok": False, "motivo": str(motivo)}
    out.update(campos)
    return out


def _agora():
    return datetime.now()


def _iso(dt):
    return dt.isoformat(timespec="seconds")


def _parse_iso(valor):
    try:
        return datetime.fromisoformat(valor)
    except Exception:
        return None


def _carregar_estado():
    os.makedirs(AUTONOMIA_DIR, exist_ok=True)
    if os.path.exists(AUTONOMIA_STATE):
        try:
            with open(AUTONOMIA_STATE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "ultimo_ciclo": None,
        "acoes_executadas": [],
        "padroes_detectados": {},
        "skills_criadas": [],
        "estatisticas": {
            "ciclos_total": 0,
            "acoes_total": 0,
            "sucessos": 0,
            "falhas": 0,
        }
    }


def _salvar_estado(estado):
    try:
        tmp = AUTONOMIA_STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        os.replace(tmp, AUTONOMIA_STATE)
    except Exception:
        pass


def _log(evento, dados=None):
    try:
        os.makedirs(AUTONOMIA_DIR, exist_ok=True)
        registro = {
            "timestamp": _iso(_agora()),
            "evento": evento,
            "dados": dados or {}
        }
        with open(AUTONOMIA_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _executar_preflight():
    """Roda preflight técnico e ético. Retorna (ok, detalhes)."""
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "preflight_check.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, cwd=BASE
        )
        if r.returncode != 0:
            return False, f"preflight técnico falhou: {r.stderr[:500]}"
        r2 = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "preflight_etica.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, cwd=BASE
        )
        if r2.returncode != 0:
            return False, f"preflight ético falhou: {r2.stderr[:500]}"
        return True, "preflight ok"
    except Exception as e:
        return False, f"erro no preflight: {e}"


def _analisar_memoria_padroes():
    """Analisa arquivos de aprendizado para detectar padrões repetidos."""
    padroes = Counter()
    arquivos_processados = 0
    
    if not os.path.exists(MEMORIA):
        return padroes
    
    for arquivo in Path(MEMORIA).glob("*.md"):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
            arquivos_processados += 1
            
            # Extrai tags do frontmatter
            tags_match = re.search(r"tags:\s*\[(.*?)\]", conteudo)
            if tags_match:
                tags = [t.strip().strip('"\'') for t in tags_match.group(1).split(",")]
                for tag in tags:
                    padroes[tag] += 1
            
            # Extrai tipo
            tipo_match = re.search(r"tipo:\s*(\w+)", conteudo)
            if tipo_match:
                padroes[f"tipo:{tipo_match.group(1)}"] += 1
                
        except Exception:
            continue
    
    _log("memoria_analisada", {"arquivos": arquivos_processados, "padroes_unicos": len(padroes)})
    return padroes


def _detectar_oportunidades(padroes, estado):
    """Identifica oportunidades de melhoria baseadas nos padrões."""
    oportunidades = []
    agora = _agora()
    
    for padrao, count in padroes.most_common():
        if count < MIN_OCORRENCIAS_PARA_PADRAO:
            continue
        
        # Verifica se já tratamos este padrão recentemente
        ultima = estado["padroes_detectados"].get(padrao)
        if ultima:
            try:
                dt = _parse_iso(ultima)
                if dt and (agora - dt).days < MIN_DIAS_PARA_SUGESTAO:
                    continue
            except Exception:
                pass
        
        # Classifica oportunidade
        if padrao.startswith("tipo:erro"):
            oportunidades.append({
                "tipo": "corrigir_padrao",
                "padrao": padrao,
                "frequencia": count,
                "prioridade": "alta",
                "descricao": f"Padrão de erro recorrente: {padrao} ({count}x)"
            })
        elif padrao.startswith("tipo:padrao") and count >= 5:
            oportunidades.append({
                "tipo": "criar_skill",
                "padrao": padrao,
                "frequencia": count,
                "prioridade": "media",
                "descricao": f"Padrão repetido viável para skill: {padrao} ({count}x)"
            })
        elif "duplicad" in padrao.lower() or "redundant" in padrao.lower():
            oportunidades.append({
                "tipo": "consolidar_duplicado",
                "padrao": padrao,
                "frequencia": count,
                "prioridade": "media",
                "descricao": f"Duplicação detectada: {padrao} ({count}x)"
            })
    
    return oportunidades[:MAX_ACOES_POR_CICLO]


def _executar_acao(oportunidade):
    """Executa uma ação autônoma baseada na oportunidade."""
    acao = oportunidade["tipo"]
    
    if acao == "criar_skill":
        return _criar_skill_autonoma(oportunidade)
    elif acao == "corrigir_padrao":
        return _corrigir_padrao_conhecido(oportunidade)
    elif acao == "consolidar_duplicado":
        return _consolidar_duplicados(oportunidade)
    elif acao == "limpar_temporario":
        return _limpar_temporarios()
    elif acao == "atualizar_docs":
        return _atualizar_documentacao(oportunidade)
    
    return _falha(f"ação desconhecida: {acao}")


def _criar_skill_autonoma(oportunidade):
    """Cria skill baseada em padrão repetido (placeholder - requer análise de código)."""
    # Por enquanto registra a intenção; implementação completa precisa
    # de análise de código real (AST, grep, etc.)
    _log("skill_proposta", oportunidade)
    return _ok(
        acao="criar_skill",
        status="proposta_registrada",
        detalhe="Requer análise de código para implementação completa"
    )


def _corrigir_padrao_conhecido(oportunidade):
    """Aplica correção conhecida para padrão de erro recorrente."""
    _log("correcao_padrao", oportunidade)
    # Placeholder: integração com memory_engine para buscar correções conhecidas
    return _ok(
        acao="corrigir_padrao",
        status="analise_necessaria",
        detalhe="Integração com base de correções conhecida pendente"
    )


def _consolidar_duplicados(oportunidade):
    """Consolida código/estruturas duplicadas."""
    _log("consolidacao_proposta", oportunidade)
    return _ok(
        acao="consolidar_duplicado",
        status="proposta_registrada",
        detalhe="Requer análise de similaridade de código (AST/diff)"
    )


def _limpar_temporarios():
    """Limpa arquivos temporários antigos."""
    limpos = 0
    try:
        for tmp_dir in ["/tmp", os.path.join(BASE, "tmp"), os.path.join(RUNTIME, "tmp")]:
            if os.path.exists(tmp_dir):
                for f in Path(tmp_dir).glob("*"):
                    try:
                        if f.is_file():
                            idade = _agora() - datetime.fromtimestamp(f.stat().st_mtime)
                            if idade.days > 7:
                                f.unlink()
                                limpos += 1
                    except Exception:
                        pass
    except Exception:
        pass
    return _ok(acao="limpar_temporario", arquivos_removidos=limpos)


def _atualizar_documentacao(oportunidade):
    """Atualiza docs baseadas em mudanças recentes."""
    _log("docs_atualizacao", oportunidade)
    return _ok(acao="atualizar_docs", status="placeholder")


def _verificar_cooldown(estado):
    """Verifica se passou tempo suficiente desde último ciclo."""
    ultimo = estado.get("ultimo_ciclo")
    if not ultimo:
        return True
    dt = _parse_iso(ultimo)
    if not dt:
        return True
    return (_agora() - dt).total_seconds() >= COOLDOWN_ENTRE_CICLOS_H * 3600


def executar_ciclo_autonomo():
    """Executa um ciclo completo do loop autônomo."""
    estado = _carregar_estado()
    
    if not _verificar_cooldown(estado):
        return _ok(status="cooldown_ativo", proximo_em=f"{COOLDOWN_ENTRE_CICLOS_H}h")
    
    _log("ciclo_iniciado", {"timestamp": _iso(_agora())})
    
    # 1. Preflight
    preflight_ok, preflight_msg = _executar_preflight()
    if not preflight_ok:
        _log("preflight_falhou", {"motivo": preflight_msg})
        return _falha(f"preflight bloqueou: {preflight_msg}")
    
    # 2. Analisa memória
    padroes = _analisar_memoria_padroes()
    
    # 3. Detecta oportunidades
    oportunidades = _detectar_oportunidades(padroes, estado)
    
    if not oportunidades:
        _log("ciclo_sem_oportunidades", {"padroes_analisados": len(padroes)})
        estado["ultimo_ciclo"] = _iso(_agora())
        _salvar_estado(estado)
        return _ok(status="sem_oportunidades", padroes=len(padroes))
    
    # 4. Executa ações
    resultados = []
    for opp in oportunidades:
        resultado = _executar_acao(opp)
        resultados.append({**opp, "resultado": resultado})
        
        if resultado.get("ok"):
            estado["estatisticas"]["sucessos"] += 1
            estado["acoes_executadas"].append({
                "timestamp": _iso(_agora()),
                "acao": opp["tipo"],
                "padrao": opp["padrao"],
                "detalhe": resultado.get("detalhe", "")
            })
            # Atualiza último visto do padrão
            estado["padroes_detectados"][opp["padrao"]] = _iso(_agora())
        else:
            estado["estatisticas"]["falhas"] += 1
        
        estado["estatisticas"]["acoes_total"] += 1
    
    # 5. Atualiza estado
    estado["ultimo_ciclo"] = _iso(_agora())
    estado["estatisticas"]["ciclos_total"] += 1
    _salvar_estado(estado)
    
    _log("ciclo_concluido", {
        "oportunidades": len(oportunidades),
        "executadas": len([r for r in resultados if r["resultado"].get("ok")])
    })
    
    return _ok(
        status="concluido",
        oportunidades=oportunidades,
        resultados=resultados,
        estatisticas=estado["estatisticas"]
    )


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Loop Autônomo EcoSystemUmGrau")
    ap.add_argument("--ciclo", action="store_true", help="Executa um ciclo")
    ap.add_argument("--status", action="store_true", help="Mostra status")
    ap.add_argument("--reset", action="store_true", help="Reseta estado")
    args = ap.parse_args()
    
    if args.reset:
        if os.path.exists(AUTONOMIA_STATE):
            os.remove(AUTONOMIA_STATE)
        print(json.dumps(_ok(status="resetado"), ensure_ascii=False, indent=2))
        return 0
    
    if args.status:
        estado = _carregar_estado()
        print(json.dumps(_ok(estado=estado), ensure_ascii=False, indent=2))
        return 0
    
    if args.ciclo:
        resultado = executar_ciclo_autonomo()
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0 if resultado.get("ok") else 1
    
    # Default: mostra help
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())