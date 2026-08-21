---
tags: [estado, execucao, framework, global, seguranca]
aliases: [FIRST Principles para testes]
date: 2026-08-21
---

# FIRST Principles para testes

Propriedades de um bom teste unitario: Fast, Isolated, Repeatable, Self-validating, Timely.

Fast: Teste roda em milissegundos. Se demora, nao e teste unitario. Isolated: Teste nao depende de outros testes, ordem de execucao, ou estado global. Repeatable: Mesmo resultado sempre, em qualquer maquina. Self-validating: Teste passa ou falha — sem interpretacao humana. Timely: Teste escrito antes ou junto com o codigo. Se um teste viola FIRST, ele perde valor como rede de seguranca.
## Conexoes

- [[cluster-hub-cognicao]]
- [[framework-hub-frameworks]]