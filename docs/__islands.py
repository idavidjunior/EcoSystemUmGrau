import sys
from collections import defaultdict
sys.path.insert(0, 'scripts')
import generate_graph_html as g

nos, arestas = g.extrair_nos()

# arestas eh um set de tuples
print(f'nos: {len(nos)} | arestas: {len(arestas)}')
adj = defaultdict(set)
for a, b in arestas:
    adj[a].add(b)
    adj[b].add(a)

cat = {}
label = {}
grau = {}
for n in nos:
    cat[n['id']] = n['categoria']
    label[n['id']] = n['label']
    grau[n['id']] = 0
for a, b in arestas:
    grau[a] += 1
    grau[b] += 1

ids = [n['id'] for n in nos]
visitados = set()
componentes = []
for nid in ids:
    if nid in visitados:
        continue
    comp = []
    stack = [nid]
    while stack:
        cur = stack.pop()
        if cur in visitados:
            continue
        visitados.add(cur)
        comp.append(cur)
        for nb in adj[cur]:
            if nb not in visitados:
                stack.append(nb)
    componentes.append(comp)

# isola ilhas realmente desconexas (nao o componente gigante)
gigante = max(componentes, key=len)
ilhas = [c for c in componentes if c is not gigante]

def cats(c):
    d = defaultdict(int)
    for nid in c:
        d[cat.get(nid, '?')] += 1
    return dict(d)

print(f'\nCOMPONENTE GIGANTE: {len(gigante)} nos')
print(f'ILHAS (desconexas): {len(ilhas)}')
print('=' * 60)
for idx, c in enumerate(sorted(ilhas, key=lambda c: -len(c)), 1):
    print(f'\nILHA {idx}: {len(c)} nos | categorias: {cats(c)}')
    for nid in sorted(c, key=lambda x: -grau.get(x, 0)):
        print(f'   - {label.get(nid,"?")}   [{cat.get(nid,"?")}]  grau={grau.get(nid,0)}')

# nos totalmente sem arestas
sem_aresta = [nid for nid in ids if grau.get(nid, 0) == 0]
print(f'\nNOS SEM NENHUMA ARESTA (grau 0): {len(sem_aresta)}')
for nid in sem_aresta:
    print(f'   - {label.get(nid,"?")}   [{cat.get(nid,"?")}]')