---
tags: [arquitetura, batendo, clientes, instante, padrao, sincronizados]
aliases: [Arquitetura: resiliência — retry, circuit breaker, backoff e]
date: 2026-08-20
---

# Arquitetura: resiliência — retry, circuit breaker, backoff e idempotência

**Fonte:** arquitetura

Sistemas distribuídos falham: rede, timeouts, sobrecarga de dependentes. Resiliência é a disciplina de continuar útil diante de falhas de vizinhos.

**Retry**: repete uma chamada que falhou de forma transitória (timeout, 5xx, lock). Regras: retry **com backoff exponencial + jitter** — `attempt = base * 2^n` com aleatoriedade para evitar thundering herd (todos os clientes sincronizados batendo no mesmo recurso no mesmo instante). Limite o número de tentativas; retry em falhas 4xx é inútil (erro de cliente).

**Circuit breaker**: detecta dependente degradado e 'abre' o circuito — falha rápido sem esperar timeout, preservando threads e evitando cascata. Estados: fechado (normal) → aberto (falha rápido) → half-open (envia sonda para testar recuperação). Implemente com limiares de erro, janela de tempo e contadores deslizantes (bibliotecas: resilience4j, Polly, Hystrix). Sem circuit breaker, um recurso lento derruba toda a cadeia (cascading failure).

**Timeouts e budget**: todo call remoto precisa de timeout explícito; defina o timeout do cliente menor que o do servidor, e o do serviço A menor que o do B que ele chama. **Bulkhead**: isole pools de conexão por dependente — uma fila cheia não engole as demais. **Backpressure / load shedding**: descarte ou reduza trabalho (fail fast, degração de funcionalidade) antes de morrer.

**Idempotência**: a peça-chave — operações devem poder ser repetidas sem efeito duplicado. Chaves de idempotência (id único do request), `INSERT ... ON CONFLICT DO NOTHING`, versões de recurso (optimistic locking), bancos do consumidor armazenando mensagens já processadas. Idempotência + retry confiável substituem a necessidade de exatamente-uma-vez.

Padrão completo: retry (curto, com jitter) → circuit breaker → fallback/cache → cauda lenta (hedged requests). Simule falhas (chaos engineering: kill de dependência, injeção de latência) para provar o comportamento sob estresse.
## Conexoes

- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]