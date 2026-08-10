#!/usr/bin/env python3
"""os-automation — MCP server para automação Windows + Web (Playwright + pywinauto).

MCP 2.0+ usa API diferente. Exportamos a classe OSAutomation para uso direto.
Para servidor MCP completo, usar mcp-server-http ou adaptar para a nova API.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Importações lazy para não quebrar se dependências faltarem
PLAYWRIGHT_AVAILABLE = False
PYWINAUTO_AVAILABLE = False

try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

try:
    import pywinauto
    from pywinauto import Desktop, Application
    PYWINAUTO_AVAILABLE = True
except ImportError:
    pass


class OSAutomation:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._desktop = None

    async def _ensure_browser(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("playwright não instalado: pip install playwright && playwright install chromium")
        if self.browser is None or not self.browser.is_connected():
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()

    async def _close_browser(self):
        if self.page:
            await self.page.close()
            self.page = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    # ===== WEB =====
    async def web_navigate(self, url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 30000) -> Dict:
        await self._ensure_browser()
        resp = await self.page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        return {"status": resp.status if resp else "ok", "url": self.page.url}

    async def web_click(self, selector: str, button: str = "left", count: int = 1, timeout_ms: int = 10000) -> Dict:
        await self._ensure_browser()
        await self.page.click(selector, button=button, click_count=count, timeout=timeout_ms)
        return {"ok": True}

    async def web_type(self, selector: str, text: str, delay_ms: int = 0, clear_first: bool = True) -> Dict:
        await self._ensure_browser()
        if clear_first:
            await self.page.fill(selector, "")
        await self.page.type(selector, text, delay=delay_ms)
        return {"ok": True}

    async def web_extract(self, selector: str, attribute: str = "text", multiple: bool = False, timeout_ms: int = 10000) -> Dict:
        await self._ensure_browser()
        # Caso especial: page.title() para <title> que está hidden
        if selector == "title" and attribute == "text":
            t = await self.page.title()
            return {"data": t}
        try:
            await self.page.wait_for_selector(selector, timeout=timeout_ms)
        except Exception:
            # Tenta mesmo assim (elemento pode estar hidden)
            pass
        if multiple:
            elements = await self.page.query_selector_all(selector)
            results = []
            for el in elements:
                if attribute == "text":
                    val = await el.inner_text()
                elif attribute == "html":
                    val = await el.inner_html()
                else:
                    val = await el.get_attribute(attribute)
                results.append(val)
            return {"data": results}
        else:
            el = await self.page.query_selector(selector)
            if not el:
                return {"data": "", "error": f"Elemento não encontrado: {selector}"}
            if attribute == "text":
                val = await el.inner_text()
            elif attribute == "html":
                val = await el.inner_html()
            else:
                val = await el.get_attribute(attribute)
            return {"data": val}

    async def web_screenshot(self, path: Optional[str] = None, selector: Optional[str] = None, full_page: bool = True) -> Dict:
        await self._ensure_browser()
        if path is None:
            path = os.path.join(tempfile.gettempdir(), f"jarvis_screenshot_{int(time.time()*1000)}.png")
        if selector:
            el = await self.page.query_selector(selector)
            if el:
                await el.screenshot(path=path)
            else:
                raise ValueError(f"Seletor não encontrado: {selector}")
        else:
            await self.page.screenshot(path=path, full_page=full_page)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return {"path": path, "base64": b64}

    async def web_wait(self, selector: Optional[str] = None, state: str = "visible", timeout_ms: int = 10000, url_contains: Optional[str] = None) -> Dict:
        await self._ensure_browser()
        if selector:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout_ms)
        if url_contains:
            await self.page.wait_for_url(f"**{url_contains}**", timeout=timeout_ms)
        return {"ok": True}

    # ===== DESKTOP =====
    def _ensure_desktop(self):
        if not PYWINAUTO_AVAILABLE:
            raise RuntimeError("pywinauto não instalado: pip install pywinauto")
        if self._desktop is None:
            self._desktop = Desktop(backend="uia")
        return self._desktop

    def desktop_find_window(self, title_regex: Optional[str] = None, class_name: Optional[str] = None, process_name: Optional[str] = None) -> Dict:
        desktop = self._ensure_desktop()
        windows = desktop.windows()
        for w in windows:
            try:
                if title_regex and not __import__("re").search(title_regex, w.window_text(), __import__("re").IGNORECASE):
                    continue
                if class_name and w.class_name() != class_name:
                    continue
                if process_name:
                    import psutil
                    pid = w.process_id()
                    if psutil.Process(pid).name().lower() != process_name.lower():
                        continue
                return {"handle": w.handle, "title": w.window_text(), "class": w.class_name(), "process_id": w.process_id()}
            except Exception:
                continue
        raise ValueError("Janela não encontrada")

    def desktop_click(self, window_handle: int, x: Optional[int] = None, y: Optional[int] = None, control_path: Optional[str] = None) -> Dict:
        desktop = self._ensure_desktop()
        win = desktop.window(handle=window_handle)
        win.set_focus()
        if control_path:
            ctrl = win
            for part in control_path.split("->"):
                ctrl = getattr(ctrl, part)
            ctrl.click_input()
        elif x is not None and y is not None:
            win.click_input(coords=(x, y))
        else:
            win.click_input()
        return {"ok": True}

    def desktop_type(self, window_handle: int, text: str, control_path: Optional[str] = None, send_keys: bool = False) -> Dict:
        desktop = self._ensure_desktop()
        win = desktop.window(handle=window_handle)
        win.set_focus()
        if control_path:
            ctrl = win
            for part in control_path.split("->"):
                ctrl = getattr(ctrl, part)
            if send_keys:
                ctrl.type_keys(text)
            else:
                ctrl.set_text(text)
        else:
            if send_keys:
                win.type_keys(text)
            else:
                import pywinauto.keyboard as keyboard
                keyboard.send_keys(text)
        return {"ok": True}

    def desktop_screenshot(self, window_handle: int, path: Optional[str] = None) -> Dict:
        desktop = self._ensure_desktop()
        win = desktop.window(handle=window_handle)
        if path is None:
            path = os.path.join(tempfile.gettempdir(), f"jarvis_desktop_{int(time.time()*1000)}.png")
        win.capture_as_image().save(path)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return {"path": path, "base64": b64}

    def sleep(self, seconds: float) -> Dict:
        time.sleep(seconds)
        return {"ok": True}


# Instância global para uso direto
automation = OSAutomation()

# Exportação compatível com MCP 1.x (não funcional em 2.x, mas não quebra)
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent
    
    server = Server("os-automation")
    
    # Em MCP 2.x, a API mudou. Mantemos a classe automation para uso direto.
    # Quem quiser servidor MCP real, usa mcp-server-http ou adapta para nova API.
    
except ImportError:
    pass


if __name__ == "__main__":
    # Teste rápido direto
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        async def teste():
            r = await automation.web_navigate("https://www.google.com")
            print("nav:", r)
            r = await automation.web_extract("title", attribute="text")
            print("title:", r)
            await automation._close_browser()
        asyncio.run(teste())
    else:
        print("os-automation: use 'python -m mcp.os.habilidades.os-automation server.py test' para teste rápido")
        print("ou importe: from server import automation")