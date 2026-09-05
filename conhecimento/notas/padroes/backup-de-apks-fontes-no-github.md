---
tags: [limpos, opencode, padrao, permitir, proj, trackeado]
aliases: [Backup de APKs + fontes no GitHub]
date: 2026-08-08
---

# Backup de APKs + fontes no GitHub

**Fonte:** opencode

## Contexto
Dos 11 apps em `Projetos/` (submódulos do EcoSystemUmGrau), 9 estavam limpos e 2
tinham trabalho não commitado: `SupermarketCalculator` (feature v1.5.0 de sons) e
`VoxUmGrau` (ajustes de áudio/chamada v17). Além disso, **nenhum APK era trackeado**
em nenhum projeto — `*.apk` estava no `.gitignore` do SupermarketCalculator, e o APK
do VoxUmGrau ficava em `app/build/` (ignorado). Ou seja: não havia backup dos APKs.

## Decisões e padrão estabelecido

### 1. Backup de APKs: pasta `releases/` versionada
- **SupermarketCalculator** (build com `build.ps1`, APKs release assinados):
  - `.gitignore` passou a ter a negação para permitir releases:
    ```
    *.apk
    !releases/
    !releases/*.apk
    ```
  - APK canônico de cada versão fica em `releases/SupermarketCalculator-vX.Y.Z.apk`
    (já existiam v1.2, v1.3.0, v1.4.0; adicionado v1.5.0).
  - Duplicatas da raiz (ex.: `...-release.apk`) e APKs debug foram movidos para
    `build/` (área de artefatos gitignored) — raiz do proj
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]