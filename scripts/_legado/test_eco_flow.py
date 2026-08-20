import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts")
from jarvis_bridge import Cliente
import asyncio

async def test():
    c = Cliente()
    print("Enviando @eco via perguntar...")
    result = await c.perguntar('@eco')
    print(f"Resposta: '{result}'")

asyncio.run(test())