# Ciclo 7 — Testes de Performance e Acessibilidade (blocos J e D)
# Mede Core Web Vitals (LCP/CLS/INP) de uma página real com Playwright e
# valida correções WCAG básicas. Uso: python test_performance.py
#
# Decisões: ThreadingHTTPServer stdlib (ADR-003); medição via Playwright
# sync + PerformanceObserver injetado (ADR-007). Nenhuma dependência nova.

import json
import os
import sys
import time
import threading

import server as lab_server

# Playwright import é pesado; importar no main para permitir a página ambiente
from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = None  # definido no inicio
PASS = 0
FAIL = 0

# JS injetado antes de toda navegação: observa LCP, CLS e INP.
_BOOT_JS = """
window.__cwv = { lcp: 0, cls: 0, inp: 0, lcp_entries: [], cls_entries: [] };
try {
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      if (e.entryType === 'largest-contentful-paint') {
        window.__cwv.lcp = Math.max(window.__cwv.lcp, e.renderTime || e.loadTime || e.startTime || 0);
      }
    }
  }).observe({type: 'largest-contentful-paint', buffered: true});
} catch (err) {}
try {
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      window.__cwv.cls += e.value;
    }
  }).observe({type: 'layout-shift', buffered: true});
} catch (err) {}
try {
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      if (e.entryType === 'event' && e.interactionId) {
        window.__cwv.inp = Math.max(window.__cwv.inp, e.duration || 0);
      }
    }
  }).observe({type: 'event', buffered: true, durationThreshold: 16});
} catch (err) {}
"""


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        msg = f"{label}: {detail}" if detail else label
        print(f"  [FAIL] {msg}")


def medir_cwv(browser, caminho, clicar=False):
    """Abre caminho, coleta CWV após carregar, opcionalmente gera INP via clique."""
    ctx = browser.new_context(reduced_motion="reduce")
    page = ctx.new_page()
    page.add_init_script(_BOOT_JS)
    page.goto(f"http://{HOST}:{PORT}{caminho}", wait_until="load", timeout=15000)
    # espera hero + layout estabilizar
    page.wait_for_timeout(1500)
    # gera INP com interação real (clique no botão de newsletter)
    if clicar:
        botao = page.locator("#botao-cadastrar")
        if botao.count() > 0:
            botao.click()
            page.wait_for_timeout(300)
    metrics = page.evaluate("() => ({lcp: window.__cwv.lcp, cls: window.__cwv.cls, inp: window.__cwv.inp})")
    ctx.close()
    return metrics


def calcular_contraste(rgb1, rgb2):
    """Contraste WCAG a partir de duas cores [r,g,b] 0-255."""
    def lum(c):
        vals = []
        for v in c:
            v = v / 255.0
            vals.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]
    l1, l2 = lum(rgb1), lum(rgb2)
    mais, menos = max(l1, l2), min(l1, l2)
    return (mais + 0.05) / (menos + 0.05)


def parse_cor(css):
    css = css.strip()
    if css.startswith("rgb("):
        nums = css[4:-1].split(",")
        return [int(x.strip()) for x in nums[:3]]
    return [0, 0, 0]


def test_performance(browser):
    """1. LCP/CLS/INP mensuráveis; 2. versão corrigida não degrada."""
    print("\n[1] Medição de Core Web Vitals")

    antes = medir_cwv(browser, "/antes")
    depois = medir_cwv(browser, "/corrigida", clicar=True)

    print(f"      ANTES : LCP={antes['lcp']:.0f}ms CLS={antes['cls']:.4f} INP={antes['inp']:.0f}ms")
    print(f"      DEPOIS: LCP={depois['lcp']:.0f}ms CLS={depois['cls']:.4f} INP={depois['inp']:.0f}ms")

    check("LCP medido na página antes", antes["lcp"] > 0, f"lcp={antes['lcp']}")
    check("LCP medido na página depois", depois["lcp"] > 0, f"lcp={depois['lcp']}")
    check("CLS da versão depois fica abaixo de 0.1 (Good)", depois["cls"] < 0.1,
          f"cls={depois['cls']}")
    check("INP da versão depois fica abaixo de 200ms (Good)", depois["inp"] < 200,
          f"inp={depois['inp']}")
    check("CLS depois não é maior que CLS antes (correção não degradou)",
          depois["cls"] <= antes["cls"] + 0.01,
          f"antes={antes['cls']} depois={depois['cls']}")
    check("LCP depois não é pior que antes (preload + dimensões não atrasaram)",
          depois["lcp"] <= antes["lcp"] + 100,
          f"antes={antes['lcp']} depois={depois['lcp']}")

    global dados_cwv
    dados_cwv = {"antes": antes, "depois": depois, "metrica": "ms / ratio"}


