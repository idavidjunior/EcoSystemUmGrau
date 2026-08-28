import json
with open('mem_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Nodes: {len(data.get("nodes", []))}')
if data.get('nodes'):
    n = data['nodes'][0]
    print(f'Sample: id={n["id"]}, title={n["title"][:40]}, kind={n["kind"]}, decayScore={n["decayScore"]}, filePath={n["filePath"]}')