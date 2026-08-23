import json
d = json.load(open('conhecimento/memoria/memories.json', encoding='utf-8'))
for m in d:
    if m['kind'] == 'preferencia':
        print(f'{m["id"]}: {m["task"][:80]} -> {m["summary"][:200]}')
        print()