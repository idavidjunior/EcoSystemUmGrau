import sys, os, re, json, collections
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'scripts'))

from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

# analisa as notas existentes
notas_dir = g.NOTES_DIR
print('NOTES_DIR:', notas_dir, 'existe:', os.path.isdir(notas_dir))

if not os.path.isdir(notas_dir):
    import glob
    md = glob.glob(os.path.join(os.getcwd(), '**', '*.md'), recursive=True)
    print('total md no repo:', len(md))
    for p in md[:30]:
        print('  ', p)
    sys.exit(0)

meta_dir = os.path.join(notas_dir, '_meta')
sources = collections.Counter()
front = collections.Counter()

def load_meta():
    res = {}
    if os.path.isdir(meta_dir):
        for f in os.listdir(meta_dir):
            if f.endswith('.json'):
                try:
                    res[f[:-5]] = json.load(open(os.path.join(meta_dir, f), encoding='utf-8'))
                except Exception:
                    pass
    return res

metas = load_meta()
print('metas:', len(metas))

def cluster_of(source):
    src = (source or '').split('+')[0].strip()
    for cl, sources_list in g.CLUSTERS.items():
        if src in sources_list:
            return cl
    return 'geral'

clusters = collections.Counter()
unmapped = collections.Counter()
for slug, meta in metas.items():
    if isinstance(meta, dict):
        src = meta.get('source', '')
        cl = cluster_of(src)
        clusters[cl] += 1
        if cl == 'geral' and src:
            unmapped[src] += 1
    else:
        clusters['sem-meta'] += 1

print('distribuicao de clusters nas notas:')
for cl, n in clusters.most_common():
    print(f'  {cl}: {n}')

print('\nfontes nao mapeadas (seriam "geral") mais frequentes:')
for src, n in unmapped.most_common(30):
    print(f'  {n:4d}  {src}')
