"""MCP Server — Browser Automation (Playwright).

Automação web real via Playwright: navegação, busca, extração, formulários, screenshots.

Tools:
  - navigate          — acessa URL, retorna HTML + screenshot opcional
  - search            — busca via SearXNG + navega para resultados
  - extract           — extrai dados via seletores CSS/XPath
  - fill_form         — preenche e submete formulários
  - click             — clica em elementos
  - scroll            — rola página
  - screenshot        — captura tela
  - get_text          — retorna texto visível da página
  - wait_for          — aguarda elemento/condição
"""
import json
import sys
import os
import asyncio
import base64
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

# Adiciona paths
BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"))

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

TOOLS = [
    {
        "name": "navigate",
        "description": "Navega para uma URL e retorna HTML da página. Opcionalmente captura screenshot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL para navegar", "minLength": 1},
                "wait_until": {"type": "string", "description": "Quando considerar navegação completa", "enum": ["load", "domcontentloaded", "networkidle"], "default": "networkidle"},
                "screenshot": {"type": "boolean", "description": "Capturar screenshot após carregar", "default": False},
                "timeout_ms": {"type": "integer", "description": "Timeout em ms", "default": 30000},
            },
            "required": ["url"]
        },
    },
    {
        "name": "search",
        "description": "Busca via SearXNG e navega para o primeiro resultado (ou índice especificado).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termo de busca", "minLength": 1},
                "index": {"type": "integer", "description": "Índice do resultado para clicar (0 = primeiro)", "default": 0},
                "searxng_url": {"type": "string", "description": "URL do SearXNG (opcional, usa env SEARXNG_BASE_URL)"},
            },
            "required": ["query"]
        },
    },
    {
        "name": "extract",
        "description": "Extrai dados da página atual usando seletores CSS ou XPath.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selectors": {"type": "object", "description": "Dict {nome_campo: seletor_css}", "additionalProperties": {"type": "string"}},
                "xpath": {"type": "object", "description": "Dict {nome_campo: xpath}", "additionalProperties": {"type": "string"}},
                "attribute": {"type": "string", "description": "Atributo a extrair (default: textContent)", "default": "textContent"},
                "multiple": {"type": "boolean", "description": "Se true, retorna lista de elementos", "default": False},
            },
            "required": []
        },
    },
    {
        "name": "fill_form",
        "description": "Preenche formulário com dados e opcionalmente submete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fields": {"type": "object", "description": "Dict {seletor: valor}", "additionalProperties": {"type": "string"}},
                "submit": {"type": "boolean", "description": "Submeter formulário após preencher", "default": False},
                "submit_selector": {"type": "string", "description": "Seletor do botão submit (se submit=true)"},
            },
            "required": ["fields"]
        },
    },
    {
        "name": "click",
        "description": "Clica em elemento via seletor CSS/XPath.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "Seletor CSS do elemento"},
                "xpath": {"type": "string", "description": "XPath alternativo"},
                "wait_for_navigation": {"type": "boolean", "description": "Aguardar navegação após clique", "default": False},
            },
            "required": []
        },
    },
    {
        "name": "scroll",
        "description": "Rola a página.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "description": "Direção", "enum": ["down", "up", "top", "bottom"], "default": "down"},
                "pixels": {"type": "integer", "description": "Pixels para rolar (se direction=down/up)", "default": 500},
            },
            "required": []
        },
    },
    {
        "name": "screenshot",
        "description": "Captura screenshot da página atual.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "full_page": {"type": "boolean", "description": "Capturar página inteira", "default": True},
                "format": {"type": "string", "description": "Formato", "enum": ["png", "jpeg"], "default": "png"},
            },
            "required": []
        },
    },
    {
        "name": "get_text",
        "description": "Retorna texto visível da página.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "Seletor opcional para limitar escopo"},
            },
            "required": []
        },
    },
    {
        "name": "wait_for",
        "description": "Aguarda elemento aparecer ou condição.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "Seletor CSS para aguardar"},
                "state": {"type": "string", "description": "Estado esperado", "enum": ["attached", "detached", "visible", "hidden"], "default": "visible"},
                "timeout_ms": {"type": "integer", "description": "Timeout em ms", "default": 10000},
            },
            "required": ["selector"]
        },
    },
    {
        "name": "close",
        "description": "Fecha browser/context atual.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
]


