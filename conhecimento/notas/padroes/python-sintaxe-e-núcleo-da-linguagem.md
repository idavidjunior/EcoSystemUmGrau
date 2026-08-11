---
tags: [despacho, else, estrutura, padrao, python, tipo]
aliases: [Python: sintaxe e núcleo da linguagem]
date: 2026-08-10
---

# Python: sintaxe e núcleo da linguagem

**Fonte:** python

Python é uma linguagem dinamicamente tipada e interpretada, com foco em legibilidade (PEP 20). Blocos são delimitados por indentação (4 espaços, nunca misturar com tabs). A função `print` exige parênteses desde a 3.x; `print()` é uma chamada de função, não uma statement.

Conceitos centrais: variáveis são referências a objetos, não caixas — `a = []` e `b = a` apontam para a MESMA lista. O operador `is` compara identidade (endereço do objeto), `==` compara valor via `__eq__`. Python usa **call-by-sharing**: objetos imutáveis (int, str, tuple, frozenset) se comportam como passagem por valor; mutáveis (list, dict, set) são passados por referência, mas a reatribuição `x = ...` dentro de uma função não afeta o chamador.

Mecânica central: `if __name__ == '__main__':` separa execução direta de importação. Compreensões (`[x**2 for x in r if x % 2]`) e geradores (`(x for x in r)`) são preferidos a loops com `append`. `range` é lazy e deve ser usado em vez de listas explícitas em `for`.

Armadilhas comuns:
- Mutable default argument: `def f(a=[])` compartilha a mesma lista entre chamadas — use `def f(a=None)` e inicialize com `a = [] if a is None else a`.
- `int` é de precisão arbitrária (sem overflow); use `sys.set_int_max_str_digits` apenas para conversões extremas.
- `==` com floats exige `math.isclose`, nunca comparação direta.
- Fatiamento copia a sequência: `s[::-1]` inverte (string, list, tuple). Slicing em memória não copia o buffer subjacente para bytes/arrays grandes.
- Escopo de loops: `for` NÃO cria escopo local; variáveis do loop vazam para o escopo externo.

Melhores práticas: use f-strings em vez de `%` e `.format()`. Prefira `pathlib.Path` a `os.path`. Use `*args`/`**kwargs` apenas para delegação. Nomeie com snake_case. Em Python 3.10+, `match` (structural pattern matching) substitui cadeias longas de `if/elif` em despacho por tipo/estrutura.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[python-decoradores-e-metaprogramação]]
- [[python-gil-e-concorrência]]
- [[python-idioms-e-boas-práticas]]