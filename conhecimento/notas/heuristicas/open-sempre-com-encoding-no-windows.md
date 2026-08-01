---
tags: [heuristica, debugging]
aliases: [open() sempre com encoding no Windows]
date: 2026-08-01
---

# open() sempre com encoding no Windows

**Dominio:** debugging | **Fonte:** ler_aprendizado

Todo open() de arquivo texto deve especificar encoding. No Windows, o default muda conforme o locale do sistema.
