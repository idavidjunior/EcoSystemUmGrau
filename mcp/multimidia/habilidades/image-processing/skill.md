---
name: image-processing
description: Processamento de imagem — OCR de imagens e PDFs, extracao de texto de imagens, conversao e analise visual de imagens estaticas. Ativa quando o usuario precisa extrair texto de imagem, fazer OCR, analisar, converter ou transformar imagens. Trigger keywords: "OCR", "imagem", "imagens", "png", "jpg", "screenshot", "captura", "extrair texto da imagem", "converter imagem", "leitura de imagem", "pdf".
---

# image-processing — Processamento de Imagem

## Objetivo

Extrair informação de imagens estáticas: OCR (imagem/PDF → texto), conversão de
formatos, análise visual e transformações.

## Operações

### OCR (imagem e PDF → texto)
- Screenshots, fotos de tela, documentos escaneados, PDFs com texto em imagem.
- Pipeline: capturar/detectar imagem → OCR → texto estruturado.

### Captura
- Screenshots do sistema para diagnóstico visual (padrões de UI, erros de render).
- Reuso: ferramentas de captura já usadas no diagnóstico do grafo (diag_*.py).

### Conversão
- Entre formatos (png/jpg/webp/bmp), redimensionar, recortar, otimizar.

### Análise visual
- Detecção de elementos de UI, cores dominantes, estrutura de layout em capturas.

## Regras
- OCR prioritário quando o conteúdo está "preso" em imagem (sem texto extraível).
- Diagnóstico de UI: prefira captura + OCR a descrever "de memória" o que está na tela.

## Arquivos
- `skill.md` — definição.
- Reuso: utilidades de captura em `scripts/diag_*.py`, `scripts/device_probe.py`.
