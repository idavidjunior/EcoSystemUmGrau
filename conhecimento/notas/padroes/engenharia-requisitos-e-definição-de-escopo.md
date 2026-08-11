---
tags: [engenharia, espalhadas, estável, iteração, numa, padrao]
aliases: [Engenharia: requisitos e definição de escopo]
date: 2026-08-10
---

# Engenharia: requisitos e definição de escopo

**Fonte:** engenharia

Requisitos ruins geram retrabalho, bugs e escopo que cresce sem controle. O objetivo da engenharia de requisitos é transformar necessidades vagas em algo **testável, mensurável e negociado** antes de escrever código.

### Tipos de requisitos
- **Funcionais**: o que o sistema faz (o usuário pode cadastrar um produto).
- **Não funcionais**: como faz (performance < 200ms, disponibilidade 99.9%, segurança, acessibilidade, escalabilidade).
- **Restrições**: limites de plataforma, orçamento, prazos, compliance.
- **Regras de negócio**: políticas de domínio (idade mínima, limites de crédito) — devem viver no código de forma explícita, não espalhadas em `if`s.

### Como escrever um bom requisito (INVEST)
Cada requisito deve ser **I**ndependente, **N**egociável, **V**alioso, **E**stimável, **S**mall (pequeno o suficiente para caber numa iteração) e **T**estável. Escreva no formato de user story: *Como [persona], eu quero [capacidade] para [benefício]*. Critérios de aceite (Given/When/Then) tornam o requisito verificável:
```
Dado um carrinho com itens e usuário logado,
Quando o pagamento é aprovado,
Então o pedido é criado com status 'pago' e o estoque é decrementado.
```

### Definição de escopo
- **Identifique o problema** (não pule para a solução): pergunte *por quê* cinco vezes.
- **Diferencie escopo obrigatório, desejável e fora do escopo** — o terceiro grupo previne o gold-plating.
- **Decida explicitamente o que NÃO será feito** e registre (evita surpresas no review).
- Use o **Modelo Kano** para priorizar: features básicas (devem existir), de desempenho (quanto mais melhor) e encantadoras (surpreendem).

### Armadilhas
- Confundir requisito com solução de implementação (o *como* em vez do *o quê*).
- Requisitos ambíguos: “rápido”, “fácil”, “melhor” precisam de números.
- Não definir critérios de aceite → aceitação vira discussão.
- Escopo mudando sem revisão de impacto em custo e prazo (scope creep).

**Checklist**: cada requisito tem dono? É testável? Tem número quando aplicável? O fora-de-escopo está registrado? Critérios de aceite estão escritos antes do desenvolvimento? Se não, o backlog ainda é uma lista de desejos, não de requisitos.
## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-code-review-eficaz]]
- [[engenharia-documentação-que-não-vira-lixo-adr-readme-vivo-co]]
- [[engenharia-dívida-técnica-e-manutenibilidade]]
- [[engenharia-refactoring-seguro]]
- [[padrao-hub-padroes]]