import os, re, collections, sys
sys.path.insert(0, os.getcwd())
from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

notas_dir = g.OUTPUT_DIR
known_sources = set()
for cl, sources in g.CLUSTERS.items():
    known_sources.update(sources)

# coleta todas as tags de projeto: aquelas que aparecem junto com "projeto" ou que
# são fontes em CLUSTERS. Também lista todas as tags distintas para inspeção.
todas_tags = collections.Counter()
notas_por_tag = collections.defaultdict(list)
for root, dirs, files in os.walk(notas_dir):
    for f in files:
        if not f.endswith('.md'):
            continue
        raw = open(os.path.join(root, f), encoding='utf-8', errors='replace').read()
        m = re.search(r'^---\s*\n(.*?)\n---', raw, re.S)
        tags = []
        if m:
            tm = re.search(r'tags:\s*\[(.*?)\]', m.group(1), re.S)
            if tm:
                tags = [x.strip() for x in tm.group(1).split(',') if x.strip()]
        for t in tags:
            if t == 'projeto':
                continue
            todas_tags[t.lower()] += 1
            notas_por_tag[t.lower()].append(f)

print('=== top 80 tags mais frequentes ===')
for t, n in todas_tags.most_common(80):
    print(f'  {n:4d}  {t}')

print('\n=== tags que parecem projeto/fonte (candidatas) ===')
cands = ['android', 'androidpuresdk', 'sdk', 'mp3player', 'music', 'itunes', 'ler', 'navegacao',
         'session', 'opencode', 'ecossistema', 'mcp', 'rustdesk', 'auth', 'server', 'provider',
         'cognitivo', 'metacogni', 'meta', 'react', 'flutter', 'expo', 'app', 'widget', 'treinamento']
for c in cands:
    for t, n in todas_tags.most_common():
        if c in t:
            print(f'  {n:4d}  {t}')
