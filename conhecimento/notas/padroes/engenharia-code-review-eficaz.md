---
tags: [ceder, consistência, engenharia, individual, padrao, velocidade]
aliases: [Engenharia: code review eficaz]
date: 2026-08-23
---

# Engenharia: code review eficaz

**Fonte:** engenharia

Code review é a principal ferramenta para difundir conhecimento, reduzir bugs e manter consistência. Review eficaz é focado, rápido, construtivo e orientado a decisões — não a gosto pessoal.

### O que revisar (em ordem de impacto)
1. **Corretude e lógica**: o código faz o que os testes dizem? Cobre edge cases (vazio, nulo, limite, concorrência)?
2. **Segurança**: injeção, autenticação, validação de entrada, segredos, autorização por objeto.
3. **Complexidade**: existe jeito mais simples? Código difícil de entender é onde bugs se escondem.
4. **Testes**: cobrem a mudança? Testam o comportamento, não a implementação?
5. **Design e acoplamento**: a mudança respeita as fronteiras do sistema? Duplica conceito já existente?
6. **Legibilidade e estilo**: só no fim, e só se diferir do padrão acordado.

### Como escrever comentários eficazes
- **Crítica ao código, não à pessoa**: descreva o comportamento, sugira alternativa.
- **Porquê acima de o quê**: “por que este valor é 0.05?” é mais útil que “talvez 0.05 esteja errado”.
- **Seja específico**: cite linha e dê exemplo concreto de quando quebra.
- **Diferencie severidade**: bloqueante (bug/segurança) → pedido de melhoria → sugestão opcional. Use labels/emoji de severidade para o autor saber o que decidir.
- **Não force preferência**: “eu escreveria assim” não é requisito. Questione se a alternativa traz valor real.
- **Pergunte em vez de impor** quando for dúvida: “não entendi por que X; pode explicar?”

### Tamanho importa
- PRs < 200–300 linhas são revisados com muito mais profundidade; mudanças gigantes viram “LGTM” burocrático.
- **Split por intenção**: refactor isolado de feature; commits atômicos e revisáveis.
- Review em < 24h úteis mantém o fluxo; priorize interações pequenas e rápidas.

### Do lado do autor
- PR pequeno, com descrição do contexto, decisões e trade-offs.
- Explique a motivação: o que estava errado antes e por que esta é a solução.
- Responda comentários; peça o que faltar. Resolver discussão deve ser explícito.

**Cultura**: trate review como colaboração, não auditoria. O objetivo é código que o time inteiro entenda e sustente — a velocidade individual deve ceder à velocidade do time.
## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-documentação-que-não-vira-lixo-adr-readme-vivo-co]]
- [[engenharia-dívida-técnica-e-manutenibilidade]]
- [[engenharia-refactoring-seguro]]
- [[engenharia-requisitos-e-definição-de-escopo]]
- [[padrao-hub-padroes]]