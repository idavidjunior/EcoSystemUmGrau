---
tags: [checkout, designpatterns, fakes, finas, padrao, simples]
aliases: [Design patterns: estruturais — adapter, facade e decorator]
date: 2026-08-22
---

# Design patterns: estruturais — adapter, facade e decorator

**Fonte:** designpatterns

Padrões estruturais compõem classes e objetos para formar estruturas maiores sem acoplar as partes.

**Adapter**: converte a interface de uma classe em outra esperada pelo cliente (`LegacyPaymentAPI` → interface `GatewayPagamento` esperada pelo domínio). É o mediador entre interfaces incompatíveis — sem alterar o código legado. Use em integrações, bibliotecas de terceiros e testes (fake adapter). O domínio define a interface (port); o adapter traduz. Cuidado: adapter fino demais é ideal — camadas de tradução grossas viram código 'copia e cola' difícil de manter.

**Facade**: fornece interface única e simplificada sobre um subsistema complexo (`PedidoFacade` chamando estoque, pagamento, email em uma chamada `checkout()`). Reduz acoplamento: o cliente conversa com a facade, não com 12 classes internas. Usado para API pública, integração de bibliotecas complexas e módulos legados. Diferença do adapter: facade simplifica *um subsistema inteiro*, adapter ajusta *duas interfaces*.

**Decorator**: adiciona comportamento a um objeto dinamicamente, envolvendo-o e delegando — respeitando a mesma interface (composição em vez de herança). Ex.: `Compressao`, `Logging`, `Caching`, `CircuitBreaker` ao redor de `HttpClient` ou de um stream de dados. Permite empilhar responsabilidades em qualquer ordem em runtime, sem tocar na classe original. Cuidado com a explosão de camadas e com a ordem (a ordem importa — compressão antes de criptografia é diferente). Distinga de proxy: proxy controla *acesso*/ciclo de vida; decorator adiciona *comportamento*.

Quando usar: adapter para interoperar, facade para simplificar a borda do sistema, decorator para estender responsabilidade sem herança profunda. Os três são composição em favor de acoplamento direto e são pré-requisitos para testabilidade (interfaces finas, fakes simples).
## Conexoes

- [[cluster-hub-programacao]]
- [[design-patterns-anti-patterns-comuns-god-object-service-loca]]
- [[design-patterns-comportamentais-strategy-observer-template-m]]
- [[design-patterns-creacionais-factory-builder-e-por-que-single]]
- [[design-patterns-solid-e-como-os-padrões-gof-derivam-dele]]
- [[padrao-hub-padroes]]