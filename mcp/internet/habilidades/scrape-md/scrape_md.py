"""scrape_md.py — Scrape local de paginas web para Markdown (100% stdlib).

Assimilacao dos padroes centrais do Firecrawl, sem depender do servico:
1. Extracao de conteudo principal (heuristica tipo Readability):
   article > main > [role=main] / class~content > body limpo.
2. Conversao HTML -> Markdown limpo (titulos, listas, links absolutos, codigo).
3. Crawl BFS opcional no mesmo dominio com rate limit, robots.txt e cache TTL.

Uso:
  python scrape_md.py <url>                    # pagina unica -> markdown
  python scrape_md.py <url> --crawl 5          # BFS ate 5 paginas do dominio
  python scrape_md.py <url> --sem-cache        # ignora cache (TTL 24h)
  python scrape_md.py <url> --salvar saida.md

Saida (stdout): JSON {"url", "titulo", "markdown", "paginas": [...]} ou
em modo crawl {"origem", "paginas": [{"url","titulo","markdown"}], "erudos": [...]}
"""
import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CACHE_DIR = ROOT / "runtime" / "scrape_md_cache"
CACHE_TTL_S = 24 * 3600
MAX_BYTES = 800_000
TIMEOUT_S = 15
UA = "Mozilla/5.0 (compatible; EcoSystemUmGrau-scrape-md/1.0; +local)"
RATE_LIMIT_S = 0.4

IGNORAR = {
    "script", "style", "nav", "footer", "header", "aside", "form", "svg",
    "iframe", "noscript", "button", "select", "label", "template", "dialog",
}
BLOCO = {"p", "div", "section", "article", "main", "li", "tr", "table",
         "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr"}
TITULOS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}


def _limpar_texto(t):
    t = unicodedata.normalize("NFC", t or "")
    return re.sub(r"\s+", " ", t)


