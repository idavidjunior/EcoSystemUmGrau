---
tipo: padrao
tags: [cerebro-vivo, cluster-visual, google-skills, skills-mcp, separacao-radial, padrao-reutilizavel]
data: 2026-09-15
contexto: Integração das skills oficiais do Google (gemini-api-dev, gemini-live-api-dev, gemini-omni-flash-api) ao ecossistema como novo cluster "google-skills" no Cérebro Vivo, aplicando o padrão de 5 etapas dos agentes — da pasta funcional em mcp/ até a separação radial no widget.
decisao: Padrão de 6 etapas para importar skills oficiais externas como cluster visual:

## 1. CRIAR LOCAL FUNCIONAL (mcp/)
- Domínio novo em `mcp/<dominio>/habilidades/<nome>/`
- `skill.md` (minúsculo) com o padrão Agent Skills do ecossistema em pt-BR
- Skills oficiais copiadas em subpastas próprias com `SKILL.md` (maiúsculo, padrão Google), `references/` e `scripts/` intactos

## 2. CRIAR NÓS NO VAULT (conhecimento/notas/)
- Pasta `conhecimento/notas/<grupo>/` com 1 .md por skill + 1 .md para a skill-mãe
- Frontmatter obrigatório: `tags`, `aliases`, `date`, `categoria: <grupo>`
- Wikilinks: `[[cluster-hub-ecossistema]]`, `[[cluster-hub-<grupo>]]`, pares/metódos
- Hub em `conhecimento/notas/_hubs/cluster-hub-<grupo>.md`
- IMPORTANTE: tags SEMANTICAS e ESPECIFICAS (`gemini-api-dev`, `interactions-api`), NUNCA genéricas (`gemini`, `google`, `api`, `sdk`) — tags genéricas colidem com notas de outros clusters no aprendizado do ClusterMapper

## 3. REGISTRAR CLUSTER NO GERADOR (generate-graph-html.py)
- `CLUSTERS['<grupo>'] = ['slug1', 'slug2', ...]` (slugs exatos)
- `CLUSTER_COR['<grupo>'] = '#' + cor hex distinta` (não repetir cores existentes)
- `CLUSTER_DESC['<grupo>'] = 'Tooltip do botão'`
- Forçar pela categoria em `_resolver_cluster`:
  ```python
  if categoria == '<grupo>':
      return '<grupo>'
  ```

## 4. REGISTRAR NO CLUSTERMAPPER (cluster_mapper.py)
- Adicionar `'<grupo>': [...slugs + variantes normalizadas...]` em `ClusterMapper.CLUSTERS`
- Manter consistência com o CLUSTERS estático do gerador
- Também com tags específicas, sem termos genéricos no índice normalizado

## 5. INTEGRAR NO WIDGET (cerebro.html)
- `PALETA['<grupo>'] = '#cor-hex'` (após o bloco de `agentes`)
- `DESCRICOES_FOCO['<grupo>'] = 'Tooltip do painel Foco'`
- (FORTE é opcional — 'agentes' também não está lá)

## 6. SEPARAÇÃO RADIAL GENERALIZADA (widget_grafo.py → layout_3d)
- GENERALIZAR o bloco de separação para aceitar N clusters periféricos (DRY):
  ```python
  perifericos = ('agentes', '<grupo>')  # tupla expandível
  for cl_perif in perifericos:
      cl_i = [i for i in range(n) if nos[i].get('cl') == cl_perif]
      if len(cl_i) >= 3:
          cg = pos.mean(axis=0)
          vec = pos[cl_i].mean(axis=0) - cg
          dist = np.linalg.norm(vec)
          if dist > 1e-6:
              dir_unit = vec / dist
              for i in cl_i:
                  pos[i] = pos[i] + dir_unit * (np.linalg.norm(pos[i] - cg) * 0.8)
  ```

## REGENERAR E TESTAR
```bash
python scripts/refresh_cerebro_cache.py  # atualiza cache do widget
python -m py_compile scripts/generate-graph-html.py scripts/widget_grafo.py scripts/cluster_mapper.py
@ecow  # fechar/abrir widget para ver mudanças
```

## RESULTADO OBTIDO
- Cluster "google-skills": 4 notas + 1 hub = 5 nós azuis (#4285f4, cor do Google)
- Visualmente separado na periferia junto dos agentes (mesma expansão radial 0.8x)
- Falso positivo corrigido: tag 'gemini' genérica puxava `cadeia-de-provedores-com-failover-inteligente` para o cluster; removida e a nota voltou para 'ecossistema'
- 0 regressões: compilação OK nos 3 scripts, cache regenerado com contagens coerentes

## REUTILIZAÇÃO PARA OUTROS GRUPOS
Para novo grupo (ex: "anthropic-skills", "openai-skills"):
1. Repetir etapas 1-6 substituindo `<grupo>`, cor, slugs
2. Tags SEMPRE específicas do domínio, nunca do fornecedor genérico
3. Adicionar o grupo à tupla `perifericos` do widget_grafo.py (não criar bloco novo)
impacto: Padrão consolidado para importar skills externas como cluster visual destacado no Cérebro Vivo, com anti-colisão de tags genéricas e separação radial configurável.
reutilizavel: Sim. Checklist completo acima para aplicar a qualquer conjunto de skills/domínios externos.