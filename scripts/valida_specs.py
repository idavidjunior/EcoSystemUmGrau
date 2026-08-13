#!/usr/bin/env python3
"""Validador de specs do EcoSystemUmGrau (camada spec-driven development).

Conferencia se cada spec em `specs/*.spec.md` esta bem formada e se o codigo
realmente implementa o que a spec promete:

1. Frontmatter YAML (id, versao, status, componente, data; tags opcional).
2. 11 secoes obrigatorias.
3. O `componente` referenciado existe no disco.
4. Cada arquivo listado em `Testes Relacionados` existe.
5. Criterios de aceitacao com prefixos reconheciveis:
   - `[arquivo:<path>]`  -> o arquivo deve existir
   - `[comando:<cmd>]`   -> o comando deve retornar exit 0
   - texto livre         -> verificado manualmente (relatado como "manual")
6. Specs com `status: deprecada` sao relatadas e puladas (historico).

Uso:
  python scripts/valida_specs.py                       # todas as specs
  python scripts/valida_specs.py --spec specs/x.spec.md  # uma spec
  python scripts/valida_specs.py --json                # saida em JSON

Exit code: 0 = ok / 1 = falhas.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS_DIR = os.path.join(BASE, "specs")

SECOES_OBRIGATORIAS = [
    "Objetivo",
    "Requisitos",
    "Restrições",
    "Dependências",
    "Premissas",
    "Entradas e Saídas",
    "Casos de Borda",
    "Critérios de Aceitação",
    "Definition of Done",
    "Riscos",
    "Testes Relacionados",
]

STATUS_VALIDOS = {"proposta", "ativa", "deprecada"}

FRONTMATTER_OBRIGATORIO = ["id", "versao", "status", "componente", "data"]
FRONTMATTER_OPCIONAL = ["tags"]


def _sem_acentos(texto):
    """Remove acentos para comparacao flexivel de titulos de secao."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


SECOES_NORMALIZADAS = {_sem_acentos(s): s for s in SECOES_OBRIGATORIAS}


