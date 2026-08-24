---
tipo: padrao
tags: [projetos-irmaos, android, registro, conhecimento, supermarketcaculator, mp3player, bibliaestudocompleta]
data: 2026-08-09
contexto: Usuario pediu para aprender/memorizar os tres projetos irmaos registrados em conhecimento/projetos-irmaos.json
---

# Projetos irmaos do EcoSystemUmGrau

## Decisao

Registrar de forma consolidada o conhecimento sobre os tres projetos irmaos criados/auxiliados pelo ecossistema. Todos sao Android, vivem em `../` (PROJECT_PARENT) e foram catalogados em `conhecimento/projetos-irmaos.json`.

## Os tres projetos

### 1. SupermarketCalculator
- Tipo: android (Kotlin/Java)
- Status: funcional | versao v1.2
- Caminho: `../SupermarketCalculator`
- APK: `releases/SupermarketCalculator-v1.2.apk`
- Build: `build.ps1`
- Skill: `.opencode/skills/android-pure-sdk`
- Envolvimento: criado com auxilio do EcoSystemUmGrau (agentes, build, arquitetura)
- Tags: android, kotlin, calculator, shopping, budget
- Key files: AndroidManifest.xml, build.ps1, AGENTS.md, ARQUITETURA.md, METODOLOGIA.md, PLAYBOOK.md, opencode.json

### 2. Mp3Player
- Tipo: android
- Status: em_desenvolvimento | versao —
- Caminho: `../Mp3Player`
- Build: — (ainda nao definido)
- Envolvimento: criado com auxilio do EcoSystemUmGrau
- Tags: android, media, audio, music
- Key files: AndroidManifest.xml, build.gradle.kts, settings.gradle.kts, gradle.properties, gradlew.bat

### 3. BibliaEstudoCompleta
- Tipo: android
- Status: funcional | versao —
- Caminho: `../BibliaEstudoCompleta`
- Build: `build.ps1`
- Envolvimento: criado com auxilio do EcoSystemUmGrau (build, arquitetura, versionamento)
- Tags: android, bible, study, religious, audio
- Key files: AndroidManifest.xml, build.ps1, build.gradle.kts, settings.gradle.kts, gradle.properties, AGENTS.md, project.properties, version.properties, biblia-sagrada-app-source.zip

## Impacto

O Jarvis passa a conhecer os tres projetos irmaos para futuras referencias em conversa, builds, diagnostico ADB, sincronizacao e suporte. O registry oficial continua sendo `conhecimento/projetos-irmaos.json` (atualizado em 2026-08-01).

## Aprendizado

- Todo projeto irmao deve ser registrado em `projetos-irmaos.json` ao ser criado/auxiliado.
- O Jarvis consulta o registry antes de buscar arquivos/dados de projetos irmaos.
- Builds Android seguem `build.ps1` quando existir (SupermarketCalculator e BibliaEstudoCompleta); Mp3Player ainda sem script de build.

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[album-art-download-com-redirect-loop-manual-instancefollowre]]
- [[audioprocessorisactive-must-be-dynamic]]
- [[filename-artist-extraction-two-strategies]]
- [[itunes-search-with-scoring-thresholds]]
- [[metadata-busca-em-multi-fontes-acoustid-itunes-br-musicbrain]]
- [[renderersfactory-for-custom-audioprocessor]]
- [[searchmodenormal-relaxed-auto-fallback-se-normal-retorna-nul]]