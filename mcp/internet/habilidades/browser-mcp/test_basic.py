import asyncio
import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\mcp\internet\habilidades\browser-mcp")

async def test():
    print("Starting...")
    from playwright.async_api import async_playwright
    print("Playwright imported")
    playwright = await async_playwright().start()
    print("Playwright started")
    browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
    print("Browser launched")
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    print("Context created")
    page = await context.new_page()
    print("Page created")
    await page.goto("https://example.com", wait_until="networkidle", timeout=30000)
    print("Navigated")
    title = await page.title()
    print(f"Title: {title}")
    await browser.close()
    await playwright.stop()
    print("Done")

asyncio.run(test())