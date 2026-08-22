---
tags: [definidos, devem, hash, juntos, padrao, python]
aliases: [Python: decoradores e metaprogramação]
date: 2026-08-22
---

# Python: decoradores e metaprogramação

**Fonte:** python

Decoradores são funções que recebem outra função/classe e retornam uma versão modificada. Sintaxe `@decorator` acima de `def` é açúcar sintático para `f = decorator(f)`. Com argumentos, precisam de uma camada extra: `@deco(args)` equivale a `f = deco(args)(f)`.

Estrutura essencial:
```python
from functools import wraps

def timer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        r = fn(*args, **kwargs)
        return r
    return wrapper
```
`@wraps` copia `__name__`, `__doc__`, `__wrapped__` para o wrapper — sem ele, introspection e stack traces quebram.

Classe como decorator: implemente `__call__` para estado mutável (contadores, cache). `functools.lru_cache` e `functools.singledispatch` são decoradores do stdlib. `singledispatch` faz sobrecarga por tipo do primeiro argumento — alternativa limpa a `isinstance` em cascata.

Metaprogramação: `__getattr__` intercepta atributos inexistentes (proxies, lazy loading); `__getattribute__` intercepta TODOS os acessos (cuidado com recursão infinita — use `object.__getattribute__(self, name)`). `__setattr__` e `__delattr__` controlam escrita. `property` cria atributos calculados. `__slots__` reduz memória impedindo `__dict__` por instância (mas trava atributos dinâmicos).

Metaclasses (`type.__new__`) e `__init_subclass__` interceptam a CRIação de classes — usados por ORMs e frameworks para registrar subclasses automaticamente. `__init_subclass__` é mais simples e preferível para a maioria dos casos.

Armadilhas:
- Decorar sem `@wraps` quebra docstrings e `inspect.signature`.
- Ordem importa: o decorator mais próximo da função roda primeiro na aplicação (embaixo para cima); a composição acontece de fora para dentro.
- `@property` + setter/delete requerem o mesmo nome e uso de `@x.setter`.
- Metaclasses quebram herança múltipla com conflito de `type` — quase sempre há alternativa (hooks, `__init_subclass__`).

Melhores práticas: decoradores para cross-cutting (logging, cache, auth, retry, timing); não para lógica de negócio. Documente o contrato. Prefira composição e `__init_subclass__` a metaclasses. No Python 3.9+, decoradores aceitam qualquer expressão, inclusive `lambda`.

Dunder aliás: `__enter__`/`__exit__` (with), `__iter__`/`__next__` (iteração), `__len__`, `__getitem__`/`__setitem__` (subscript), `__call__` (callable), `__eq__`/`__hash__` (devem ser definidos juntos).
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[python-gil-e-concorrência]]
- [[python-idioms-e-boas-práticas]]
- [[python-sintaxe-e-núcleo-da-linguagem]]