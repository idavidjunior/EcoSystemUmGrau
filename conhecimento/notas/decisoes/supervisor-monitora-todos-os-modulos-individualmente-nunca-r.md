---
tags: [decisao, inteira, lerarquitetura, missao, modulo, reinicia]
aliases: [Supervisor monitora todos os modulos individualmente — nunca]
date: 2026-08-10
---

# Supervisor monitora todos os modulos individualmente — nunca reinicia missao inteira por falha de um modulo.

**Fonte:** ler_arquitetura

Isolamento de falha: se o validator falha, recupera so o validator, nao o planner.
## Conexoes

- [[checkpoints-salvos-antes-de-cada-iteracao-sobrevive-a-crash-]]
- [[cluster-hub-ler]]
- [[decisao-hub-decisoes]]
- [[estado-persiste-em-json-nao-sqlite-legivel-editavel-fora-do-]]
- [[ler-usa-python-puro-stdlib-only-zero-dependencias-externas-i]]
- [[pontuacao-ponderada-com-6-categorias-req-30-func-30-testes-1]]