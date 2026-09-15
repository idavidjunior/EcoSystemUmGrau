---
tipo: erro
tags: [embroidery, digitizer, segmentation, background, noise, speckle, pipeline]
data: 2026-09-13
contexto: Preview 'tudo bagunçado' no ConversorBordado com fotos reais (logo Corinthians e screenshot). A CLI com test_image.png passava, mas fotos geravam dezenas de regiões-lixo e o fundo dominante 'devorava' o desenho.
decisao: Remover o fundo apenas na parte conectada à moldura (não por índice global de paleta), converter RGBA->branco antes da redução e filtrar objetos com pouquíssimos pontos. Removida a classe DigitizerPipeline duplicada em stitch_planner.py (código morto).
impacto: Logo Corinthians 42->10 regiões limpas (contornos reais + letras brancas internas preservadas); screenshot 108->2. 92 testes verdes.
---

# Causa raiz do preview 'tudo bagunçado' (ConversorBordado)

## Causas reais (com evidência)

1. Fundo dominante não era removido. `_identify_background_color` escolhia a cor
   mais frequente GLOBAL da paleta: no brasão escuro do Corinthians, a cor mais
   frequente era o PRETO do desenho, não o fundo branco da moldura. Resultado:
   região gigante quase-preta (mask 417x347, 3384 pts) engolindo detalhes.
2. Remoção por ÍNDICE de paleta removia a cor INTEIRA. Se removesse o branco,
   sumiriam também as letras brancas internas do brasão (detalhe legítimo).
3. Speckles de antialiasing/recorte: dezenas de regiões RUNNING/SATIN com 1-2
   pontos e máscaras 5-11px (ex.: 42 regiões no logo; 108 na screenshot).
   `min_region_area=50` deixava passar componentes finos (10x5 = 50px²).
4. PNGs com alfa: transparência virada para preto no RGB destruía o fundo.

## Correções aplicadas

### src/image/segmentation/segmentation_engine.py
- `_identify_background_color`: prioriza a cor dominante na MOLDURA (anel externo,
  min(h,w)//50 px). Só cai no fallback global se a moldura não tiver >= 55% de
  uma cor. (Fundo branco do logo agora é detectado.)
- `_compute_background_mask` (novo): máscara da cor de fundo conectada à borda
  via `measure.label` + `_border_connected`. Elementos internos da cor do fundo
  (letras brancas dentro do brasão preto) são PRESERVADOS e viram regiões próprias.
- `segment`: usa `mask & ~bg_mask` em vez de pular o índice.

### src/pipeline/digitizer_pipeline.py
- `_prepare_image` (novo): RGBA/LA/P+transparency → composição sobre fundo
  branco (tecido) antes da redução KMeans.
- `_filter_noise_objects` (novo): remove objetos com poucos pontos reais
  (conta comando STITCH, como o motor). Piso = `max(5, 0.008 * maior_objeto)`.
- `digitize` agora chama `_prepare_image` e `_filter_noise_objects`.

### src/embroidery/planning/stitch_planner.py
- Removida a classe `DigitizerPipeline` duplicada (linhas 172-217, código morto;
  nada importava — motor usa `src.pipeline.digitizer_pipeline`).

## Números antes/depois (test_fotos.py, depois removido)

| Imagem | Antes | Depois |
|---|---|---|
| Logo Corinthians (447x447) | 42 regiões / 5798 pts | 10 regiões / 9561 pts |
| Screenshot (1024x768) | 108 regiões / 188 pts | 2 regiões / 12 pts |

Depois: contorno preto do brasão (FILL), detalhes dourados SATIN 33-310 pts,
letras brancas internas como FILL próprios (1212/2768 pts). Nenhum speckle.

## Aprendizados reutilizáveis

1. Remoção de fundo em digitalização profissional = componente conectado à BORDA,
   nunca cor inteira da paleta. Isso preserva vazados internos (padrão PE-Design).
2. Piso de região por ÁREA (px²) vaza componentes finos (10x5). Piso por PONTOS
   gerados é o critério certo contra speckles de 1-5 pontos.
3. `remove_small_objects(..., max_size=)` na skimage 0.26 remove PIXELS MENORES
   que o valor (nome confuso, semântica correta para o intento de min_region_area).
4. Sempre normalizar alfa→branco/tecido ANTES do KMeans, não depois.

## Arquivos

- `src/image/segmentation/segmentation_engine.py`
- `src/pipeline/digitizer_pipeline.py`
- `src/embroidery/planning/stitch_planner.py`
- 92 testes verdes (`python -m pytest tests/ -q`)
