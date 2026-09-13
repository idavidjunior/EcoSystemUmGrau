---
tipo: padrao
tags: [cerebro-vivo, cluster-visual, agentes, separacao-radial, rotacao-zero, padrao-reutilizavel]
data: 2026-09-12
contexto: Implementação completa do cluster "agentes" no Cérebro Vivo (widget 3D do conhecimento) — desde a criação das notas no vault até a separação visual radial e correção da rotação zero.
decisao: Padrão completo em 5 etapas reutilizável para qualquer grupo de nós:

## 1. CRIAR NÓS NO VAULT (conhecimento/notas/)
- Pasta dedicada: `conhecimento/notas/<grupo>/` com 1 .md por item
- Frontmatter obrigatório: `tags`, `aliases`, `date`, `categoria: <grupo>`
- Wikilinks conectando: hub pai (`[[cluster-hub-ecossistema]]`), hub do grupo (`[[cluster-hub-<grupo>]]`), pares do grupo, skills/cláusulas relevantes
- Hub do grupo em `conhecimento/notas/_hubs/cluster-hub-<grupo>.md` indexando todos

## 2. REGISTRAR CLUSTER NO GERADOR (generate-graph-html.py)
- Adicionar em `CLUSTERS`: `'<grupo>': ['slug1', 'slug2', ...]` (slugs das notas)
- Adicionar em `CLUSTER_COR`: `'<grupo>': '#cor-hex-distinta'`
- Adicionar em `CLUSTER_DESC`: `'<grupo>': 'Descrição para tooltip'`
- Forçar cluster pela categoria em `_resolver_cluster`:
  ```python
  if categoria == '<grupo>':
      return '<grupo>'
  ```

## 3. INTEGRAR NO WIDGET (cerebro.html)
- `PALETA['<grupo>'] = '#cor-hex'`
- `DESCRICOES_FOCO['<grupo>'] = 'Tooltip do painel Foco'`
- Regenerar cache: `python scripts/refresh_cerebro_cache.py`

## 4. SEPARAÇÃO RADIAL VISUAL (widget_grafo.py → layout_3d)
Após agrupar região de fala, adicionar bloco:
```python
# afasta cluster "<grupo>" do centro: empurra radialmente
grupo_i = [i for i in range(n) if nos[i].get('cl') == '<grupo>']
if len(grupo_i) >= 3:
    cg = pos.mean(axis=0)           # centro global
    cgrupo = pos[grupo_i].mean(axis=0)
    vec = cgrupo - cg
    dist = np.linalg.norm(vec)
    if dist > 1e-6:
        dir_unit = vec / dist
        for i in grupo_i:
            pos[i] = pos[i] + dir_unit * (np.linalg.norm(pos[i] - cg) * 0.8)
```
- Fator 0.8 = expansão radial (ajustável)
- Mínimo 3 nós para ativar
- Estrutura interna preservada (deslocamento na mesma direção)

## 5. ROTAÇÃO ZERO REAL (cerebro.html → laco())
No loop principal, remover base fixa que impede parada total:
```javascript
// Antes (bug): base 0.0015 sempre presente
const rotAlvo = 0.0015 + (AJUSTES.rotacao || 0.6) * 0.0045;

// Depois (corrigido): ternário explícito
const rotAlvo = AJUSTES.rotacao > 0 ? (0.0015 + AJUSTES.rotacao * 0.0045) : 0;
```
- Slider 0% = rotação zero real (grafo para completamente)
- Padrão reutilizável: `valor > 0 ? calculo : 0` em vez de base fixa + multiplicador

## REGENERAR E TESTAR
```bash
python scripts/refresh_cerebro_cache.py  # atualiza cache do widget
python scripts/generate-graph-html.py    # grafo estático
@ecow  # fechar/abrir widget para ver mudanças
```

## RESULTADO OBTIDO
- Cluster "agentes": 22 nós + 1 hub = 23 nós roxos (#e066ff)
- Visualmente separado na periferia do grafo (expansão radial 0.8x)
- Cor distinta, tooltip no painel Foco, conexões mantidas
- Rotação 0% = grafo parado completamente

## REUTILIZAÇÃO PARA OUTROS GRUPOS
Para novo grupo (ex: "projetos-android", "skills-mcp", "missões-ativas"):
1. Repetir etapas 1-5 substituindo `<grupo>`, cor, slugs, slugs
2. Ajustar fator de expansão (0.8) e mínimo de nós (3) conforme densidade
3. Mesmo padrão de rotação zero aplica-se a qualquer slider que deve zerar de verdade
impacto: Padrão consolidado para criar clusters visualmente destacados no Cérebro Vivo, com separação radial configurável e controles que respeitam o zero absoluto.
reutilizavel: Sim. Checklist completo acima para aplicar a qualquer conjunto de nós no vault.