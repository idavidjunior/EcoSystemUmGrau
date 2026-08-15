---
tags: [críticas, padrao, setup, supera, testes, áreas]
aliases: [Testes: TDD e quando ele compensa]
date: 2026-08-15
---

# Testes: TDD e quando ele compensa

**Fonte:** testes

TDD (Test-Driven Development) segue o ciclo **red → green → refactor**: escreva um teste que falhe para o comportamento desejado (red), implemente o mínimo para passar (green) e então melhore o código mantendo os testes verdes (refactor). O ritmo é de passos curtos: um teste por vez, rodando a suíte frequentemente. **Vantagens:** feedback imediato sobre o design da API — você desenha a interface pelo ponto de uso; cobertura por intenção (o teste documenta o contrato); refatoração segura; regressão rara; e menos debug porque você sabe exatamente o que foi exercitado. **Quando compensa:** lógica de negócio com regras ricas e bordas (preço, impostos, elegibilidade), parsing e formatação, algoritmos, correção de bugs (escreva antes um teste que reproduza o bug), e código novo em áreas críticas. **Quando NÃO compensa:** protótipos e spikes descartáveis, integração com frameworks muito verbosos onde a maior parte do código é 'colagem' (UI, mapeamentos triviais de DTO, config), código que vai ser exploratório, e quando o custo de setup do teste supera o valor. Nesses casos, testes de caracterização (pós-fato) ou apenas integração são melhores. **Armadilhas:** TDD vira teatro quando o teste é escrito junto com a implementação em um só passo (red fingido) — o valor vem do red que falha pelo motivo certo; assert em detalhes internos torna o refactor impossível. **Dica de engenheiro:** o TDD brilha em 'núcleo doce' (core puro) e perde valor nas bordas adaptadoras. Use a tríade: testes escritos primeiro para o domínio, e testes de contrato para as bordas.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[testes-cobertura-de-código-como-métrica-o-que-ela-mostra-e-o]]
- [[testes-mocks-fakes-e-stubs-e-quando-evitar-mockar]]
- [[testes-pirâmide-de-testes-e-o-que-testar-em-cada-camada]]
- [[testes-testes-de-contrato-e-testes-de-api]]