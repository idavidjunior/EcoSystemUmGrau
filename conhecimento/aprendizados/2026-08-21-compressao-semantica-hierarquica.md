---
tipo: padrao
tags: [hsc, compressao-semantica, anti-alucinacao, extracao, validator]
data: 2026-08-21
contexto: Implementação da Compressão Semântica Hierárquica (spec de 10 fases)
decisao: Compressão 100% extrativa e determinística; fidelidade medida como recuperabilidade nos níveis consultáveis (L2-L8), nunca contra o nível mais comprimido sozinho.
impacto: scripts/hsc.py operacional com CLI; docs reais do eco alcançam fidelidade 0.93-0.97 acima do threshold 0.85; base para integração futura com cognitive_core e memory_engine.
---

# Compressão Semântica Hierárquica — lições da implementação

## O que foi construído
scripts/hsc.py (~1050 linhas, stdlib puro) implementa os 9 níveis de representação
(source → semantic_core) com extratores determinísticos, detector de redundância,
validador de fidelidade, rastreabilidade por fragmento, gestão de confiança,
detector de conflitos entre fontes, storage versionado com cache SHA-256 e CLI
(compress/text/get/list/stats/multi/recommend).

## Decisões que funcionaram
1. EXTRATIVO por construção: nada é gerado, tudo é seleção/organização do original.
   Anti-alucinação estrutural, não por prompt.
2. Fidelidade = recuperabilidade: um fato crítico está preservado se aparece verbatim
   em qualquer nível consultável OU no core com números/datas conferindo. Medir só
   contra o nível mais comprimido era injusto e dava 0.62 em docs reais.
3. Garantia de críticos no core: fatos com número/data/negação entram no núcleo mesmo
   fora do top-10 de importância (teto total 20). Isso subiu fatos_criticos de 0.68
   para 0.95 sem inflar a prosa.
4. Calibração empírica de limiares: mediu-se jaccard/dice em pares verdadeiros vs
   controle antes de fixar thresholds (paráfrase: dice≥0.40+jac≥0.10; controle ficava
   ≤0.15). Nunca chutar limiar.

## Erros encontrados e corrigidos
- dividir_frases juntava todas as linhas numa frase única → colapsava toda extração.
- findall retorna lista; subtração de set quebrou 19/24 testes de uma vez.
- Cache servia registros criados pelo código bugado (hash do texto, não do código).
  Testes agora usam sandbox runtime/.hsc_test apagado no tearDownModule.
- Sujeito genérico "A" (artigo) virava stopword vazio → conflitos nunca detectados.
  _sujeito_generico agora pula stopwords; predicado começa depois do sujeito.
- Markdown (frontmatter, cabeçalhos, tabelas) virava ruído que derrubava fidelidade.
  _remover_ruido_estrutural limpa antes de extrair; source level mantém original intacto.

## Padrão para o futuro
Quando um check de validação falhar em doc real, diagnosticar QUAL check antes de
ajustar threshold. Threshold baixo demais esconde perda real; alto demais sem garantia
estrutural força pass=false legítimo. A resposta certa quase sempre é melhorar a
garantia de preservação, não afrouxar a régua.
