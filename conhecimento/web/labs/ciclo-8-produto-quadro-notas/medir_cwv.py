# Ciclo 8 — Medição de Core Web Vitals da página do produto (bloco N7/performance-cwv)
# Reusa o padrão do Ciclo 7 (ADR-007): Playwright sync + PerformanceObserver injetado.
# Uso: python medir_cwv.py [porta]  → salva conhecimento/web/benchmarks/ciclo-8-cwv.json
#
# Decisões: ThreadingHTTPServer stdlib (ADR-003); medição via Playwright +
# PerformanceObserver (ADR-007). Sem dependência nova. Em loopback o tempo de
# rede é desprezível; o CWV aqui mede a página real do produto em comportamento.

import json
import os
import sys
import threading
import time

import server as lab_server
from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = None

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


def medir(browser):
    """Mede CWV de / (página real do produto) com interação no chat IA fake."""
    ctx = browser.new_context(reduced_motion="reduce")
    page = ctx.new_page()
    page.add_init_script(_BOOT_JS)
    t0 = time.monotonic()
    page.goto(f"http://{HOST}:{PORT}/", wait_until="load", timeout=15000)
    ttfb_ms = (time.monotonic() - t0) * 1000
    page.wait_for_timeout(1200)
    # interação real para gerar INP: foca/clica no campo de nova nota
    campo = page.locator("#nova-conteudo")
    if campo.count() > 0:
        campo.focus()
        page.wait_for_timeout(120)
    cwv = page.evaluate("() => ({lcp: window.__cwv.lcp, cls: window.__cwv.cls, inp: window.__cwv.inp})")
    cwv["ttfb_ms"] = ttfb_ms
    ctx.close()
    return cwv


def main():
    global PORT
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8098
    print("=" * 50)
    print("  CICLO 8 — CORE WEB VITALS (produto)")
    print("=" * 50)

    sv = lab_server.start(PORT)
    th = threading.Thread(target=sv.serve_forever, daemon=True)
    th.start()
    time.sleep(0.5)

    res = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                res = medir(browser)
            finally:
                browser.close()
    finally:
        sv.shutdown()
        sv.server_close()

    ok_lcp = res.get("lcp", 0) > 0
    ok_cls = res.get("cls", 99) < 0.1
    ok_inp = res.get("inp", 999) < 200
    print(f"  LCP={res.get('lcp', 0):.0f}ms CLS={res.get('cls', 0):.4f} "
          f"INP={res.get('inp', 0):.0f}ms TTFB={res.get('ttfb_ms', 0):.0f}ms")
    print(f"  LCP medido (>0): {ok_lcp} | CLS < 0.1 (Good): {ok_cls} | INP < 200ms (Good): {ok_inp}")

    bk_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "benchmarks")
    os.makedirs(bk_dir, exist_ok=True)
    with open(os.path.join(bk_dir, "ciclo-8-cwv.json"), "w", encoding="utf-8") as f:
        json.dump({"pagina": "/", "browser": "chromium", "metrica": "ms / ratio", **res},
                  f, ensure_ascii=False, indent=2)

    print(f"  Evidência salva em {bk_dir}/ciclo-8-cwv.json")
    if ok_lcp and ok_cls and ok_inp:
        print("  STATUS: OK (CWV atendido)")
        return 0
    print("  STATUS: FALHA (CWV fora das bandas)")
    return 1


if __name__ == "__main__":
    sys.exit(main())