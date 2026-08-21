---
tags: [bugs, compatíveis, git, nativa, padrao, trás]
aliases: [Git: conventional commits e versionamento semântico]
date: 2026-08-21
---

# Git: conventional commits e versionamento semântico

**Fonte:** git

**Conventional Commits** padroniza a mensagem de commit: `tipo(escopo): descrição`. Tipos principais: `feat` (nova funcionalidade), `fix` (correção de bug), `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Modificadores: `BREAKING CHANGE` (no corpo ou `!` após o tipo: `feat!:` ou `fix!:`). **Valor:** leitura rápida do que o PR faz, geração automática de changelog, ativação automática de release e gating de CI (sem `feat`/`fix` não publica), e integração nativa com **SemVer**. **Versionamento Semântico (SemVer)** usa `MAJOR.MINOR.PATCH`: **MAJOR** muda com breaking changes (API incompatível), **MINOR** adiciona funcionalidade compatível com versões anteriores (API ampliada, depreciações), **PATCH** corrige bugs compatíveis para trás. Correlação direta: `feat` → MINOR, `fix` → PATCH, `BREAKING CHANGE` → MAJOR. **Boas práticas:** (1) mensagem em imperativo e no corpo explique *por quê* e *como* (o 'o quê' o diff já mostra); (2) referencie issues/tickets no corpo (`Closes #42`); (3) regra do `1 commit = 1 mudança lógica`; (4) use `git log --oneline` e `--grep` para navegar; (5) squashed merges com a convenção no PR. **Ferramentas:** commitlint/husky (validação), standard-version/release-please/semantic-release (release automática a partir dos commits), changelog gerado. **Armadilhas:** breaking change anunciada só na descrição mas sem bump de MAJOR; `fix` que muda contrato de retorno (é breaking!); usar `chore` como 'coringa' para tudo — esconder `feat` de gerador de changelog; releases manuais fora da semântica. **Regra de ouro:** convenção + SemVer só valem se aplicadas consistentemente — defina no repo, valide em CI e gere release/versão de forma automatizada a partir dela.
## Conexoes

- [[cluster-hub-programacao]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]
- [[padrao-hub-padroes]]