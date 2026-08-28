import json
with open('mem_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for n in data['nodes'][:5]:
    print(f'{n["kind"]}: decayScore={n["decayScore"]}, filePath={n["filePath"]}, title={n["title"][:30]}')