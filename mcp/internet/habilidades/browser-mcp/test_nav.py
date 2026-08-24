import asyncio
import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\mcp\internet\habilidades\browser-mcp")
from server import navigate

async def test():
    result = await navigate({"url": "https://example.com", "screenshot": False})
    print(result)

asyncio.run(test())