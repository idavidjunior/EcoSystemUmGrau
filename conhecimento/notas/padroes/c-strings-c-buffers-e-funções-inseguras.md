---
tags: [c, cve, daí, memória, nasce, padrao]
aliases: [C: strings C, buffers e funções inseguras]
date: 2026-08-22
---

# C: strings C, buffers e funções inseguras

**Fonte:** c

Em C, `char*` não carrega tamanho: strings são sequências de bytes terminadas em `'\0'` (NUL). Toda operação precisa de contexto externo para saber quanto espaço há — e quase todo CVE de memória nasce daí. Funções da era clássica são armadilhas:

- `strcpy(dst, src)` copia até o NUL sem limite → overflow clássico. Prefira `strncpy`/`strlcpy`, mas `strncpy` NÃO garante terminação e preenche o resto com zeros.
- `strcat`/`sprintf` → mesma vulnerabilidade. Use `snprintf(dst, sizeof(dst), "...", ...)`, que sempre termina com NUL (se `sizeof > 0`) e retorna o tamanho que seria escrito.
- `gets` é removida do C11; usar é dar controle do programa.

`snprintf` retorna o número de caracteres que TERIAM sido escritos (sem NUL). Detectar truncamento: `if (n >= sizeof(dst)) /* truncou */`. `sizeof(dst)` só funciona para arrays de verdade, não para parâmetros (decaem para ponteiro) — passe o tamanho explicitamente.

Para entrada: `fgets(buf, sizeof(buf), stdin)` (mantém o `\n`) ou `getline` (POSIX, aloca dinamicamente). `strlen` em buffer não terminado lê fora dos limites → UB; sempre garantir terminação logo após qualquer cópia. `strtok` é não-reentrante (usa estado estático); use `strtok_r`/`strsep`. Funções locale-dependentes (`strtol` vs `strtoll`) confundem conversão numérica.

Idioma de cópia segura:

```c
char dst[64];
snprintf(dst, sizeof(dst), "%s:%d", host, port);
```

Regras: (1) definir e respeitar um tamanho máximo para cada buffer; (2) nunca confiar no compilador para checar limites — use anotações como `__attribute__((nonnull))`/`_FORTIFY_SOURCE`/`-D_FORTIFY_SOURCE=2`; (3) tratar truncamento como erro, não como sucesso silencioso; (4) considerar alternativas: `asprintf` (glibc/POSIX), ou usar C++ `std::string` quando performance de latência não for o fator. Use sanitizers e fuzzing (libFuzzer/AFL) — strings C são o principal alvo de entradas malformadas.
## Conexoes

- [[c-comportamento-indefinido-e-o-modelo-de-memória]]
- [[c-ponteiros-aritmética-e-gestão-manual-de-memória]]
- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]