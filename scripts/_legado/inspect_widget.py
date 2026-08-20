import sys
import os
import json

sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

print('=== INSPECÇÃO DO CÓDIGO DO WIDGET ===')
print()

# 1. Inspect eco_widget.py key functions
print('--- eco_widget.py ---')
with open('C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\scripts\\eco_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for key functions
key_funcs = ['activate', 'deactivate', '_iniciar_widget', '_escrever_estado', '_widget_pid', '_mostrar_widget', '_esconder_widget']
for func in key_funcs:
    if f'def {func}' in content:
        print(f'  {func}: EXISTE')
    else:
        print(f'  {func}: NÃO ENCONTRADO')

print()
print('--- Verificando CONTROLE state file ---')
controle_path = r'C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\runtime\\narracao_estado.json'
if os.path.exists(controle_path):
    with open(controle_path, 'r', encoding='utf-8') as f:
        d = json.loads(f.read())
    print(f'CONTROLE content: ativo={d.get("ativo")}, pausado={d.get("pausado")}')

print()
print('--- Verificando BRIDGE_FLAG ---')
bridge_flag = r'C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\runtime\\bridge_enabled.flag'
if os.path.exists(bridge_flag):
    with open(bridge_flag, 'r', encoding='utf-8') as f:
        bf = json.load(f)
    print(f'BRIDGE_FLAG: ativo={bf.get("ativo")}, timestamp={bf.get("timestamp")}')

print()
print('--- Fim da inspeção ---')