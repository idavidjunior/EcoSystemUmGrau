---
tags: [clareza, código, intenção, lambda, padrao, python]
aliases: [Python: idioms e boas práticas]
date: 2026-08-17
---

# Python: idioms e boas práticas

**Fonte:** python

Escrever Python idiomático é usar os recursos da linguagem para expressar intenção com menos código e mais clareza. PEP 8 (estilo), PEP 20 (Zen) e The Zen of Python guiam as decisões.

Idioms centrais:
- EAFP (Easier to Ask Forgiveness than Permission): envolva em `try/except` em vez de pré-checar (`if hasattr(...)`) — é mais rápido quando o erro é raro e evita corridas.
- Desempacotamento: `a, b = b, a` troca valores; `first, *rest = seq`; `for idx, v in enumerate(seq)`; `for k, v in dict.items()`.
- `any()`/`all()` com gerador substituem loops de verificação: `any(x > 10 for x in data)`.
- `dict.get(k, default)`, `dict.setdefault`, `collections.defaultdict` e `collections.Counter` substituem o padrão `if k not in d: d[k] = ...`.
- Context managers (`with open(...) as f`) garantem release de recursos mesmo em exceção. `contextlib.contextmanager` cria gerenciadores sob medida.
- `@dataclass` (3.7+) substitui classes boilerplate de dados; `@property` controla acesso; enums via `enum.Enum`.
- `functools.lru_cache` memoiza funções puras com zero esforço.
- `zip(a, b)` itera em paralelo; `itertools` (chain, groupby, product) evita loops aninhados.

Armadilhas comuns:
- Listas como default de parâmetro e como valor em `defaultdict` (a mesma instância é compartilhada) — use `lambda: []`.
- `*args` captura posicionais, `**kwargs` nomeados; esquecer `**` ao despachar causa erro sutil.
- `str.strip()` remove espaços das pontas — não usar para substring.
- Comparar com `is None` (não `== None`); evite `is` com números/strings (podem ser internados, mas é detalhe de implementação).

Melhores práticas: nomeie funções com verbos e variáveis com substantivos. Prefira funções puras. Type hints (`def f(x: int) -> str`) melhoram legibilidade e permitem mypy. Organize imports (stdlib, terceiros, locais) em ordem. Evite cadeias de `isinstance` para despacho — use dunder methods ou polimorfismo. `logging` em vez de `print` em aplicações; `__main__` só para scripts de verdade. Pequenas funções: uma responsabilidade, teste fácil.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[python-decoradores-e-metaprogramação]]
- [[python-gil-e-concorrência]]
- [[python-sintaxe-e-núcleo-da-linguagem]]