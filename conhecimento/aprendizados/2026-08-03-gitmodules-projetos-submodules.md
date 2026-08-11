---
tipo: decisao
tags: [git, submodules, gitmodules, projetos, estrutura]
data: 2026-08-03
contexto: Gitlinks dos Projetos/ existiam sem .gitmodules, impedindo clone recursivo
---

# Formalizacao de submodules dos projetos

## Decisao

Criado .gitmodules com as 11 entradas de Projetos/ (url + branch). backups/ adicionado ao .gitignore (nao versionar). Removido gitlink fantasma plugins/ponytail (vazio, sem remote).

## Impacto

git clone --recursive do EcoSystemUmGrau agora baixa todos os projetos automaticamente. Validado com clone de teste em temp.

## Conexoes

- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]