# Estado global do browser
_browser: Optional["Browser"] = None
_context: Optional["BrowserContext"] = None
_page: Optional["Page"] = None
_playwright = None


async def get_page() -> "Page":
    """Obtém ou cria página do browser."""
    global _browser, _context, _page, _playwright

    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright não instalado. pip install playwright && playwright install chromium")

    if _page is None or _page.is_closed():
        if _playwright is None:
            _playwright = await async_playwright().start()
        if _browser is None or not _browser.is_connected():
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
        if _context is None:
            _context = await _browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        _page = await _context.new_page()

    return _page


async def cleanup():
    """Limpa recursos."""
    global _browser, _context, _page, _playwright
    if _page and not _page.is_closed():
        await _page.close()
    if _context:
        await _context.close()
    if _browser and _browser.is_connected():
        await _browser.close()
    if _playwright:
        await _playwright.stop()
    _browser = _context = _page = _playwright = None


async def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-browser", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return await handle_tool_async(tool, args, rid)

    return None


async def handle_tool_async(tool, args, rid):
    try:
        if tool == "navigate":
            result = await navigate(args)
        elif tool == "search":
            result = await search(args)
        elif tool == "extract":
            result = await extract(args)
        elif tool == "fill_form":
            result = await fill_form(args)
        elif tool == "click":
            result = await click(args)
        elif tool == "scroll":
            result = await scroll(args)
        elif tool == "screenshot":
            result = await screenshot(args)
        elif tool == "get_text":
            result = await get_text(args)
        elif tool == "wait_for":
            result = await wait_for(args)
        elif tool == "close":
            result = await close_browser(args)
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)}]}}

    return {"jsonrpc": "2.0", "id": rid, "result": {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


async def navigate(args) -> dict:
    page = await get_page()
    url = args.get("url")
    wait_until = args.get("wait_until", "networkidle")
    screenshot_flag = args.get("screenshot", False)
    timeout_ms = args.get("timeout_ms", 30000)

    await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
    html = await page.content()

    result = {"url": page.url, "title": await page.title(), "html_length": len(html)}

    if screenshot_flag:
        img = await page.screenshot(full_page=True)
        result["screenshot_base64"] = base64.b64encode(img).decode()

    return {"navigate": result}


async def search(args) -> dict:
    page = await get_page()
    query = args.get("query")
    index = args.get("index", 0)
    searxng_url = args.get("searxng_url") or os.getenv("SEARXNG_BASE_URL", "http://localhost:8080")

    # Navega para SearXNG
    search_url = f"{searxng_url}/search?q={query.replace(' ', '+')}&format=json"
    await page.goto(search_url, wait_until="networkidle")

    # Tenta extrair links dos resultados
    try:
        results = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('article.result h3 a, .result a.url_header'));
                return links.slice(0, 10).map((a, i) => ({index: i, title: a.textContent.trim(), url: a.href}));
            }
        """)
        if results and len(results) > index:
            target = results[index]
            await page.goto(target["url"], wait_until="networkidle")
            return {"search": {"query": query, "clicked": target, "current_url": page.url}}
    except Exception:
        pass

    return {"search": {"query": query, "error": "Não foi possível extrair/clicar resultado", "current_url": page.url}}


async def extract(args) -> dict:
    page = await get_page()
    selectors = args.get("selectors", {})
    xpaths = args.get("xpath", {})
    attribute = args.get("attribute", "textContent")
    multiple = args.get("multiple", False)

    result = {}

    # CSS selectors
    for name, selector in selectors.items():
        try:
            if multiple:
                elements = await page.query_selector_all(selector)
                values = []
                for el in elements:
                    val = await el.get_attribute(attribute) if attribute != "textContent" else await el.text_content()
                    values.append(val)
                result[name] = values
            else:
                el = await page.query_selector(selector)
                if el:
                    val = await el.get_attribute(attribute) if attribute != "textContent" else await el.text_content()
                    result[name] = val
                else:
                    result[name] = None
        except Exception as e:
            result[name] = {"error": str(e)}

    # XPath
    for name, xpath in xpaths.items():
        try:
            if multiple:
                elements = await page.query_selector_all(f"xpath={xpath}")
                values = []
                for el in elements:
                    val = await el.get_attribute(attribute) if attribute != "textContent" else await el.text_content()
                    values.append(val)
                result[name] = values
            else:
                el = await page.query_selector(f"xpath={xpath}")
                if el:
                    val = await el.get_attribute(attribute) if attribute != "textContent" else await el.text_content()
                    result[name] = val
                else:
                    result[name] = None
        except Exception as e:
            result[name] = {"error": str(e)}

    return {"extract": result}


async def fill_form(args) -> dict:
    page = await get_page()
    fields = args.get("fields", {})
    submit = args.get("submit", False)
    submit_selector = args.get("submit_selector")

    filled = []
    for selector, value in fields.items():
        try:
            await page.fill(selector, value)
            filled.append(selector)
        except Exception as e:
            return {"fill_form": {"error": f"Falha ao preencher {selector}: {e}", "filled": filled}}

    if submit:
        try:
            if submit_selector:
                await page.click(submit_selector)
            else:
                await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle", timeout=10000)
            return {"fill_form": {"filled": filled, "submitted": True, "current_url": page.url}}
        except Exception as e:
            return {"fill_form": {"filled": filled, "submitted": False, "error": str(e)}}

    return {"fill_form": {"filled": filled, "submitted": False}}


async def click(args) -> dict:
    page = await get_page()
    selector = args.get("selector")
    xpath = args.get("xpath")
    wait_for_navigation = args.get("wait_for_navigation", False)

    target = f"xpath={xpath}" if xpath else selector

    try:
        if wait_for_navigation:
            async with page.expect_navigation(wait_until="networkidle"):
                await page.click(target)
        else:
            await page.click(target)
        return {"click": {"success": True, "current_url": page.url}}
    except Exception as e:
        return {"click": {"success": False, "error": str(e)}}


async def scroll(args) -> dict:
    page = await get_page()
    direction = args.get("direction", "down")
    pixels = args.get("pixels", 500)

    try:
        if direction == "down":
            await page.mouse.wheel(0, pixels)
        elif direction == "up":
            await page.mouse.wheel(0, -pixels)
        elif direction == "top":
            await page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        return {"scroll": {"success": True, "direction": direction}}
    except Exception as e:
        return {"scroll": {"success": False, "error": str(e)}}


async def screenshot(args) -> dict:
    page = await get_page()
    full_page = args.get("full_page", True)
    format = args.get("format", "png")

    img = await page.screenshot(full_page=full_page, type=format)
    return {"screenshot": {"base64": base64.b64encode(img).decode(), "format": format}}


async def get_text(args) -> dict:
    page = await get_page()
    selector = args.get("selector")

    try:
        if selector:
            el = await page.query_selector(selector)
            text = await el.text_content() if el else ""
        else:
            text = await page.text_content("body")
        return {"get_text": {"text": text[:50000]}}  # Limita tamanho
    except Exception as e:
        return {"get_text": {"error": str(e)}}


async def wait_for(args) -> dict:
    page = await get_page()
    selector = args.get("selector")
    state = args.get("state", "visible")
    timeout_ms = args.get("timeout_ms", 10000)

    try:
        await page.wait_for_selector(selector, state=state, timeout=timeout_ms)
        return {"wait_for": {"success": True, "selector": selector, "state": state}}
    except Exception as e:
        return {"wait_for": {"success": False, "error": str(e)}}


async def close_browser(args) -> dict:
    global _browser, _context, _page, _playwright
    try:
        await cleanup()
        return {"close": {"success": True}}
    except Exception as e:
        return {"close": {"success": False, "error": str(e)}}


if __name__ == "__main__":
    import os
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
async def _read_frame(stream):
    peek = stream.peek(1)
    if not peek:
        return None
    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        return None

    headers = {}
    if b":" in first:
        key, value = first.split(b":", 1)
        headers[key.strip().lower()] = value.strip()
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length <= 0:
        return None
    body = stream.read(length)
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


async def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


async def main_loop():
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = await _read_frame(stdin)
        if req is None:
            break
        resp = await handle(req)
        if resp is not None:
            await _write_frame(stdout, resp)


if __name__ == "__main__":
    import os
    asyncio.run(main_loop())