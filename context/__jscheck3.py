import re
import esprima

src = open('docs/grafo_widget.html', encoding='utf-8').read()
# valida TODOS os blocos <script>, incluindo o vendor (pode ser grande)
blocks = re.findall(r'<script>(.*?)</script>', src, re.S)
print('blocos script:', len(blocks))
for i, b in enumerate(blocks):
    # pula o vendor (vis-network) se existir - valida so o codigo proprio
    if 'vis-network' in b[:2000] and i < len(blocks):
        try:
            esprima.parseScript(b[:10000] + '\n//truncado')
            print(f'bloco {i}: vendor OK (validacao parcial)')
        except Exception as e:
            print(f'bloco {i}: vendor SKIP ({e})')
        continue
    try:
        esprima.parseScript(b)
        print(f'bloco {i}: OK ({len(b)} chars)')
    except Exception as e:
        print(f'bloco {i}: ERRO -> {e}')

print('--- recursos presentes ---')
for probe in ['mk-controles', 'Velocidade', 'Quadro', 'data-filter="dom"',
              '_aplicarVelocidade', 'tamanhos', 'cba6f7', 'aplicarPersistidos']:
    print(f'  {probe}: {"SIM" if probe in src else "NAO"}')
