---
tags: [ambiente, desenvolvimento, justa, padrao, php, tolerante]
aliases: [PHP: modelo de execução e SAPI]
date: 2026-08-14
---

# PHP: modelo de execução e SAPI

**Fonte:** php

### Modelo de execução

O PHP é **stateless por requisição** (shared-nothing): cada request sobe do zero, executa e morre. Nenhuma variável sobrevive entre requests, a não ser via camadas externas (session files, APCu, Redis, banco). Isso elimina vazamentos persistentes, mas repete a inicialização a cada request — por isso o **OPcache** é obrigatório em produção (compila o bytecode uma vez e o reaproveita; sem ele, cada request recompila todos os arquivos).

### SAPIs principais

- **CLI (php-cli)**: script único, sem timeout de request, recebe argumentos via `$argv`/`$argc`; usado em cron, filas (Symfony Messenger, Laravel Queue) e comandos artisan/console.
- **PHP-FPM**: processo mestre + pool de workers que mantêm o interpretador vivo; cada request é atendido por um worker livre. Configuração em `php-fpm.conf` e `www.conf` (`pm.max_children`, `pm.start_servers`, `pm.max_requests`). É a opção recomendada com nginx.
- **mod_php (Apache)**: interpretador embutido no Apache; simples de configurar, porém consome um processo por conexão e não escala bem — legado.
- **CGI/FastCGI**: executável por request, sem reaproveitamento; em desuso frente ao FPM.

### Ciclo de vida

`php.ini` → `auto_prepend_file` → bootstrap do framework (autoload, providers/DI) → roteamento → controller → resposta → shutdown. Com FPM, o `index.php` é o único ponto de entrada; o nginx repassa a URI via variáveis FastCGI (`fastcgi_param SCRIPT_FILENAME ...`).

### Ajustes práticos

- Defina `memory_limit`, `max_execution_time` e `post_max_size` por ambiente (desenvolvimento tolerante, produção justa).
- `pm.max_requests` força o reciclo do worker a cada N requests, prevenindo vazamento de memória em código legado.
- Com PHP-FPM + nginx, quem entrega arquivos estáticos é o nginx; o FPM processa somente PHP — nunca use `sendfile` no FPM para conteúdo dinâmico.

```ini
; www.conf
pm = dynamic
pm.max_children = 50
pm.start_servers = 5
pm.max_requests = 500
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[php-psrs-autoload-e-composer]]
- [[php-sistema-de-tipos-arrays-e-coerção]]