class Analisador(HTMLParser):
    """Passada unica: mede blocos candidatos e extrai titulo/links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titulo = ""
        self._dentro_title = False
        self.candidatos = {}          # (tag, indice_global) -> chars de texto
        self._pilha_cand = []
        self._n = 0                   # contador global de aberturas
        self.links = set()

    def handle_starttag(self, tag, attrs):
        self._n += 1
        a = dict(attrs)
        if tag == "title":
            self._dentro_title = True
        if tag in ("article", "main"):
            self._pilha_cand.append((tag, self._n))
            self.candidatos[(tag, self._n)] = 0
        if tag == "a":
            href = (a.get("href") or "").strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                self.links.add(href)

    def handle_endtag(self, tag):
        if tag == "title":
            self._dentro_title = False
        if tag in ("article", "main") and self._pilha_cand:
            self._pilha_cand.pop()

    def handle_data(self, data):
        if self._dentro_title and not self.titulo:
            self.titulo = _limpar_texto(data)[:200]
        peso = len(_limpar_texto(data))
        if not peso:
            return
        for chave in self._pilha_cand:
            self.candidatos[chave] += peso


class Conversor(HTMLParser):
    """HTML -> Markdown. Captura somente dentro do elemento-alvo (se definido).

    O alvo vem do Analisador como (tag, n_da_abertura). Para casar, este parser
    tambem conta TODA starttag (inclusive ignoradas) com o mesmo contador.
    """

    def __init__(self, alvo=None):
        super().__init__(convert_charrefs=True)
        self.alvo = tuple(alvo) if alvo else None   # ("article", n)
        self.saida = []
        self.lixo = 0                 # profundidade dentro de tag ignorada
        self._pilhas = []             # [(tag, n_abertura)]
        self._ativo = alvo is None
        self._fechando_alvo = False
        self._n = 0
        self.href = None              # link em curso
        self.buf_link = []

    def _empurra(self, txt):
        if txt:
            self.saida.append(txt)

    # --- handlers -------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        self._n += 1
        if tag in IGNORAR:
            if self._ativo or not self.alvo:
                self.lixo += 1
            return
        if (not self._ativo and self.alvo
                and (tag, self._n) == self.alvo):
            self._ativo = True
            self._fechando_alvo = True
        self._pilhas.append((tag, self._n))
        if not self._ativo:
            return
        a = dict(attrs)
        if tag in TITULOS:
            self._empurra("\n\n" + TITULOS[tag] + " ")
        elif tag == "p":
            self._empurra("\n\n")
        elif tag in ("ul", "ol", "table", "blockquote", "pre"):
            self._empurra("\n\n")
        elif tag == "li":
            self._empurra("\n- ")
        elif tag == "tr":
            self._empurra("\n| ")
        elif tag in ("td", "th"):
            self._empurra(" | ")
        elif tag == "br":
            self._empurra("\n")
        elif tag == "hr":
            self._empurra("\n\n---\n\n")
        elif tag == "blockquote":
            self._empurra("> ")
        elif tag == "a":
            href = (a.get("href") or "").strip()
            if href.startswith(("http", "/")) :
                href = urljoin(getattr(self, "base", ""), href)
            self.href = href
            self.buf_link = []
        elif tag in ("strong", "b"):
            self._empurra("**")
        elif tag in ("em", "i"):
            self._empurra("*")
        elif tag == "code":
            self._empurra("`")

    def handle_endtag(self, tag):
        if tag in IGNORAR:
            if self.lixo:
                self.lixo -= 1
            return
        if self._ativo:
            if tag == "a" and self.href is not None:
                txt = "".join(self.buf_link).strip() or self.href
                self.saida.append(f"[{txt}]({self.href})")
                self.href = None
            elif tag in ("strong", "b"):
                self._empurra("**")
            elif tag in ("em", "i"):
                self._empurra("*")
            elif tag == "code":
                self._empurra("`")
            elif tag == "pre":
                self._empurra("\n```\n\n")
        for i in range(len(self._pilhas) - 1, -1, -1):
            if self._pilhas[i][0] == tag:
                n_abertura = self._pilhas[i][1]
                del self._pilhas[i:]
                if (self._fechando_alvo and self.alvo
                        and tag == self.alvo[0] and n_abertura == self.alvo[1]):
                    self._ativo = False
                    self._fechando_alvo = False
                break

    def handle_data(self, data):
        if self.lixo or not self._ativo:
            return
        txt = _limpar_texto(data)
        if not txt:
            return
        if self.href is not None:
            self.buf_link.append(txt)
        else:
            self._empurra(txt)


def _baixar(url):
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            ctype = r.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype and ctype:
                raise ErroScrape(f"tipo_nao_suportado:{ctype}")
            bruto = r.read(MAX_BYTES + 1)
            truncado = len(bruto) > MAX_BYTES
            if truncado:
                bruto = bruto[:MAX_BYTES]
    except urllib.error.HTTPError as e:
        raise ErroScrape(f"http_{e.code}") from None
    except urllib.error.URLError as e:
        motivo = str(getattr(e, "reason", e))
        tipo = "timeout" if "timed out" in motivo.lower() else "rede"
        raise ErroScrape(f"{tipo}:{motivo[:80]}") from None
    charset = "utf-8"
    m = re.search(r"charset=([\w-]+)", ctype)
    if not m:
        # fallback: meta charset declarada no proprio HTML
        cabeca = bruto[:4096].decode("ascii", errors="ignore")
        m2 = re.search(r'charset=["\']?([\w-]+)', cabeca, re.IGNORECASE)
        if m2:
            charset = m2.group(1)
    else:
        charset = m.group(1)
    try:
        return bruto.decode(charset, errors="replace"), str(r.geturl()), truncado
    except LookupError:
        return bruto.decode("utf-8", errors="replace"), str(r.geturl()), truncado


def _cache_ok(url, usar_cache=True):
    if not usar_cache:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        if time.time() - d["ts"] < CACHE_TTL_S:
            return d
    except Exception:
        pass
    return None


def _cache_grava(url, dados):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": time.time(), **dados}, ensure_ascii=False),
                   encoding="utf-8")
    try:
        tmp.replace(f)
    except OSError:
        pass


def _robots_permite(url):
    """RFC 9309: retorna True (livre), False (regra explicita proibe) ou
    None (indeterminado: robots ausente-inacessivel por rede -> seguir e
    deixar _baixar reportar o erro real). Feito manualmente porque o
    robotparser desta maquina trata 404 como disallow_all."""
    import urllib.error
    q = urlparse(url)
    if not q.scheme.startswith("http"):
        return True               # file:// etc.: robots nao se aplica
    raiz = f"{q.scheme}://{q.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        req = urllib.request.Request(raiz, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            corpo = r.read(256_000).decode("utf-8", errors="replace")
        rp.parse(corpo.splitlines())
    except urllib.error.HTTPError as e:
        if e.code == 404 or 400 <= e.code < 500:
            return True           # sem regras -> livre
        return False              # 401/403/5xx -> negado
    except Exception:
        return None               # rede/DNS: indeterminado, erro real vem depois
    try:
        return rp.can_fetch("*", url)
    except Exception:
        return True


class ErroScrape(Exception):
    """Erro classificado: tipo legivel para o chamador decidir fallback."""


def _normalizar_url(url):
    """Garante esquema http(s) e barra final no path, p/ cache consistente."""
    url = url.strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    q = urlparse(url)
    path = q.path or "/"
    return f"{q.scheme}://{q.netloc}{path}" + (f"?{q.query}" if q.query else "")


def scrape(url, usar_cache=True):
    """Baixa e converte uma pagina -> dict {url, titulo, markdown, avisos}."""
    url = _normalizar_url(url)
    hit = _cache_ok(url, usar_cache)
    if hit is not None:
        return {"url": url, "titulo": "", "markdown": hit["md"],
                "avisos": ["cache"]}
    if _robots_permite(url) is False:
        raise ErroScrape(f"robots_proibe:{url}")
    html, final, truncado = _baixar(url)
    ana = Analisador()
    try:
        ana.feed(html)
    except Exception:
        pass
    alvo = None
    melhores = sorted(ana.candidatos.items(), key=lambda kv: -kv[1])
    if melhores and melhores[0][1] >= 200:
        alvo = melhores[0][0]
    conv = Conversor(alvo=alvo)
    conv.base = final
    try:
        conv.feed(html)
    except Exception:
        pass
    md = "".join(conv.saida)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]{2,}", " ", md).strip()
    avisos = []
    if truncado:
        avisos.append("html_truncado")
    # Deteccao SPA: pouco texto + sinais de app JS -> sugerir Playwright
    if len(md) < 120 and re.search(r"<script[\s>]", html, re.IGNORECASE):
        avisos.append("pagina_aparenta_js:use_playwright_ou_browser_mcp")
    if not md:
        md = "(pagina sem texto extraivel)"
        avisos.append("vazio")
    _cache_grava(final, {"md": md})
    return {"url": final, "titulo": ana.titulo, "markdown": md, "avisos": avisos}


def crawl(url, max_paginas=5, usar_cache=True):
    """BFS no mesmo dominio a partir de url. Retorna dict com paginas e erros."""
    origem = urlparse(url)
    fila, vistas = [url], {url}
    resultado = {"origem": url, "paginas": [], "erros": []}
    while fila and len(resultado["paginas"]) < max_paginas:
        atual = fila.pop(0)
        try:
            html, _f, _t = _baixar(atual)
            ana = Analisador()
            ana.feed(html)
            _LINKS_CACHE[atual] = sorted(ana.links)
            resultado["paginas"].append(scrape(atual, usar_cache))
            for href in _LINKS_CACHE.get(atual, []):
                absu = urljoin(atual, href.split("#")[0])
                q = urlparse(absu)
                if (q.netloc == origem.netloc and q.scheme.startswith("http")
                        and absu not in vistas):
                    vistas.add(absu)
                    fila.append(absu)
        except Exception as e:
            erros = {"url": atual, "erro": str(e)}
            resultado["erros"].append(erros)
        if fila:
            time.sleep(RATE_LIMIT_S)
    return resultado


_LINKS_CACHE = {}


def main():
    ap = argparse.ArgumentParser(description="Scrape de pagina(s) -> Markdown")
    ap.add_argument("url")
    ap.add_argument("--crawl", type=int, default=0,
                    help="seguir links internos ate N paginas (BFS)")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--salvar", help="gravar markdown em arquivo")
    args = ap.parse_args()
    if args.crawl:
        resultado = crawl(args.url, args.crawl, not args.sem_cache)
    else:
        r = scrape(args.url, not args.sem_cache)
        resultado = {"url": r["url"], "titulo": r["titulo"],
                     "markdown": r["markdown"], "avisos": r["avisos"]}

    if args.salvar:
        textos = "\n\n---\n\n".join(
            p["markdown"] for p in resultado.get("paginas", [])
        ) if "paginas" in resultado else resultado["markdown"]
        Path(args.salvar).write_text(textos, encoding="utf-8")
        print(json.dumps({"ok": True, "salvo_em": args.salvar}, ensure_ascii=False))
    else:
        print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
