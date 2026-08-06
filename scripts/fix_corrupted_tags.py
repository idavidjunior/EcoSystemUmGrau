"""Fix corrupted 'sessionsession' tags in knowledge_graph.json"""
import json
from pathlib import Path

KG = Path(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\ler-runtime\knowledge\knowledge_graph.json')
VAULT = Path(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\conhecimento')

with open(KG, encoding='utf-8') as f:
    kg = json.load(f)

nodes = kg.get('nodes', kg) if isinstance(kg, dict) else kg

bad = [n for n in nodes if isinstance(n.get('tags'), list) and any('sessionsession' in str(t) for t in n.get('tags', []))]

print(f'Found {len(bad)} nodes with corrupted tags:')
for n in bad:
    old_tags = n.get('tags', [])
    new_tags = [t.replace('sessionsession', 'session') for t in old_tags]
    n['tags'] = new_tags
    src = n.get('source_file', '?')
    print(f'  id={n.get("id")}')
    print(f'  old tags: {old_tags}')
    print(f'  new tags: {new_tags}')
    print(f'  source: {src}')
    
    # Fix the vault markdown file too
    if src:
        md_path = VAULT / f'{src}.md'
        if md_path.exists():
            content = md_path.read_text(encoding='utf-8')
            if 'sessionsession' in content:
                fixed = content.replace('sessionsession', 'session')
                md_path.write_text(fixed, encoding='utf-8')
                print(f'  VAULT FILE FIXED: {md_path}')
    print()

# Save fixed knowledge graph
kg['nodes'] = nodes
with open(KG, 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)
print('Knowledge graph saved with fixed tags.')