import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
from jarvis_bridge import Cliente
from eco_widget import status
import asyncio

async def test_flow():
    c = Cliente()
    
    print('=== Testando @eco ===')
    r = await c.perguntar('@eco')
    print('Resposta @eco:', repr(r))
    await asyncio.sleep(2)
    
    print('=== Testando status ===')
    s = status()
    print('Status:', s)
    
    print('=== Testando Desativar Eco ===')
    r = await c.perguntar('Desativar Eco')
    print('Resposta Desativar Eco:', repr(r))
    await asyncio.sleep(2)
    
    print('=== Status depois desativar ===')
    s = status()
    print('Status:', s)
    
    print('=== Testando @eco novamente ===')
    r = await c.perguntar('@eco')
    print('Resposta @eco:', repr(r))
    await asyncio.sleep(2)
    
    print('=== Status final ===')
    s = status()
    print('Status:', s)

asyncio.run(test_flow())