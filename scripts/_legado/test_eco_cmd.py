import sys
sys.path.insert(0, r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts")
from jarvis_bridge import Cliente
import asyncio

async def test():
    c = Cliente()
    print("Testando @eco...")
    result = await c._processar_comando_eco('@eco')
    print(f"Resultado @eco: {result}")
    print("Testando /eco...")
    result = await c._processar_comando_eco('/eco')
    print(f"Resultado /eco: {result}")
    print("Testando Eco...")
    result = await c._processar_comando_eco('Eco')
    print(f"Resultado Eco: {result}")
    print("Testando Desativar Eco...")
    result = await c._processar_comando_eco('Desativar Eco')
    print(f"Resultado Desativar Eco: {result}")

asyncio.run(test())