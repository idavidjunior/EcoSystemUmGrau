---
tags: [framework, matching, ocr, relativas, template]
aliases: [Cascata de Interacao (CI)]
date: 2026-08-06
---

# Cascata de Interacao (CI)

Framework de 4 niveis para interagir com qualquer elemento: N1 = seletor direto (data-testid/resource-id), N2 = seletor semantico (classe/tag/texto), N3 = coordenadas relativas, N4 = OCR + template matching. Subir um nivel a cada 3 falhas consecutivas

Implementacao: para cada interacao, tentar N1 com timeout curto (1s). Se falhar, tentar N2 (2s). Se falhar, tentar N3 (3s). Se falhar, N4 (5s). Apos sucesso em N2+, tentar proxima interacao comecando de N1 (reset). Logar em qual nivel cada elemento foi encontrado para aprendizado futuro
## Conexoes

- [[framework-hub-frameworks]]