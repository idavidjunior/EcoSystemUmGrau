---
tags: [fast, forward, git, padrao, publicar, resolve]
aliases: [Git: rebase vs merge e históricos limpos]
date: 2026-08-14
---

# Git: rebase vs merge e históricos limpos

**Fonte:** git

**Merge** cria um commit de união e preserva a topologia real (merge commit visível); **rebase** reescreve os commits da sua branch aplicando-os em cima da base mais recente, produzindo história linear. **Quando usar merge:** é a operação mais segura e 'verdadeira' — preserva contexto de quando o trabalho aconteceu; recomendado para integrar a branch de volta à main (merge de feature fechada), para preservar histórico colaborativo e em branches longas ou compartilhadas. **Quando usar rebase:** para **atualizar** sua branch local com a base antes do merge (evita o ruído de merge commits e antecipa conflitos), e para **limpar** commits (squash/fixup) antes de publicar. **Regra de ouro: nunca rebase história já publicada/compartilhada** — você reescreve hashes que outros podem ter puxado; isso gera duplicatas e corrupção no repositório compartilhado. **Workflow recomendado (linear):** `git switch feature` → `git fetch && git rebase origin/main` (atualiza) → resolve conflitos → `git push --force-with-lease` → PR → merge para main com squash ou fast-forward. **Forçar push com segurança:** use sempre `--force-with-lease`, que aborta se a branch remota mudou desde seu fetch (evita sobrescrever trabalho alheio). **Conflitos em rebase** são resolvidos commit a commit (parar e inspecionar cada um) — o `git rerere` relembra resoluções repetidas; em merge, são resolvidos de uma vez. **Histórico limpo na prática:** (1) commits pequenos e atômicos; (2) mensagens descrevendo o 'porquê'; (3) squash de 'wip' e 'fix typo' antes do merge; (4) evitar commits de merge triviais atualizando por rebase; (5) tag de versões na main. Lembre: o merge commit é o *record* — rebase é a *limpeza*. Escolha um padrão por repositório e documente no CONTRIBUTING.
## Conexoes

- [[cluster-hub-programacao]]
- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]
- [[padrao-hub-padroes]]