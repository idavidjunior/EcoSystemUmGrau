---
tags: [cobram, engenharia, exceção, futuro, padrao, proxy]
aliases: [Engenharia: dívida técnica e manutenibilidade]
date: 2026-08-21
---

# Engenharia: dívida técnica e manutenibilidade

**Fonte:** engenharia

Dívida técnica é o custo implícito de escolhas de implementação que privilegiam velocidade no presente e cobram juros no futuro: bugs que reaparecem, mudanças lentas, onboarding caro. A metáfora (Ward Cunningham) é precisa: como dívida financeira, é aceitável quando **consciente e com plano de pagamento**; destrutiva quando se acumula sem juros contabilizados.

### Tipos
- **Dívida deliberada e intencional**: atalho tomado de olhos abertos, com ticket registrado e dono.
- **Dívida acidental**: efeito de má arquitetura, falta de padrões, tecnologia obsoleta — precisa de tratamento, não só de anotação.
- **Dívida incurável**: código morto, legado sem testes que ninguém entende.

### Indicadores de manutenibilidade (mire em números, não em intuição)
- **Complexidade ciclomática** por função (ideal ≤ 10): quantos caminhos de decisão existem.
- **Acoplamento e coesão**: classes com muitas responsabilidades e muitas dependências quebram a cadeia.
- **Cobertura de testes** nas regiões críticas e **tempo para mudar uma feature** (lead time) como proxy de manutenibilidade.
- **Taxa de bugs recorrentes** no mesmo módulo: sinal de dívida localizada.

### Como gerenciar
1. **Torne a dívida visível**: todo hack/atalho deve carregar comentário `// TODO(dívida): ...` ou ticket vinculado — invisível é permanente.
2. **Contabilize juros**: não basta listar; estime o custo de não pagar (tempo extra por mudança, bugs).
3. **Pague de forma incremental**: nunca faça “big bang” de reescrita. Dedique uma fatia contínua (ex.: 10–20% do sprint) para dívida, ou inclua o pagamento junto de toda feature que tocar o código.
4. **Boy Scout Rule**: deixe o código um pouco melhor do que encontrou (renomeie, extraia, adicione teste) em cada toque.
5. **Dívida de teste é a mais cara**: código sem testes não pode ser refatorado com segurança e acelera a decadência.

### Prevenção
- Standards de código, arquitetura em camadas, design patterns explícitos e revisão constante.
- **4ª Lei de Lehman**: sistemas que mudam continuamente tendem ao aumento de entropia — manutenção constante é lei, não exceção.

**Decisão prática**: dívida só é problema quando é invisível ou impagável. Todo atalho vira débito contábil: registre, dê dono, estimativa de juros e uma data de pagamento — senão vira legacy.
## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-code-review-eficaz]]
- [[engenharia-documentação-que-não-vira-lixo-adr-readme-vivo-co]]
- [[engenharia-refactoring-seguro]]
- [[engenharia-requisitos-e-definição-de-escopo]]
- [[padrao-hub-padroes]]