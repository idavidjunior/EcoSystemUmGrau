import os, sys, json, collections
sys.path.insert(0, os.getcwd())
from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

graph = json.load(open(g.GRAPH_FILE, encoding='utf-8'))
# inspect structure of first pattern
pats = graph.get('patterns', [])
print('patterns count:', len(pats))
if pats:
    p = pats[0]
    print('pattern keys:', list(p.keys()))
    print('sample sources:', p.get('sources', [])[:5])
    print('sample tags:', p.get('tags', [])[:5])

# which key contains the per-category notes
for key in ['patterns', 'decisions', 'bug_fixes', 'cognitive_patterns', 'heuristics', 'frameworks', 'tool_knowledge']:
    items = graph.get(key, [])
    srcs = collections.Counter()
    tg = collections.Counter()
    for it in items:
        for s in it.get('sources', []):
            srcs[s] += 1
        for t in it.get('tags', []):
            tg[t] += 1
    print(f'\n== {key}: {len(items)} items ==')
    print('  top sources:', srcs.most_common(5))
    print('  top tags:', tg.most_common(5))
