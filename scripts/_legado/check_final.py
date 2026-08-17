import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from scripts.memory_engine import query, stats

print('=== STATS ===')
s = stats()
print(f'Total: {s["total"]}, Active: {s["active"]}')
print(f'By kind: {s["by_kind"]}')
print()
print('=== PREFERENCIAS ===')
prefs = query(kind='preferencia', limit=10)
for p in prefs:
    print(f'  [{p["kind"]}] {p["task"][:70]}... (conf={p.get("confidence", 1):.2f})')