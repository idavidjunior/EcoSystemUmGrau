import json
with open('conhecimento/memoria/memories.json', 'r', encoding='utf-8') as f:
    memories = json.load(f)

has_file = sum(1 for m in memories if m.get('file'))
print(f'Total: {len(memories)}, com file: {has_file}')

# Check a few samples
for m in memories[:10]:
    print(f'id={m["id"]}, has_file={"file" in m}, file={m.get("file", "N/A")}, task={m.get("task", "")[:40]}')

# Check actual files in aprendizados
import os
files = os.listdir('conhecimento/aprendizados')
print(f'\nArquivos em aprendizados: {len(files)}')
for f in files[:10]:
    print(f'  {f}')