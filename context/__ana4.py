import os, re, collections, sys
sys.path.insert(0, os.getcwd())
from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

notas_dir = g.OUTPUT_DIR
tags_unicas = collections.Counter()
for root, dirs, files in os.walk(notas_dir):
    for f in files:
        if not f.endswith('.md'):
            continue
        raw = open(os.path.join(root, f), encoding='utf-8', errors='replace').read()
        m = re.search(r'^---\s*\n(.*?)\n---', raw, re.S)
        if not m:
            continue
        tm = re.search(r'tags:\s*\[(.*?)\]', m.group(1), re.S)
        if tm:
            for t in tm.group(1).split(','):
                t = t.strip()
                if t:
                    tags_unicas[t.lower()] += 1

print('total tags unicas:', len(tags_unicas))
for t, n in sorted(tags_unicas.items()):
    print(f'{n:4d}  {t}')
