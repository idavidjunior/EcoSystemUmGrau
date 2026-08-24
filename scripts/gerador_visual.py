#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""gerador_visual.py — Materializa informações em um arquivo HTML temporário.

Uso:
  python scripts/gerador_visual.py --titulo "Tesouro Selic" --tipo kpi \
      --json '{"kpis":[...],"notas":[...]}'
  python scripts/gerador_visual.py --titulo "App X" --tipo mockup --json '{"telas":[...]}'

Tipos: kpi | tabela | barras | mockup | texto
Saída: %TEMP%\\opencode\\visuals\\<tipo>_<data>.html  (ou --salvar <caminho>)
Nunca abre navegador nem servidor. Apenas cria o arquivo.
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',system-ui,sans-serif; background:#0f1117;
       color:#e8eaf0; padding:32px; min-height:100vh; }
.cab { max-width:900px; margin:0 auto 24px; }
.cab h1 { font-size:22px; font-weight:600; }
.cab .sub { color:#8b93a7; font-size:13px; margin-top:4px; }
.grade { max-width:900px; margin:0 auto; display:grid;
         gap:16px; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); }
.card { background:#1a1d27; border:1px solid #262b3a; border-radius:14px;
        padding:20px; }
.kpi .rotulo { font-size:12px; text-transform:uppercase; letter-spacing:.08em;
               color:#8b93a7; }
.kpi .valor { font-size:30px; font-weight:700; margin-top:6px; color:#6ee7a0; }
.kpi .destaque { font-size:12px; color:#8b93a7; margin-top:6px; }
table { width:100%; border-collapse:collapse; }
th,td { text-align:left; padding:10px 12px; font-size:14px;
        border-bottom:1px solid #262b3a; }
th { color:#8b93a7; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
.barra-fundo { background:#262b3a; border-radius:8px; height:22px;
               margin-top:6px; overflow:hidden; }
.barra-valor { background:linear-gradient(90deg,#4f8cff,#6ee7a0);
               height:100%; border-radius:8px; min-width:4px; }
.barra-item { margin-bottom:14px; }
.barra-item .linha { display:flex; justify-content:space-between; font-size:14px; }
.notas { max-width:900px; margin:20px auto 0; }
.notas li { list-style:none; padding:10px 14px; background:#1a1d27;
            border-left:3px solid #4f8cff; border-radius:6px; margin-bottom:8px;
            font-size:14px; color:#c6cbd9; }
.celular { width:300px; margin:0 auto; background:#12141c;
           border:2px solid #2c3345; border-radius:28px; padding:18px 14px; }
.tela-titulo { text-align:center; font-weight:600; margin-bottom:14px; }
.tela-item { background:#1a1d27; border-radius:10px; padding:12px;
             margin-bottom:8px; font-size:13px; color:#c6cbd9; }
.tela-item b { color:#6ee7a0; }
.rodape { max-width:900px; margin:24px auto 0; text-align:center;
          color:#586074; font-size:11px; }
"""

RODAPE = ("Gerado pelo EcoSystemUmGrau em {} — arquivo temporário, "
          "sem servidor e sem navegador").format


def _pagina(titulo: str, corpo: str) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return (
        "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{_esc(titulo)}</title>\n"
        f"<style>{BASE_CSS}</style>\n</head>\n<body>\n"
        f"<div class=\"cab\"><h1>{_esc(titulo)}</h1>"
        f"<div class=\"sub\">{agora}</div></div>\n"
        f"{corpo}\n"
        f"<div class=\"rodape\">{RODAPE(agora)}</div>\n</body>\n</html>\n"
    )


def _esc(texto) -> str:
    return str(texto).replace("&", "&amp;").replace("<", "&lt;") \
                     .replace(">", "&gt;")


def _render_kpi(dados: dict) -> str:
    corpo = "<div class=\"grade\">"
    for k in dados.get("kpis", []):
        destaque = ""
        if k.get("destaque"):
            destaque = (f"<div class=\"destaque\">{_esc(k['destaque'])}</div>")
        corpo += (
            "<div class=\"card kpi\">"
            f"<div class=\"rotulo\">{_esc(k.get('rotulo',''))}</div>"
            f"<div class=\"valor\">{_esc(k.get('valor',''))}</div>"
            f"{destaque}</div>"
        )
    corpo += "</div>"
    return _com_notas(corpo, dados)


def _render_tabela(dados: dict) -> str:
    colunas = dados.get("colunas", [])
    linhas = dados.get("linhas", [])
    cab = "".join(f"<th>{_esc(c)}</th>" for c in colunas)
    corpo_linhas = ""
    for linha in linhas:
        celulas = "".join(f"<td>{_esc(c)}</td>" for c in linha)
        corpo_linhas += f"<tr>{celulas}</tr>"
    corpo = (
        "<div class=\"grade\" style=\"grid-template-columns:1fr\">"
        "<div class=\"card\"><table>"
        f"<thead><tr>{cab}</tr></thead><tbody>{corpo_linhas}</tbody>"
        "</table></div></div>"
    )
    return _com_notas(corpo, dados)


def _render_barras(dados: dict) -> str:
    itens = dados.get("itens", [])
    maximo = max([abs(i.get("valor", 0)) for i in itens] or [1]) or 1
    blocos = ""
    for i in itens:
        pct = round(abs(i.get("valor", 0)) / maximo * 100, 1)
        blocos += (
            "<div class=\"barra-item\">"
            "<div class=\"linha\">"
            f"<span>{_esc(i.get('rotulo',''))}</span>"
            f"<span>{_esc(i.get('texto',''))}</span>"
            "</div>"
            f"<div class=\"barra-fundo\"><div class=\"barra-valor\" "
            f"style=\"width:{pct}%\"></div></div></div>"
        )
    corpo = ("<div class=\"grade\" style=\"grid-template-columns:1fr\">"
             f"<div class=\"card\">{blocos}</div></div>")
    return _com_notas(corpo, dados)


def _render_mockup(dados: dict) -> str:
    telas = dados.get("telas", [])
    nome_app = dados.get("app", "App")
    colunas = "".join(
        "<div class=\"celular\" style=\"margin-bottom:20px\">"
        f"<div class=\"tela-titulo\">{_esc(t.get('titulo',''))}</div>"
        + "".join(
            "<div class=\"tela-item\">" +
            (f"<b>{_esc(i.get('chave',''))} </b>" if isinstance(i, dict) else "")
            + _esc(i.get("texto", "") if isinstance(i, dict) else i)
            + "</div>"
            for i in t.get("itens", [])
        )
        for t in telas
    )
    return (f"<div class=\"cab\"><h1>{_esc(nome_app)}</h1>"
            f"<div class=\"sub\">Mockup estático</div></div>"
            f"<div class=\"grade\" style=\"grid-template-columns:"
            f"repeat(auto-fit,minmax(320px,1fr))\">{colunas}</div>")


def _render_texto(dados: dict) -> str:
    paragrafos = "".join(
        f"<p style=\"max-width:900px;margin:0 auto 14px;line-height:1.6;"
        f"color:#c6cbd9;font-size:15px\">{_esc(p)}</p>"
        for p in dados.get("paragrafos", [])
    )
    return _com_notas(paragrafos, dados)


def _com_notas(corpo: str, dados: dict) -> str:
    notas = dados.get("notas", [])
    if not notas:
        return corpo
    itens = "".join(f"<li>{_esc(n)}</li>" for n in notas)
    return corpo + f"<div class=\"notas\"><ul>{itens}</ul></div>"


RENDERIZADORES = {
    "kpi": _render_kpi,
    "tabela": _render_tabela,
    "barras": _render_barras,
    "mockup": _render_mockup,
    "texto": _render_texto,
}


def gerar(tipo: str, titulo: str, dados: dict, destino: Path) -> Path:
    render = RENDERIZADORES.get(tipo)
    if render is None:
        raise ValueError(f"tipo desconhecido: {tipo}. "
                         f"Use: {', '.join(RENDERIZADORES)}")
    html = _pagina(titulo, render(dados))
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    os.replace(tmp, destino)
    return destino


def main():
    parser = argparse.ArgumentParser(description="Gera visual HTML temporário")
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--tipo", required=True, choices=list(RENDERIZADORES))
    parser.add_argument("--json", help="dados JSON inline")
    parser.add_argument("--arquivo", help="arquivo JSON com os dados")
    parser.add_argument("--salvar", help="persistir em caminho específico")
    args = parser.parse_args()

    if args.json:
        dados = json.loads(args.json)
    elif args.arquivo:
        dados = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
    else:
        print("ERRO: informe --json ou --arquivo")
        sys.exit(1)

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.salvar:
        destino = Path(args.salvar)
    else:
        pasta = Path(tempfile.gettempdir()) / "opencode" / "visuals"
        destino = pasta / f"{args.tipo}_{carimbo}.html"

    caminho = gerar(args.tipo, args.titulo, dados, destino)
    tamanho = caminho.stat().st_size
    print(f"[OK] visual criado: {caminho} ({tamanho} bytes)")
    print("Abra o arquivo manualmente quando quiser ver.")


if __name__ == "__main__":
    main()
