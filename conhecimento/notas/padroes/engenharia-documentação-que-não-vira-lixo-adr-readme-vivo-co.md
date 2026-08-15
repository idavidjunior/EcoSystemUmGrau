---
tags: [ativo, engenharia, fonte, padrao, review, time]
aliases: [Engenharia: documentação que não vira lixo (ADR, README vivo]
date: 2026-08-15
---

# Engenharia: documentação que não vira lixo (ADR, README vivo, comentários que explicam o porquê)

**Fonte:** engenharia

Documentação morre quando descreve *o quê* o código já conta sozinho. Sobrevive quando registra *o porquê* — contexto, decisões e intenções — que nenhuma leitura de código revela. O princípio orientador: **documente a decisão, não o resultado**.

### ADR (Architecture Decision Records)
Um ADR registra uma decisão de arquitetura, seu contexto e suas consequências, em formato curto e versionado junto ao código:
```markdown
# ADR-007: Cache com Redis em vez de memória local

## Contexto
Bursts de tráfego e múltiplas instâncias exigem cache compartilhado; memória local duplicaria estado entre nós.

## Decisão
Usar Redis com TTL de 5min e cache-aside (read-through).

## Alternativas consideradas
- Cache local (Guava/Caffeine): descartado por não ser compartilhado entre instâncias.
- Varnish/CDN: fora de escopo, o conteúdo é dinâmico e autenticado.

## Consequências
+ Escala horizontal simples; − +1 infraestrutura para operar; falhas do Redis degradam para banco.
```
O valor real do ADR está nas **alternativas descartadas e no porquê** — evita rediscutir a mesma decisão a cada review e é a memória do time.

### README vivo
README não é manual de comandos congelado; é a porta de entrada do projeto, e deve permanecer verdadeiro:
- **Quick start reproduzível**: um comando (ou script) que roda o projeto, sem passos mágicos.
- **Architecture summary**: 1 diagrama ou descrição de camadas e fluxo principal.
- **How to contribute / código de conduta** mínimo.
- **Regra prática**: se o passo para rodar precisa de mais de 3 comandos, está na hora de automatizar com um script; se um comando dos docs está errado, a CI deve detectar ou o comando deve ser idempotente.

### Comentários que explicam o porquê
Comentário útil responde **por quê**, **para quê** ou **por que não**:
```python
# IMPORTANTE: não troque para os.getenv direto aqui.
# Este módulo roda fora do ambiente da app (workers), onde o .env não é carregado.
DB_URL = config_loader(environ_override=True)
```
- Comentário que repete o código (`# soma a e b`) é ruído — delete.
- `TODO` deve ter contexto (ticket ou risco); `// TODO: fix` sozinho é lixo.
- Documente pré-condições, invariantes e edge cases sutis que a leitura não revela.
- **Documentação de API**: gerada do código (docstrings com exemplos) evita divergência.

**Regra final**: se a documentação não ajuda ninguém a tomar uma decisão ou rodar o sistema, ela é débito, não ativo. Prefira 10 linhas de *porquê* a 100 linhas de *como* que o código já mostra.
## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-code-review-eficaz]]
- [[engenharia-dívida-técnica-e-manutenibilidade]]
- [[engenharia-refactoring-seguro]]
- [[engenharia-requisitos-e-definição-de-escopo]]
- [[padrao-hub-padroes]]