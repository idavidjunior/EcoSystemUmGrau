from pathlib import Path
import re, json

content = Path(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html').read_text(encoding='utf-8')

# Extract node count
nodes_match = re.search(r'const nodes = new vis\.DataSet\((\[.*?\]\))', content)
edges_match = re.search(r'const edges = new vis\.DataSet\((\[.*?\]\))', content)

if nodes_match:
    nodes_json = nodes_match.group(1)
    try:
        parsed = json.loads(nodes_json)
        print(f'Nodes: {len(parsed)} items - valid JSON')
    except json.JSONDecodeError as e:
        print(f'Nodes JSON ERROR: {e}')
        print(f'  Around error: ...{nodes_json[max(0,e.pos-50):e.pos+50]}...')
else:
    print('Nodes not found')

if edges_match:
    edges_json = edges_match.group(1)
    try:
        parsed = json.loads(edges_json)
        print(f'Edges: {len(parsed)} items - valid JSON')
    except json.JSONDecodeError as e:
        print(f'Edges JSON ERROR: {e}')
        print(f'  At pos {e.pos}: ...{edges_json[max(0,e.pos-80):e.pos+80]}...')
else:
    print('Edges not found')

# Check if any node data has control characters that break JSON
print()
sample_nodes = nodes_json[:500]
print('First 500 chars nodes:', sample_nodes)
sample_edges = edges_json[-200:]
print('Last 200 chars edges:', sample_edges)