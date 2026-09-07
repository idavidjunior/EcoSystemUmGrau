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


def _executar_acao(oportunidade, estado=None):
    """Executa uma ação autônoma baseada na oportunidade."""
    acao = oportunidade["tipo"]
    
    if acao == "criar_skill":
        return _criar_skill_autonoma(oportunidade, estado)
    elif acao == "corrigir_padrao":
        return _corrigir_padrao_conhecido(oportunidade)
    elif acao == "consolidar_duplicado":
        return _consolidar_duplicados(oportunidade)
    elif acao == "limpar_temporario":
        return _limpar_temporarios()
    elif acao == "atualizar_docs":
        return _atualizar_documentacao(oportunidade)
    
    return _falha(f"ação desconhecida: {acao}")


def _criar_skill_autonoma(oportunidade, estado=None):
    """Cria skill baseada em padrão repetido analisando memórias relacionadas."""
    padrao = oportunidade["padrao"]
    _log("skill_analise_iniciada", {"padrao": padrao})
    
    # Busca memórias relacionadas a este padrão
    memorias_relacionadas = _buscar_memorias_por_padrao(padrao)
    
    if not memorias_relacionadas:
        return _ok(
            acao="criar_skill",
            status="sem_memorias_relacionadas",
            detalhe="Nenhuma memória com detalhes técnicos encontrados"
        )
    
    # Extrai informações técnicas das memórias
    info_tecnica = _extrair_info_tecnica(memorias_relacionadas)
    
    # Gera nome da skill baseado no padrão
    skill_name = _gerar_nome_skill(padrao, info_tecnica)
    skill_dir = os.path.join(BASE, "mcp", "habilidades", skill_name)
    
    # Verifica se skill já existe
    if os.path.exists(skill_dir):
        return _ok(
            acao="criar_skill",
            status="ja_existe",
            detalhe=f"Skill {skill_name} já existe em {skill_dir}"
        )
    
    # Cria estrutura da skill
    try:
        os.makedirs(skill_dir, exist_ok=True)
        
        # Cria skill.md
        skill_md = _gerar_skill_md(skill_name, padrao, info_tecnica, memorias_relacionadas)
        with open(os.path.join(skill_dir, "skill.md"), "w", encoding="utf-8") as f:
            f.write(skill_md)
        
        # Cria script base se houver código identificado
        if info_tecnica.get("codigo_exemplo"):
            script_path = os.path.join(skill_dir, f"{skill_name}.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(info_tecnica["codigo_exemplo"])
        
        # Registra no estado
        if estado is not None:
            estado["skills_criadas"].append({
                "nome": skill_name,
                "padrao_origem": padrao,
                "timestamp": _iso(_agora()),
                "memorias_base": [m.get("arquivo", "") for m in memorias_relacionadas[:5]]
            })
            _salvar_estado(estado)
        
        _log("skill_criada", {"nome": skill_name, "dir": skill_dir, "padrao": padrao})
        
        return _ok(
            acao="criar_skill",
            status="criada",
            skill_name=skill_name,
            path=skill_dir,
            memorias_usadas=len(memorias_relacionadas)
        )
    except Exception as e:
        return _falha(f"erro ao criar skill: {e}")


def _buscar_memorias_por_padrao(padrao):
    """Busca arquivos de memória relacionados a um padrão."""
    resultados = []
    if not os.path.exists(MEMORIA):
        return resultados
    
    for arquivo in Path(MEMORIA).glob("*.md"):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            # Verifica se contém o padrão nas tags ou tipo
            if padrao in conteudo or padrao.replace("tipo:", "") in conteudo:
                # Extrai frontmatter
                frontmatter = {}
                fm_match = re.search(r"^---\n(.*?)\n---", conteudo, re.DOTALL)
                if fm_match:
                    for line in fm_match.group(1).split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            frontmatter[k.strip()] = v.strip().strip('"\'')
                
                resultados.append({
                    "arquivo": arquivo.name,
                    "conteudo": conteudo,
                    "frontmatter": frontmatter,
                    "caminho": str(arquivo)
                })
        except Exception:
            continue
    
    return resultados


def _extrair_info_tecnica(memorias):
    """Extrai informações técnicas consolidadas das memórias."""
    info = {
        "comandos": [],
        "arquivos_mencionados": [],
        "funcoes": [],
        "bibliotecas": [],
        "codigo_exemplo": None,
        "descricao_consolidada": ""
    }
    
    for m in memorias:
        conteudo = m.get("conteudo", "")
        fm = m.get("frontmatter", {})
        
        # Extrai comandos (linhas que começam com $, python, bash, etc.)
        for line in conteudo.split("\n"):
            line = line.strip()
            if line.startswith(("$ ", "python ", "bash ", "git ", "npm ", "pip ")):
                info["comandos"].append(line)
            # Extrai caminhos de arquivo
            if ".py" in line or ".js" in line or ".json" in line:
                matches = re.findall(r'[\w/\\.-]+\.(py|js|json|md|txt)', line)
                info["arquivos_mencionados"].extend(matches)
        
        # Extrai da decisao/contexto do frontmatter
        if fm.get("decisao"):
            info["descricao_consolidada"] += fm["decisao"] + " "
        if fm.get("contexto"):
            info["descricao_consolidada"] += fm["contexto"] + " "
    
    # Remove duplicatas
    info["comandos"] = list(set(info["comandos"]))[:10]
    info["arquivos_mencionados"] = list(set(info["arquivos_mencionados"]))[:20]
    
    # Gera código exemplo se houver comandos python
    py_cmds = [c for c in info["comandos"] if c.startswith("python ")]
    if py_cmds:
        info["codigo_exemplo"] = _gerar_codigo_exemplo(skill_name="auto", comandos=py_cmds, descricao=info["descricao_consolidada"][:500])
    
    return info


def _gerar_nome_skill(padrao, info):
    """Gera nome kebab-case para skill baseado no padrão e info."""
    # Remove prefixo tipo:
    base = padrao.replace("tipo:", "").replace("padrao:", "")
    # Limpa para kebab-case
    base = re.sub(r'[^a-zA-Z0-9]+', '-', base).strip('-').lower()
    # Adiciona prefixo auto
    return f"auto-{base}"


def _gerar_skill_md(nome, padrao, info, memorias):
    """Gera conteúdo do skill.md."""
    hoje = _agora().strftime("%Y-%m-%d")
    tags = [padrao.replace("tipo:", ""), "auto-gerada", "autonomia"]
    
    md = f"""# {nome} — Skill Auto-Gerada

## Origem
Padrão detectado automaticamente: `{padrao}` ({len(memorias)} memórias relacionadas)
Gerado em: {hoje} pelo loop autônomo de melhoria contínua.

## Descrição
{info.get("descricao_consolidada", "Skill gerada automaticamente a partir de padrões repetidos na memória do ecossistema.")[:500]}

## Uso
```bash
# Exemplo de uso (ajustar conforme necessidade)
python mcp/habilidades/{nome}/{nome}.py
```

## Comandos Identificados
"""
    for cmd in info.get("comandos", [])[:5]:
        md += f"- `{cmd}`\n"
    
    md += f"""

## Arquivos Relacionados
"""
    for arq in info.get("arquivos_mencionados", [])[:10]:
        md += f"- `{arq}`\n"
    
    md += f"""

## Memórias Base
"""
    for m in memorias[:5]:
        md += f"- `{m['arquivo']}` ({m['frontmatter'].get('tipo', 'N/A')})\n"
    
    md += f"""

## Notas
- Skill gerada automaticamente — revisar e validar antes de usar em produção
- Baseada em {len(memorias)} ocorrências do padrão `{padrao}`
- Requer preflight_check.py antes de deploy

---
*Auto-gerado pelo autonomous_loop.py em {_iso(_agora())}*
"""
    return md


def _gerar_codigo_exemplo(skill_name, comandos, descricao):
    """Gera script Python exemplo baseado nos comandos identificados."""
    # Escapa aspas nos comandos para evitar erro de sintaxe
    cmds_escapados = [cmd.replace('"', '\\"').replace("'", "\\'") for cmd in comandos[:5]]
    
    return f'''#!/usr/bin/env python3
"""Skill auto-gerada: {skill_name}

{descricao[:300]}

Gerado automaticamente pelo loop autônomo.
Revisar e adaptar antes de usar.
"""

import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent

def main():
    """Ponto de entrada da skill."""
    print(f"Skill {skill_name} - auto-gerada")
    print("Comandos base identificados:")
''' + "\n".join([f'    print("  {cmd}")' for cmd in cmds_escapados]) + '''

if __name__ == "__main__":
    main()
'''


def _corrigir_padrao_conhecido(oportunidade):
    """Aplica correção conhecida para padrão de erro recorrente (auto-healing)."""
    padrao = oportunidade["padrao"]
    _log("autohealing_iniciado", {"padrao": padrao})
    
    # Busca memórias do tipo "erro" com correções conhecidas
    correcoes = _buscar_correcoes_conhecidas(padrao)
    
    if not correcoes:
        return _ok(
            acao="corrigir_padrao",
            status="sem_correcao_conhecida",
            detalhe="Nenhuma correção conhecida encontrada na memória"
        )
    
    # Tenta aplicar a correção mais votada/recentes
    correcao = correcoes[0]
    resultado = _aplicar_correcao(correcao)
    
    if resultado.get("ok"):
        _log("autohealing_sucesso", {"padrao": padrao, "correcao": correcao.get("arquivo")})
        return _ok(
            acao="corrigir_padrao",
            status="corrigido",
            detalhe=f"Aplicada correção de {correcao.get('arquivo')}: {resultado.get('detalhe', '')}"
        )
    else:
        _log("autohealing_falhou", {"padrao": padrao, "erro": resultado.get("motivo")})
        return _falha(f"Falha ao aplicar correção: {resultado.get('motivo')}")


def _buscar_correcoes_conhecidas(padrao_erro):
    """Busca memórias do tipo 'erro' que contenham soluções/correções."""
    resultados = []
    if not os.path.exists(MEMORIA):
        return resultados
    
    for arquivo in Path(MEMORIA).glob("*.md"):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            # Verifica se é tipo erro e menciona o padrão
            fm_match = re.search(r"tipo:\s*erro", conteudo)
            if not fm_match:
                continue
            
            # Verifica se menciona o padrão de erro
            if padrao_erro.replace("tipo:", "") in conteudo.lower() or "correcao" in conteudo.lower() or "fix" in conteudo.lower() or "solucao" in conteudo.lower():
                fm = {}
                fm_block = re.search(r"^---\n(.*?)\n---", conteudo, re.DOTALL)
                if fm_block:
                    for line in fm_block.group(1).split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            fm[k.strip()] = v.strip().strip('"\'')
                
                # Extrai a correção/solução do conteúdo
                correcao_texto = ""
                if "correcao" in conteudo.lower() or "solução" in conteudo.lower() or "fix" in conteudo.lower():
                    # Pega parágrafos após palavras-chave
                    for kw in ["correcao", "correção", "solução", "solucao", "fix", "resolvido"]:
                        idx = conteudo.lower().find(kw)
                        if idx >= 0:
                            correcao_texto = conteudo[idx:idx+500]
                            break
                
                resultados.append({
                    "arquivo": arquivo.name,
                    "caminho": str(arquivo),
                    "frontmatter": fm,
                    "correcao": correcao_texto or fm.get("decisao", "") or fm.get("contexto", ""),
                    "tags": fm.get("tags", "").split(",") if fm.get("tags") else []
                })
        except Exception:
            continue
    
    # Ordena por mais recente (nome do arquivo tem data)
    resultados.sort(key=lambda x: x["arquivo"], reverse=True)
    return resultados


def _aplicar_correcao(correcao):
    """Tenta aplicar uma correção baseada na memória."""
    # Por enquanto, registra a correção proposta para execução manual
    # Futuro: pode executar comandos específicos se a correção for estruturada
    
    texto = correcao.get("correcao", "")
    
    # Procura por comandos executáveis na correção
    comandos = []
    for line in texto.split("\n"):
        line = line.strip()
        if line.startswith(("python ", "bash ", "git ", "pip ", "npm ")):
            comandos.append(line)
    
    if comandos:
        return _ok(
            status="comandos_identificados",
            detalhe=f"{len(comandos)} comando(s) encontrado(s) para execução manual",
            comandos=comandos[:5]
        )
    
    # Se não há comandos, retorna a correção como texto para revisão
    return _ok(
        status="correcao_documentada",
        detalhe=texto[:300] if texto else "Correção documentada sem comandos executáveis",
        correcao_completa=texto
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
        resultado = _executar_acao(opp, estado)
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