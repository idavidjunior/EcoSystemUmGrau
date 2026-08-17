import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
from scripts.memory_engine import query

prefs = query(kind='preferencia', limit=20)
for p in prefs:
    print(f'  [{p["kind"]}] {p["task"][:80]}... (conf={p.get("confidence", 1):.2f})')
    print(f'    Summary: {p["summary"][:100]}')
    print()