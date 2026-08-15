---
tags: [asserções, chamado, padrao, posteriores, testes, valida]
aliases: [Testes: mocks, fakes e stubs (e quando evitar mockar)]
date: 2026-08-15
---

# Testes: mocks, fakes e stubs (e quando evitar mockar)

**Fonte:** testes

**Test doubles** são substitutos de dependências. A nomenclatura importa porque define a intenção: **dummy** (objeto passado mas nunca usado), **stub** (retorna respostas prontas para inputs pré-programados — define dados, não comportamento), **spy** (registra como foi chamado para asserções posteriores), **mock** (valida interação: espera chamadas específicas com argumentos específicos e falha se não acontecerem) e **fake** (implementação funcional leve e real: banco em memória, servidor HTTP de teste). **Usos corretos:** stub para forçar caminhos de erro e bordas que seriam caros/impossíveis com a dependência real; mock para validar interação com bordas externas sem estado (enviar email, publicar evento, chamar API de terceiro); fake para lógica interna que se comporta como a real. **Regra de ouro:** não mocke o que você não possui. Se a dependência é interna (seu repositório, sua classe de domínio), prefira o objeto real ou um fake; mockar 'por garantia' acopla o teste à implementação e quebra em qualquer refactor inocente. **Quando evitar mockar:** (1) ao testar comportamento, use valores reais em vez de verificar interações; (2) mocks excessivos de frameworks com sintaxe complexa geram testes que só provam que o mock funciona; (3) mockar classes concretas do seu domínio esconde bugs reais. Prefira **interfaces enxutas** e **injeção de dependência** para facilitar a substituição. **Regra de teste:** verifique o estado (resultado) sempre que possível; verifique interação apenas quando o efeito é justamente a chamada (side effect externo). Use ferramentas como Mockito, Jest, Moq ou WireMock de forma disciplinada: cada mock é um sinal de que a borda deveria ser real ou de que a arquitetura tem acoplamento demais.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[testes-cobertura-de-código-como-métrica-o-que-ela-mostra-e-o]]
- [[testes-pirâmide-de-testes-e-o-que-testar-em-cada-camada]]
- [[testes-tdd-e-quando-ele-compensa]]
- [[testes-testes-de-contrato-e-testes-de-api]]