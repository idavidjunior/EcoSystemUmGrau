import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from memory_engine import query, query_by_kind

print('=== RECENTES (último 10) ===')
for m in query(limit=10):
    print(f'  [{m["kind"]}] {m["task"][:80]}... ({m["confidence"]:.2f})')

print()
print('=== PADRÕES IDENTIFICADOS ===')
for m in query_by_kind('padrao', limit=15):
    print(f'  - {m["task"][:80]}...')

print()
print('=== DECISÕES ===')
for m in query_by_kind('decisao', limit=10):
    print(f'  - {m["task"][:80]}...')

print()
print('=== ERROS/CORREÇÕES ===')
for m in query_by_kind('erro', limit=10):
    print(f'  - {m["task"][:80]}...')