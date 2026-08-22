"""Leitor de logs resiliente a encoding errado e gravacao interrompida.

Uso:
    python scripts/ver_log.py guardian_log.txt
    python scripts/ver_log.py guardian_log.txt -n 20 --grep Narrador

Por que existe: PowerShell 5.1 (Get-Content) assume ANSI quando o log nao tem
BOM e exibe acentos UTF-8 como lixo ("ap??s"). Este helper detecta o encoding
real do arquivo antes de decodificar:

    1. BOM UTF-8 / UTF-16 -> usa o encoding indicado pelo BOM
    2. UTF-8 estrito      -> caso normal de todo log deste ecossistema
    3. fallback cp1252 com errors=replace -> byte ruim vira marcador, sem crash

Ultima linha sem newline = processo morreu no meio da escrita -> marcada como
incompleta em vez de passar despercebida.
"""
import argparse
import sys
from pathlib import Path


def _decodificar(b: bytes) -> str:
    if b.startswith(b"\xef\xbb\xbf"):
        return b.decode("utf-8-sig", errors="replace")
    for bom in (b"\xff\xfe", b"\xfe\xff"):
        if b.startswith(bom):
            return b.decode("utf-16", errors="replace")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


def processar(caminho: str, tail: int, grep: str) -> bool:
    p = Path(caminho)
    if not p.is_file():
        print(f"[ERRO] arquivo nao existe: {p}")
        return False
    texto = _decodificar(p.read_bytes())
    linhas = texto.splitlines()
    incompleta = bool(texto) and not texto.endswith(("\n", "\r"))
    if grep:
        termo = grep.lower()
        linhas = [l for l in linhas if termo in l.lower()]
    if tail and len(linhas) > tail:
        linhas = linhas[-tail:]
    print(f"=== {p.name}: {len(linhas)} linha(s) ===")
    ultimo_indice = len(linhas) - 1
    for i, l in enumerate(linhas):
        if incompleta and not grep and i == ultimo_indice:
            print(f"{l}   <<[linha incompleta: gravacao interrompida]")
        else:
            print(l)
    return True


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("-n", type=int, default=0, help="mostrar apenas as ultimas N linhas")
    ap.add_argument("--grep", default="", help="filtrar linhas contendo o termo (case-insensitive)")
    a = ap.parse_args()
    ok = all(processar(f, a.n, a.grep) for f in a.arquivos)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
