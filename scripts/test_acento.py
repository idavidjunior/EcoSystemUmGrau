import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
from vox_audio import cmd_falar_async
import asyncio

async def main():
    await cmd_falar_async('Teste de pronunc: widget uáidiguét.')

asyncio.run(main())