import json
with open('conhecimento/memoria/memories.json', encoding='utf-8') as f:
    data = json.load(f)
for m in data:
    text = f'{m["task"]} {m["summary"]}'.lower()
    if 'grafo' in text or 'graph' in text or 'dashboard' in text or 'amarelo' in text:
        print(f'{m["id"]}: {m["task"][:100]}')
        print(f'  {m["summary"][:150]}')
        print()