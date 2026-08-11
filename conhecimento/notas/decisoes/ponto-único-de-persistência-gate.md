---
tags: [causando, decisao, escrita, genéricos, indiscriminada, opencode]
aliases: [Ponto único de persistência (gate)]
date: 2026-08-10
---

# Ponto único de persistência (gate)

**Fonte:** opencode

---
tipo: decisao
tags: [persistencia, git, gate, automação, vigilante, arquitetura, pétrea]
data: 2026-08-10
contexto: Vários serviços em segundo plano (vigilante, ecosystem.ps1, narrador, register_learning órfãos) executavam git add/commit/push de forma concorrente e indiscriminada (git add -A), causando commits genéricos, corrida de escrita no knowledge_graph.json e reversão de cards de conhecimento (processos register_learning antigos sobrescrevendo o grafo com versão defasada).
decisao: Criar o PONTO ÚNICO DE PERSISTÊNCIA (scripts/persistencia.ps1) responsável por TODO commit/push do ecossistema (EcoSystemUmGrau, ler-runtime, projetos Android), com modo AUTO/MANUAL desativável via config/persistencia.json e lock por repositório. Vigilante e ecosystem.ps1 delegam ao gate (run-sync); nenhum outro script commita direto. Cláusula pétrea adicionada à Constituição (16 regras sincronizadas nas 3 camadas).
impacto: Commits automáticos parados quando o usuário quiser (persistencia.ps1 manual) e retomados com persistencia.ps1 auto; commit manual via persistencia.ps1 commit; status via persistencia.ps1 status; eliminação dos commits espúrios "[auto] LER" dentro do repo eco; corrida de register_learning mitigada (processos órfãos matados).
---

# Ponto único de persistência (gate)

## Comandos
- `persistencia.ps1 status` → modo atual (AUTO/MANUAL), HEAD e pendências por repo.
- `persistencia.ps1 manual` → pausa TODOS os commits automáticos (serviços continuam consolidando, nada vai ao git).
- `persistencia.ps1 auto` → reativa os commits automáticos.
- `persistencia.ps1 commit -Repo eco -Mensagem "..." -Push` → commit manual em qualquer modo.
- `persistencia.ps1 sync -Push` → commit manual de eco + ler + projetos Android.

## Configuração
- `config/persistencia.json` → `modo` ("auto"/"manual") e `excluir` (paths que ficam fora dos commits do gate).
- Log do gate: `%USERPROFILE%\.persistencia.log`.
- Locks por repositório em `%TEMP%\persistencia-<hash>.lock` (TTL 120s).

## Arquitetura
- `vigilante.ps1` → `Sync-GitRepo`/`Sync-ProjectRepo` agora chamam `persistencia.ps1 run-sync` (pull → add → commit → push) e NÃO tocam o git diretamente.
- `ecosystem.ps1` → bloco de commit substituído pela chamada ao gate.
- Nenhum script/agente executa `git commit`/`git push` direto (cláusula pétrea).

## Causa raiz corrigida (reversão dos cards)
- Processos `register_learning` órfãos (ex.: PID 9128 da sessão de ontem) recarregavam e salvavam o knowledge_graph.json com versão defasada, revertendo 36 cards de tradução.
- Ação: matar processos órfãos; o gate serializa commits com lock; novos aprendizados são consolidados lendo o disco atual.

## Verificação
- `python -c "import json; len(json.load(open('ler-runtime/knowledge/knowledge_graph.json'))['patterns'])"` → 244.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]