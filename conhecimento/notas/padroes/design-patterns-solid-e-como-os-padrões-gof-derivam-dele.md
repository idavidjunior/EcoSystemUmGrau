---
tags: [baseados, designpatterns, editar, existente, padrao, passos]
aliases: [Design patterns: SOLID e como os padrões GoF derivam dele]
date: 2026-08-17
---

# Design patterns: SOLID e como os padrões GoF derivam dele

**Fonte:** designpatterns

SOLID é o conjunto de princípios que orienta *por que* os patterns existem. Entender a origem torna a escolha de padrão um exercício de consequência, não de decoreba.

- **S — Single Responsibility (SRP)**: cada classe tem um único motivo para mudar. É a origem dos patterns que separam responsabilidades: Decorator separa comportamento transversal, Strategy separa variação de algoritmo, Template Method separa passos.
- **O — Open/Closed (OCP)**: aberto para extensão, fechado para modificação. Strategy, Decorator, Factory Method e Observer existem para adicionar comportamento novo sem editar o existente (composição, polimorfismo).
- **L — Liskov Substitution (LSP)**: subtipos devem ser substituíveis pelo base sem quebrar contrato. É o que torna o polimorfismo seguro; violações clássicas (subclasse que lança exceção nova, que altera invariantes) quebram todos os patterns baseados em interfaces.
- **I — Interface Segregation (ISP)**: clientes não devem depender de interfaces que não usam — interfaces finas e específicas. Adapter e Facade nascem disso: traduzir/expor exatamente o que o cliente precisa.
- **D — Dependency Inversion (DIP)**: módulos de alto nível não dependem de módulos de baixo nível; ambos dependem de abstrações; abstrações não dependem de detalhes. É a fundação de Adapter, Factory e da arquitetura hexagonal/clean: o domínio declara ports; infraestrutura implementa.

A leitura correta: *padrões são as formas canônicas de aplicar SOLID em casos recorrentes*. Ex.: a necessidade de trocar implementação em runtime = Strategy + OCP; a necessidade de injetar abstração sobre serviço externo = Adapter + DIP; composição de responsabilidades = Decorator + SRP.

Aplicando: quando uma mudança de requisito chega, pergunte qual princípio está sendo violado — a resposta sugere o pattern. SOLID não é checklist para medir 'código bom'; é linguagem para raciocinar sobre acoplamento e pontos de mudança.
## Conexoes

- [[cluster-hub-programacao]]
- [[design-patterns-anti-patterns-comuns-god-object-service-loca]]
- [[design-patterns-comportamentais-strategy-observer-template-m]]
- [[design-patterns-creacionais-factory-builder-e-por-que-single]]
- [[design-patterns-estruturais-adapter-facade-e-decorator]]
- [[padrao-hub-padroes]]