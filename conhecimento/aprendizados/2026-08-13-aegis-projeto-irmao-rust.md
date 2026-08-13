---
tipo: padrao
tags: [projetos-irmaos, rust, aegis, registro, git, seguranca]
data: 2026-08-13
contexto: Usuario pediu para criar o repositorio git do Aegis no local correto do ecossistema e registrar o projeto
---

# Aegis registrado como projeto irmao (Rust)

## Decisao

O Aegis foi movido de `Default Project\Projetos\aegis` para `EcoSystemUmGrau\Projetos\aegis`, o local correto onde vivem os projetos irmaos. O repositorio git foi criado no novo local com commit inicial. O projeto foi catalogado em `conhecimento/projetos-irmaos.json`.

## O que foi feito

- Local correto dos projetos irmaos: `EcoSystemUmGrau\Projetos\` (confirmado: SupermarketCalculator, Mp3Player e BibliaEstudoCompleta ja vivem la).
- Aegis movido para `Projetos\aegis`; pasta antiga `Default Project\Projetos\` ficou vazia.
- Git inicializado: `git init`, `.gitignore` criado (exclui `target/`, `reports/`, `data/aegis.db`, `data/cache`, `data/pending`).
- Tres repositorios git aninhados removidos (aegis-knowledge, aegis-scanner-network, aegis-scanner-software) — todos vazios, sem commits nem remote.
- Primeiro commit: "Aegis: motor de diagnostico e remediacao de seguranca em Rust" (65 arquivos).
- Registry atualizado em `conhecimento/projetos-irmaos.json` com o Aegis (tipo rust, status funcional).

## Impacto

O ecossistema passa a conhecer o Aegis como projeto irmao. O projeto tem versionamento git local. Faltam: branch main padrao, remote GitHub, futuros commits via gate.

## Aprendizado

- Todo projeto irmao vive em `EcoSystemUmGrau\Projetos\`, nao em `Default Project\Projetos\`.
- Workspaces Cargo podem conter `.git` aninhados vazios; checar com `Get-ChildItem -Directory -Filter ".git" -Recurse` antes do `git add`.
- Construir o Aegis requer PATH do MSYS2 (`C:\msys64\mingw64\bin`) para o dlltool.

## Conexoes

- [[cluster-hub-programacao]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[rust-ownership-borrow-checker-e-o-modelo-de-memória]]
- [[segurança-owasp-top-10-aplicado-na-prática]]