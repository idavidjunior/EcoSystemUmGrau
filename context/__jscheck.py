import re
import esprima

src = open('docs/grafo.html', encoding='utf-8').read()
blocks = re.findall(r'<script>(.*?)</script>', src, re.S)
print('blocos script (sem vendor):', len(blocks))
for i, b in enumerate(blocks):
    try:
        esprima.parseScript(b)
        print(f'bloco {i}: OK ({len(b)} chars)')
    except Exception as e:
        print(f'bloco {i}: ERRO -> {e}')
