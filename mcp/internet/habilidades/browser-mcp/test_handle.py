import asyncio
import json
import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\mcp\internet\habilidades\browser-mcp")
from server import handle

async def test():
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "navigate",
            "arguments": {"url": "https://example.com", "screenshot": False}
        }
    }
    resp = handle(req)
    if asyncio.iscoroutine(resp):
        resp = await resp
    print(json.dumps(resp, indent=2, ensure_ascii=False))

asyncio.run(test())