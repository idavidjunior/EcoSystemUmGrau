---
tipo: padrao
tags: [apk, backup, github, submodules, gitignore, release, android]
data: 2026-08-08
contexto: Usuário pediu que os apps APK (código-fonte + APKs) fossem atualizados e commitados no GitHub como backup, no lugar correto do Ecossistema, sem gerar bagunça/lixo
decisao: Padronizar backup de APKs em `releases/` dentro de cada projeto (trackeados), ignorar artefatos de build, e manter os gitlinks dos submódulos atualizados no pai
impacto: Todos os apps em `Projetos/` agora têm fonte + APK de release versionados no GitHub; builds intermediários e logs não poluem o repo
---

# Backup de APKs + fontes no GitHub

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
    `build/` (área de artefatos gitignored) — raiz do projeto ficou limpa.
- **VoxUmGrau** (build só gera `assembleDebug`, sem setup de release):
  - Backup do APK debug versionado em `releases/VoxUmGrau-v<buildCount>-debug.apk`.
  - Logs de build (`build_latest.txt`, `build_log*.txt`, `build_out.txt`) passaram a
    ser ignorados via `build_*.txt` no `.gitignore` — eram lixo não versionado.

### 2. Artefatos que NÃO entram no git
- `build/`, `app/build/`, `.gradle/` (outputs intermediários, ex.: `-aligned`/`-unsigned`).
- APKs debug espalhados na raiz.
- Logs de build (`build_*.txt`, `*.log`).

### 3. Estrutura no Ecossistema (submódulos)
- Cada app vive em `Projetos/<App>` como clone git próprio com remote GitHub
  (`idavidjunior/<App>`); o pai `EcoSystemUmGrau` guarda apenas **gitlinks** (SHA)
  no índice — os submódulos estão registrados no `.gitmodules` mas não inicializados
  (prefixo `-` no `submodule status`), o que é o estado normal aqui.
- Após commitar dentro de um submódulo, o gitlink no pai precisa ser atualizado:
  `git add Projetos/<App> && git commit`.
- **Atenção**: o auto-commit do opencode (`[auto] EcoSystemUmGrau - HH:MM`) já atualiza
  gitlinks de submódulos cujo trabalho foi commitado antes dele rodar — pode sobrar
  só um gitlink stale para atualizar manualmente (foi o caso do VoxUmGrau).
- Ao commitar o pai, **não** usar `git add -A` se houver dezenas de arquivos de
  conhecimento modificados por processos do ecossistema (vigilante/LER): commitar
  apenas o caminho do submódulo.

## Verificação
- `SupermarketCalculator`: commit `7e62a61` (15 arquivos, 6 WAVs + 3 APKs release) → push OK.
- `VoxUmGrau`: commit `eacf8ba` (8 arquivos, 4 Kotlin + APK v17) → push OK.
- Pai: gitlink do VoxUmGrau atualizado (`6cdd6744`) → push OK.
- `git status -sb` de ambos os apps: `## master...origin/master` (limpos e sincronizados).

## Lições
- Se quiser APK de backup versionado, a regra do `.gitignore` precisa de negação
  (`!releases/` + `!releases/*.apk`) — `*.apk` genérico mata o backup silenciosamente.
- Backup de APK deve ser o **artefato canônico** (release assinado ou, no mínimo, o
  mesmo APK que o `build.ps1` gera), nunca duplicatas soltas na raiz.
- Rodar `build.ps1` do VoxUmGrau faz auto-bump de `version.properties`/`build.gradle.kts`
  (versionCode++); o commit deve incluir esses arquivos junto com o APK.
