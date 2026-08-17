---
tags: [coupling, designpatterns, frágil, herança, padrao, profunda]
aliases: [Design patterns: anti-patterns comuns — god object, service ]
date: 2026-08-17
---

# Design patterns: anti-patterns comuns — god object, service locator e spaghetti

**Fonte:** designpatterns

Anti-patterns são soluções recorrentes que parecem resolver um problema mas criam dívida de longo prazo. Reconhecê-los é tão valioso quanto conhecer os GoF.

**God Object**: uma classe que faz de tudo — domínio, I/O, UI, orquestração (ex.: `Utils`, `Manager`, `Controller` de 3000 linhas). Sintomas: dezenas de dependências, todos os métodos públicos usados 'por fora', dificuldade de testar, qualquer mudança quebra o resto. Causa raiz: SRP ignorado. Tratamento: identificar responsabilidades e extrair (extract class) em serviços de domínio, repositórios e casos de uso; quebrar em fatias pequenas; usar facade apenas na borda, nunca como recipiente de tudo.

**Service Locator**: um registro global devolve dependências sob demanda (`ServiceLocator.get(Pagamento.class)`) no lugar de injeção. É um singleton disfarçado e o mesmo code smell: dependências ocultas (o código parece sem dependência, mas explode em runtime), teste difícil e acoplamento a um concreto global. Tratamento: substitua por injeção de dependência explícita via construtor — o compositioon root cria tudo; as classes declaram o que precisam. Raras exceções: frameworks/plugins com extensão dinâmica.

**Spaghetti**: fluxo de controle emaranhado — gotos, estados globais, código sequencial gigante sem estrutura, responsabilidades misturadas (validação, banco e regra na mesma função). Sintoma de arquitetura ausente. Tratamento: refatoração estruturada — dividir em funções puras, introduzir camadas, aplicar strategy/state para condicionais e polimorfismo para switches de tipo.

Outros a conhecer: **Copy-Paste Programming**, **Golden Hammer** (usar a mesma tecnologia/pattern para tudo), **Lava Layer** (código morto acumulado), **Temporal coupling**, **Yo-Yo class** (herança profunda e frágil).

Detecção automatizada: métricas (complexidade ciclomática, acoplamento aferente/efetivo, tamanho de método), code review com foco em 'onde está a regra de negócio?', testes que obrigam a desacoplar. Regra: se você precisa ler 500 linhas para entender uma mudança, é anti-pattern.
## Conexoes

- [[cluster-hub-programacao]]
- [[design-patterns-comportamentais-strategy-observer-template-m]]
- [[design-patterns-creacionais-factory-builder-e-por-que-single]]
- [[design-patterns-estruturais-adapter-facade-e-decorator]]
- [[design-patterns-solid-e-como-os-padrões-gof-derivam-dele]]
- [[padrao-hub-padroes]]