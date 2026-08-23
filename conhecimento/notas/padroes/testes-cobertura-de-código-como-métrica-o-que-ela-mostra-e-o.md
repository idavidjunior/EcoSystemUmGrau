---
tags: [badge, mutation, padrao, provam, testes, testing]
aliases: [Testes: cobertura de código como métrica — o que ela mostra ]
date: 2026-08-22
---

# Testes: cobertura de código como métrica — o que ela mostra e o que esconde

**Fonte:** testes

Cobertura (linha, branch, function) mede **quanto do código foi executado** pelos testes — nada mais. Ela é uma métrica de **execução**, não de **qualidade**. **O que ela mostra:** regiões mortas e código nunca exercitado, base para encontrar lacunas; tendência ao longo do tempo (queda = sinal de alerta); e o mínimo de sanidade da suíte. **O que ela esconde:** (1) não diz se os asserts verificam o comportamento correto — testes sem assert ou com assert trivial 'cobrem' o código mas provam nada; (2) cobertura de linha ignora caminhos — 100% de linha pode ter zero de branch nos casos de borda; (3) mockar demais infla cobertura falsamente (o caminho real nunca roda); (4) não mede integrações nem contratos com o mundo externo; (5) não detecta testes frágeis, duplicados ou lentos; (6) não mede cobertura de requisitos — regra de negócio inteira pode estar errada com 100% de cobertura de código. **Uso profissional:** trate cobertura como **ferramenta de diagnóstico**, não como alvo de meta cega. Defina um piso (ex.: 80% de branch em módulos críticos) e exija justificativa para quedas, mas **proíba gamification** (forçar 100% em código trivial só para o badge). Ferramentas: jaCoCo (Java), istanbul/c8 (Node), coverage.py (Python), Coverlet (C#). Boas práticas: gere relatório por diff em PRs (cobertura do código novo), integre ao CI com gate apenas nos módulos críticos, e use **mutation testing** (ex.: PIT, Stryker) como upgrade: ele introduz bugs no código e verifica se a suíte os detecta — cobertura de mutações é um proxy muito melhor de eficácia do que cobertura de linha.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[testes-mocks-fakes-e-stubs-e-quando-evitar-mockar]]
- [[testes-pirâmide-de-testes-e-o-que-testar-em-cada-camada]]
- [[testes-tdd-e-quando-ele-compensa]]
- [[testes-testes-de-contrato-e-testes-de-api]]