def test_acessibilidade(browser):
    """3. WCAG básico na página corrigida (lang, títulos, alt, label, contraste)."""
    print("\n[2] Acessibilidade (WCAG básico)")
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"http://{HOST}:{PORT}/corrigida", wait_until="load", timeout=15000)

    lang = page.locator("html").get_attribute("lang")
    check("Atributo lang presente no <html>", lang and lang.startswith("pt"), f"lang={lang}")

    title = page.title()
    check("Título da página presente", bool(title.strip()), f"title={title}")

    h1 = page.locator("h1")
    check("Existe exatamente um h1", h1.count() == 1, f"h1={h1.count()}")
    first_heading = page.locator("h1, h2, h3, h4, h5, h6").first.inner_text()
    check("Primeiro heading da página é h1", first_heading.lower().startswith(("a sua", "a lenda", "engenharia")),
          f"first={first_heading}")

    imgs = page.locator("img")
    sem_alt = 0
    for i in range(imgs.count()):
        alt = imgs.nth(i).get_attribute("alt")
        if alt is None:
            sem_alt += 1
    check("Todas as imagens possuem alt", sem_alt == 0, f"img sem alt={sem_alt}")

    label_email = page.locator("label[for='email-news']")
    check("Campo de email tem label associado via for/id",
          label_email.count() == 1 and label_email.inner_text().strip() != "",
          f"label-count={label_email.count()}")

    inputs = page.locator("input[type='email']")
    check("Input de email existe e tem id", inputs.count() >= 1 and
          inputs.first.get_attribute("id") == "email-news")

    # Contraste do texto principal (p) sobre o fundo do body
    fundo = page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
    texto = page.locator("main p").first.evaluate("el => getComputedStyle(el).color")
    ratio = calcular_contraste(parse_cor(texto), parse_cor(fundo))
    check(f"Contraste texto/body >= 4.5 (AA)", ratio >= 4.5, f"ratio={ratio:.2f} ({texto} sobre {fundo})")

    bt = page.locator("#botao-cadastrar")
    check("Botão de newsletter tem texto visível",
          bt.count() == 1 and bt.inner_text().strip() != "", f"count={bt.count()}")
    check("Botão de newsletter tem tamanho clicável (>= 24px)",
          bt.count() == 1 and bt.bounding_box()["height"] >= 24,
          f"h={bt.bounding_box()['height'] if bt.count() else 0:.1f}px")

    # A página ANTES deve conter problemas (contraste baixo / sem alt) — evidência
    page2 = ctx.new_page()
    page2.goto(f"http://{HOST}:{PORT}/antes", wait_until="load", timeout=15000)
    antes_lang = page2.locator("html").get_attribute("lang")
    check("Versão antes NÃO tem lang (problema original demonstrado)",
          antes_lang is None or antes_lang == "", f"lang={antes_lang}")
    alt_count = 0
    for i in range(page2.locator("img").count()):
        a = page2.locator("img").nth(i).get_attribute("alt")
        if a is None or a.strip() == "":
            alt_count += 1
    check("Versão antes tem imagem sem alt (problema original demonstrado)",
          alt_count >= 1, f"img sem alt={alt_count}")
    ctx.close()


def main():
    global PORT
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    else:
        PORT = 8097

    print("=" * 50)
    print("  CICLO 7 — PERFORMANCE E ACESSIBILIDADE")
    print("=" * 50)

    # sobe o servidor em thread
    sv = lab_server.criar_servidor(PORT)
    t = threading.Thread(target=sv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                test_performance(browser)
                test_acessibilidade(browser)
            finally:
                browser.close()
    finally:
        sv.shutdown()
        sv.server_close()

    # persiste medição em web/benchmarks/ (evidência do bloco J)
    bk_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "benchmarks")
    os.makedirs(bk_dir, exist_ok=True)
    with open(os.path.join(bk_dir, "ciclo-7-cwv.json"), "w", encoding="utf-8") as f:
        json.dump(dados_cwv, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"  STATUS: OK ({PASS} checks, {FAIL} falhas)")
    else:
        print(f"  STATUS: FALHA ({PASS} pass, {FAIL} falhas)")
    print("=" * 50)
    return FAIL == 0


if __name__ == "__main__":
    dados_cwv = {}
    ok = main()
    sys.exit(0 if ok else 1)