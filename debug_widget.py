import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import re
from widget_grafo import _build_view

src = _build_view().read_text(encoding='utf-8')

scripts = re.findall(r'<script[^>]*src="([^"]*)"', src)
print('Scripts externos na ordem:')
for s in scripts:
    print('  ', s)
print()

idx_net = src.find('new vis.Network')
idx_vendor = src.find('vis-network.min.js')
idx_body_start = src.find('<body>')
idx_net_in_body = src.find('const container = document.getElementById')
print('Posicao init network:', idx_net)
print('Posicao ref vendor/CDN:', idx_vendor)
print('Body comeca em:', idx_body_start)
print('container getElementById em:', idx_net_in_body)

# Encontrar o bloco onde vis.Network e inicializado para ver o conteudo completo
print()
print('--- Ordem de execucao ---')
print('Script tag src (vendor) em:', idx_vendor)
print('Script init network em:', idx_net)
print('O init network vem DEPOIS do script src:', idx_net > idx_vendor)
