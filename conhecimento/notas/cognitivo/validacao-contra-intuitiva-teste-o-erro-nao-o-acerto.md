---
tags: [cognitivo, concorrencia, corrompido, estado, inconsistente, testing]
aliases: [Validacao contra-intuitiva: teste o erro, nao o acerto]
date: 2026-08-14
---

# Validacao contra-intuitiva: teste o erro, nao o acerto

**Dominio:** testing

Para cada funcao, o teste mais valioso nao e o 'caminho feliz' mas sim: (1) entrada vazia/nula, (2) entrada no limite, (3) entrada fora do dominio, (4) estado inconsistente, (5) concorrencia. Se sua funcao lida com arquivos: arquivo inexistente, permissao negada, disco cheio, arquivo corrompido. 80% dos bugs estao nos 20% de casos de erro.
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[testar-failover-ativamente]]