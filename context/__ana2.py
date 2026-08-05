import os, re, collections, sys
sys.path.insert(0, os.getcwd())

from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

CLUSTERS = g.CLUSTERS

def cluster_of_tag(tags):
    for t in tags:
        t = t.strip().lower()
        if t == 'projeto':
            continue
        for cl, sources in CLUSTERS.items():
            if t in sources:
                return cl
        # match por substring: fonte 'foo' casa tag 'foo-bar'?
        for cl, sources in CLUSTERS.items():
            for s in sources:
                if s in t:
                    return cl
    return 'geral'

notas_dir = g.OUTPUT_DIR
counter = collections.Counter()
unmapped = collections.Counter()
total = 0
for root, dirs, files in os.walk(notas_dir):
    for f in files:
        if not f.endswith('.md'):
            continue
        path = os.path.join(root, f)
        raw = open(path, encoding='utf-8', errors='replace').read()
        m = re.search(r'^---\s*\n(.*?)\n---', raw, re.S)
        tags = []
        if m:
            fm = m.group(1)
            tm = re.search(r'tags:\s*\[(.*?)\]', fm, re.S)
            if tm:
                tags = [x.strip() for x in tm.group(1).split(',') if x.strip()]
        total += 1
        cl = cluster_of_tag(tags)
        counter[cl] += 1
        if cl == 'geral':
            for t in tags:
                if t and t != 'projeto':
                    unmapped[t] += 1
                    break

print(f'total notas: {total}')
print('distribuicao de clusters:')
for cl, n in counter.most_common():
    print(f'  {cl}: {n}  ({100*n/total:.1f}%)')

print('\nnotas "geral" por primeira tag:')
for t, n in unmapped.most_common(30):
    print(f'  {n:4d}  {t}')