def _ler_arquivo(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _parse_frontmatter(texto):
    """Extrai campos do bloco --- ... --- no topo do arquivo."""
    if not texto.startswith("---"):
        return None
    fim = texto.find("\n---", 3)
    if fim == -1:
        return None
    bloco = texto[3:fim]
    campos = {}
    for linha in bloco.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if ":" in linha:
            chave, _, valor = linha.partition(":")
            campos[chave.strip()] = valor.strip()
    return campos


def _extrair_secoes(texto):
    """Mapa titulo_normalizado -> lista de linhas da secao."""
    secoes = {}
    atual = None
    for linha in texto.splitlines():
        if linha.startswith("## "):
            atual = _sem_acentos(linha[3:].strip())
            secoes.setdefault(atual, [])
        elif atual is not None:
            secoes[atual].append(linha)
    return secoes


def _extrair_itens(secoes, titulo):
    """Itens de lista (linhas iniciadas com '-') de uma secao."""
    norm = _sem_acentos(titulo)
    linhas = secoes.get(norm, [])
    itens = []
    for linha in linhas:
        l = linha.strip()
        if l.startswith("- "):
            itens.append(l[2:].strip())
    return itens


def _checar_criterio(item, base):
    """Verifica um criterio de aceitacao. Retorna (status, detalhe)."""
    m = re.match(r"^\[arquivo:([^\]]+)\]", item)
    if m:
        caminho = m.group(1).strip()
        full = os.path.join(base, caminho) if not os.path.isabs(caminho) else caminho
        if os.path.isfile(full):
            return "OK", "arquivo existe"
        return "FALHA", "arquivo nao encontrado: %s" % caminho
    m = re.match(r"^\[comando:([^\]]+)\]", item)
    if m:
        cmd = m.group(1).strip()
        try:
            r = subprocess.run(cmd, shell=True, cwd=base, timeout=120)
        except Exception as exc:  # noqa: BLE001
            return "FALHA", "comando nao executou: %s" % exc
        if r.returncode == 0:
            return "OK", "comando retornou exit 0"
        return "FALHA", "comando retornou exit %d" % r.returncode
    return "MANUAL", item


def _validar_arquivo_spec(path, base):
    """Valida uma unica spec. Retorna dict de resultado.

    Para status 'proposta', o componente pode ainda nao existir (a spec documenta
    o que sera criado): a checagem vira AVISO. Para 'ativa', e FALHA."""
    nome = os.path.basename(path)
    resultado = {
        "arquivo": nome,
        "caminho": os.path.relpath(path, base),
        "checks": [],
        "criterios": [],
        "status_spec": None,
        "passou": False,
        "pulada": False,
    }

    if not os.path.isfile(path):
        resultado["checks"].append({"tipo": "arquivo", "status": "FALHA",
                                    "detalhe": "spec nao encontrada"})
        return resultado

    texto = _ler_arquivo(path)
    campos = _parse_frontmatter(texto)

    # Frontmatter
    if campos is None:
        resultado["checks"].append({"tipo": "frontmatter", "status": "FALHA",
                                    "detalhe": "bloco --- ... --- ausente"})
    else:
        faltando = [c for c in FRONTMATTER_OBRIGATORIO if not campos.get(c)]
        if faltando:
            resultado["checks"].append({"tipo": "frontmatter", "status": "FALHA",
                                        "detalhe": "campos ausentes: %s" % ", ".join(faltando)})
        else:
            resultado["checks"].append({"tipo": "frontmatter", "status": "OK",
                                        "detalhe": "campos presentes"})
        status_spec = campos.get("status", "").strip().lower()
        if status_spec not in STATUS_VALIDOS:
            resultado["checks"].append({"tipo": "status", "status": "FALHA",
                                        "detalhe": "status invalido: %s" % campos.get("status")})
        else:
            resultado["checks"].append({"tipo": "status", "status": "OK",
                                        "detalhe": "status=%s" % status_spec})
        resultado["status_spec"] = status_spec

    # Se deprecada, relata e pula (historico)
    if resultado["status_spec"] == "deprecada":
        resultado["pulada"] = True
        resultado["passou"] = True
        return resultado

    secoes = _extrair_secoes(texto)

    # Secoes obrigatorias
    ausentes = [SECOES_NORMALIZADAS[s] for s in SECOES_NORMALIZADAS
                if s not in secoes]
    if ausentes:
        resultado["checks"].append({"tipo": "secoes", "status": "FALHA",
                                    "detalhe": "secoes ausentes: %s" % ", ".join(ausentes)})
    else:
        resultado["checks"].append({"tipo": "secoes", "status": "OK",
                                    "detalhe": "11 secoes presentes"})

    # Componente existe
    # Em proposta, o componente pode ainda nao existir (a spec documenta o que sera criado):
    # vira AVISO; para ativa, e FALHA.
    componente = (campos or {}).get("componente", "")
    if componente:
        full = os.path.join(base, componente) if not os.path.isabs(componente) else componente
        if os.path.exists(full):
            resultado["checks"].append({"tipo": "componente", "status": "OK",
                                        "detalhe": componente})
        elif resultado["status_spec"] == "proposta":
            resultado["checks"].append({"tipo": "componente", "status": "AVISO",
                                        "detalhe": "componente nao existe (proposta): %s" % componente})
        else:
            resultado["checks"].append({"tipo": "componente", "status": "FALHA",
                                        "detalhe": "componente nao encontrado: %s" % componente})
    else:
        resultado["checks"].append({"tipo": "componente", "status": "FALHA",
                                    "detalhe": "campo componente ausente"})

    # Testes relacionados existem
    testes = _extrair_itens(secoes, "Testes Relacionados")
    if not testes:
        resultado["checks"].append({"tipo": "testes", "status": "FALHA",
                                    "detalhe": "nenhum teste listado"})
    else:
        faltantes = []
        for t in testes:
            if "(" in t or ")" in t or "<" in t:
                continue  # exemplo de template, nao conta
            full = os.path.join(base, t) if not os.path.isabs(t) else t
            if not os.path.exists(full):
                faltantes.append(t)
        if faltantes:
            resultado["checks"].append({"tipo": "testes", "status": "FALHA",
                                        "detalhe": "testes nao encontrados: %s" % ", ".join(faltantes)})
        else:
            resultado["checks"].append({"tipo": "testes", "status": "OK",
                                        "detalhe": "%d teste(s)" % len(testes)})

    # Criterios de aceitacao
    criterios = _extrair_itens(secoes, "Critérios de Aceitação")
    if not criterios:
        resultado["checks"].append({"tipo": "criterios", "status": "FALHA",
                                    "detalhe": "nenhum criterio listado"})
    else:
        resultado["criterios"] = [{"texto": c, "status": s, "detalhe": d}
                                  for c, (s, d) in
                                  ((c, _checar_criterio(c, base)) for c in criterios)]
        falhas = [c for c in resultado["criterios"] if c["status"] == "FALHA"]
        if falhas:
            resultado["checks"].append({"tipo": "criterios", "status": "FALHA",
                                        "detalhe": "%d criterio(s) com falha" % len(falhas)})
        else:
            resultado["checks"].append({"tipo": "criterios", "status": "OK",
                                        "detalhe": "%d criterio(s)" % len(criterios)})

    falhas = [c for c in resultado["checks"] if c["status"] == "FALHA"]
    resultado["passou"] = not falhas
    return resultado


def _validar_tudo(specs_dir):
    """Valida todas as specs em specs/. Retorna lista de resultados.

    `specs_dir` localiza os arquivos .spec.md; a base de resolucao de
    caminhos (componente, testes, criterios) e sempre a raiz do ecossistema
    (BASE), nao o diretorio de specs.
    """
    resultados = []
    if not os.path.isdir(specs_dir):
        return resultados
    for nome in sorted(os.listdir(specs_dir)):
        if nome.endswith(".spec.md"):
            resultados.append(_validar_arquivo_spec(os.path.join(specs_dir, nome), BASE))
    return resultados


def _relatorio_texto(resultados):
    linhas = []
    total = len(resultados)
    ok = sum(1 for r in resultados if r["passou"] and not r["pulada"])
    puladas = sum(1 for r in resultados if r["pulada"])
    falhas = sum(1 for r in resultados if not r["passou"])
    linhas.append("=== VALIDACAO DE SPECS ===")
    linhas.append("")
    if total == 0:
        linhas.append("Nenhuma spec encontrada em %s" % os.path.relpath(base, BASE))
        linhas.append("")
        linhas.append("RESULTADO: FALHA (nenhuma spec)")
        return "\n".join(linhas)
    for r in resultados:
        linhas.append("[%s] %s (status=%s)" % (
            "OK" if r["passou"] else "PULADA" if r["pulada"] else "FALHA",
            r["caminho"], r["status_spec"]))
        for c in r["checks"]:
            linhas.append("    %-4s %s: %s" % (c["status"], c["tipo"], c["detalhe"]))
        for cr in r["criterios"]:
            linhas.append("    %-6s criterio: %s (%s)" % (cr["status"], cr["texto"], cr["detalhe"]))
        linhas.append("")
    linhas.append("Resumo: %d spec(s), %d ok, %d pulada(s), %d com falha" %
                  (total, ok, puladas, falhas))
    linhas.append("RESULTADO: %s" % ("OK" if falhas == 0 else "FALHA"))
    return "\n".join(linhas)


def _relatorio_json(resultados, base):
    total = len(resultados)
    ok = sum(1 for r in resultados if r["passou"] and not r["pulada"])
    puladas = sum(1 for r in resultados if r["pulada"])
    falhas = sum(1 for r in resultados if not r["passou"])
    return json.dumps({
        "specs_dir": os.path.relpath(base, BASE),
        "total": total,
        "ok": ok,
        "puladas": puladas,
        "falhas": falhas,
        "specs": resultados,
    }, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Validador de specs do ecossistema.")
    parser.add_argument("--spec", default=None,
                        help="caminho de uma spec especifica (default: todas)")
    parser.add_argument("--json", action="store_true",
                        help="saida em JSON")
    args = parser.parse_args()

    base = BASE
    if args.spec:
        caminho = os.path.join(base, args.spec) if not os.path.isabs(args.spec) else args.spec
        resultados = [_validar_arquivo_spec(caminho, base)]
    else:
        resultados = _validar_tudo(os.path.join(base, "specs"))

    if args.json:
        saida = _relatorio_json(resultados, base)
    else:
        saida = _relatorio_texto(resultados)
    print(saida)

    falhas = sum(1 for r in resultados if not r["passou"])
    if len(resultados) == 0:
        sys.exit(1)
    sys.exit(1 if falhas > 0 else 0)


if __name__ == "__main__":
    main()
