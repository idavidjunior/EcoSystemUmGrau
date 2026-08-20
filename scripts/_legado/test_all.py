import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
from jarvis_bridge import Cliente
import asyncio

async def test_comandos_eco():
    c = Cliente()
    
    # Test @eco
    print('=== Testando @eco ===')
    r = await c.perguntar('@eco')
    print('Resposta @eco: "%s"' % r)
    
    # Test /eco
    print('=== Testando /eco ===')
    r = await c.perguntar('/eco')
    print('Resposta /eco: "%s"' % r)
    
    # Test Eco (palavra única)
    print('=== Testando Eco ===')
    r = await c.perguntar('Eco')
    print('Resposta Eco: "%s"' % r)
    
    # Test Desativar Eco
    print('=== Testando Desativar Eco ===')
    r = await c.perguntar('Desativar Eco')
    print('Resposta Desativar Eco: "%s"' % r)

asyncio.run(test_comandos_eco())