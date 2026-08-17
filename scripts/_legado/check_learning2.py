import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from scripts.memory_engine import query

print('=== RECENTES ===')
for m in query(limit=10):
    kind = m['kind']
    task = m['task'][:70]
    conf = m.get('confidence', 1)
    print(f'  [{kind}] {task}... (conf={conf:.2f})')

print()
print('=== PADROES ===')
for m in query(kind='padrao', limit=10):
    print(f'  - {m["task"][:70]}...')

print()
print('=== DECISOES ===')
for m in query(kind='decisao', limit=10):
    print(f'  - {m["task"][:70]}...')

print()
print('=== ERROS ===')
for m in query(kind='erro', limit=10):
    print(f'  - {m["task"][:70]}...')

print()
print('=== EPISODIOS ===')
for m in query(kind='episodio', limit=10):
    print(f'  - {m["task"][:70]}...')