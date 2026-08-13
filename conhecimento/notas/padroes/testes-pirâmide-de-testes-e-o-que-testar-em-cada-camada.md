---
tags: [esperado, funções, não, padrao, puras, testes]
aliases: [Testes: pirâmide de testes e o que testar em cada camada]
date: 2026-08-13
---

# Testes: pirâmide de testes e o que testar em cada camada

**Fonte:** testes

A pirâmide de testes organiza a suíte em camadas com custo, velocidade e estabilidade crescentes conforme sobe. **Base (unitários):** a maioria dos testes. Testam uma unidade isolada (função, método, classe) sem I/O real. Devem ser rápidos (milissegundos), determinísticos e rodar em paralelo. Teste aqui: lógica de negócio pura, regras de cálculo, formatação, validação de entrada, decisões com condicionais complexas, transformações de dados e funções puras. Evite testar getters triviais e detalhes de implementação (prova falsa de segurança). **Meio (integração):** testam a colaboração entre unidades com dependências reais ou quase reais: banco de dados, filas, caches, sistema de arquivos, serviços externos. Teste aqui: mapeamento ORM, queries e transações, concorrência e locking, contratos com bibliotecas de terceiros, e o comportamento de camadas adjacentes. São mais lentos e frágeis — mantenha a quantidade controlada e prefira um banco de teste real (ex.: SQLite em memória só se o comportamento do SGBD for irrelevante). **Topo (e2e):** poucos, simulam o fluxo completo pela interface real (HTTP, UI). Testam os cenários felizes críticos do usuário. Devem ser estáveis e usar ambientes de staging ou contratos controlados; são caros para manter. **Regra prática:** quando um teste e2e quebra, o problema deveria ter sido pego mais embaixo. Se você conserta bugs sempre nos unitários, a pirâmide está saudável. Escreva testes novos com o formato AAA (arrange, act, assert) e nomeie pelo comportamento esperado, não pela implementação. O antifraude clássico é a 'pirâmide invertida': suíte pesada em e2e que roda devagar e quebra sem motivo — sinal de poucos unitários e acoplamento a infraestrutura.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[testes-cobertura-de-código-como-métrica-o-que-ela-mostra-e-o]]
- [[testes-mocks-fakes-e-stubs-e-quando-evitar-mockar]]
- [[testes-tdd-e-quando-ele-compensa]]
- [[testes-testes-de-contrato-e-testes-de-api]]