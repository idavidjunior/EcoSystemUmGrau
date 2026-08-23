---
tags: [artisan, comandos, instalação, migrate, padrao, php]
aliases: [PHP: PSRs, autoload e Composer]
date: 2026-08-23
---

# PHP: PSRs, autoload e Composer

**Fonte:** php

### Composer

Composer é o gerenciador de dependências do PHP. `composer.json` declara dependências e scripts; `composer.lock` fixa as versões exatas — **commite o lock** e rode `composer install` (não `update`) em produção. Restrições de versão seguem semver: `^1.2` (>=1.2 e <2.0), `~1.2` (>=1.2 e <1.3), `*`. Em produção use `composer install --no-dev --optimize-autoloader --classmap-authoritative` para maximizar performance do autoload.

### Autoload

Sem `require` manual: `composer dump-autoload` gera `vendor/autoload.php`, incluído uma única vez no bootstrap. Padrões:

- **PSR-4**: namespace → diretório. O mapeamento `"App\\": "src/"` resolve `App\Controllers\UserController` para `src/Controllers/UserController.php`. É o padrão dos frameworks atuais.
- **PSR-0** (legado): underscore `_` vira `/`; obsoleto.
- **classmap**: lista classes pré-escaneadas, mais rápido, mas exige re-gerar o dump ao adicionar classes.

### PSRs que importam

- **PSR-1/PSR-12**: padrões de estilo (classes StudlyCase, métodos camelCase, 4 espaços; PSR-12 atualizou o PSR-2).
- **PSR-4**: autoload moderno.
- **PSR-7**: interfaces de mensagens HTTP (`ServerRequestInterface`, `ResponseInterface`); base dos middlewares PSR-15 e dos clientes HTTP PSR-18.
- **PSR-11**: container de DI (interface `get($id)`).
- **PSR-3**: logging (`LoggerInterface`: `log()`, `info()`, `error()`).

### Fluxo típico

`composer require symfony/console` baixa o pacote para `vendor/`, registra o autoloader e as classes ficam disponíveis via `use`. Scripts de ciclo de vida (`post-install-cmd`, `post-update-cmd`) executam comandos como `php artisan migrate` após a instalação.

```json
{
  "require": { "php": ">=8.1", "monolog/monolog": "^3.0" },
  "autoload": { "psr-4": { "App\\": "src/" } }
}
```
## Conexoes

- [[cluster-hub-programacao]]
- [[padrao-hub-padroes]]
- [[php-modelo-de-execução-e-sapi]]
- [[php-sistema-de-tipos-arrays-e-coerção]]