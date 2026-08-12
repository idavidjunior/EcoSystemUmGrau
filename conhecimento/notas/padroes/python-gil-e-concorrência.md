---
tags: [criação, inúteis, name, padrao, processes, python]
aliases: [Python: GIL e concorrência]
date: 2026-08-11
---

# Python: GIL e concorrência

**Fonte:** python

O GIL (Global Interpreter Lock) permite que apenas uma thread execute bytecode Python por vez, tornando threads inúteis para paralelismo de CPU. Concorrência real se consegue com multiprocessing (ProcessPoolExecutor) ou com I/O assíncrono (asyncio).

Escolha correta:
- **CPU-bound** (cálculo pesado): multiprocessing — cada processo tem GIL próprio e ganha paralelismo real; pague o custo de serialização dos argumentos (pickle) e overhead de fork/spawn.
- **I/O-bound** (rede, arquivos, banco): asyncio ou threads — enquanto uma corrotina/thread espera I/O, outra progride. O GIL é liberado durante syscalls de I/O, então threads funcionam bem para I/O bound.

asyncio: `async def` cria corrotinas; `await` cede o controle ao event loop. `asyncio.gather` (paralelo) vs `asyncio.create_task` (despachar sem esperar). Não bloqueie o loop com código síncrono pesado dentro de uma corrotina — use `asyncio.to_thread` para delegar. Execução precisa de um loop: `asyncio.run(main())` a partir do Python 3.7.

Threads: `ThreadPoolExecutor` é a API moderna sobre `threading` puro. Para estado compartilhado, use `threading.Lock` (com `with lock:`), `Queue` ou variáveis atômicas — nunca conte com `+=` ser atômico (não é).

Armadilhas:
- Processos NÃO compartilham memória; para compartilhar use `multiprocessing.Queue`, `Pipe`, `shared_memory` ou arrays/maps do módulo `multiprocessing.sharedctypes`.
- No Windows, `multiprocessing` usa 'spawn' — o código do módulo é re-importado no filho, então proteja a criação de processes dentro de `if __name__ == '__main__':`.
- `asyncio.wait_for` cancela corrotinas; atenção a `CancelledError`.
- Deadlock: lock sem timeout, ou chamar `loop.run_until_complete` dentro de corrotina.

Melhores práticas: medir antes de otimizar — se o gargalo for CPU, primeiro melhore o algoritmo. `concurrent.futures` unifica ThreadPool/ProcessPool com a mesma API. Para concorrência massiva de rede, asyncio com cliente não bloqueante (aiohttp, httpx) supera threads em recursos.
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[python-decoradores-e-metaprogramação]]
- [[python-idioms-e-boas-práticas]]
- [[python-sintaxe-e-núcleo-da-linguagem]]