---
tags: [git, head, padrao, perdido, reaplicar, release]
aliases: [Git: resolver conflitos e reverter com segurança (revert, re]
date: 2026-08-12
---

# Git: resolver conflitos e reverter com segurança (revert, reset, cherry-pick)

**Fonte:** git

**Conflitos** ocorrem quando edições concorrentes atingem as mesmas linhas. Resolução segura: (1) `git fetch` e atualize sua branch por `merge` ou `rebase`; (2) identifique os arquivos com `git status` (unmerged) e inspecione com marcadores `<<<<<<< ======= >>>>>>>`; (3) decida o que fica — às vezes os dois lados ('combine'), às vezes só um; (4) para resoluções complexas, use `git mergetool`; (5) após resolver, `git add` e conclua (`git commit` para merge, `git rebase --continue` para rebase). **Reverter com segurança — `git revert`:** cria um commit que desfaz outro commit sem reescrever história; é a única opção segura para história compartilhada. `git revert <commit>` gera um novo commit; use `-m 1` para reverter um merge (informa qual parent manter). Não altera commits existentes → não quebra colegas. **`git reset`:** move o ponteiro da branch, **reescrevendo** história. `--soft` (mantém working tree e index), `--mixed` (default; mantém working tree, limpa index), `--hard` (descarta tudo — perigoso, destrutivo). Use reset apenas em commits **não publicados**. **`git cherry-pick`:** aplica um commit específico (ou vários) em cima da branch atual — útil para portar um fix para uma release branch ou reaplicar trabalho perdido. **Playbook de emergência:** bug em produção → identifique o commit com `git bisect` → `git revert` e deploy; commit apagado antes do push → `git reset --hard <hash>`; trabalho acidental na branch errada → `git stash` ou `cherry-pick` para a branch certa. **Recuperação:** nada se perde enquanto o reflog existir — `git reflog` lista todos os movimentos e permite `git reset --hard HEAD@{n}`. **Regras:** nunca `reset --hard` em história compartilhada; nunca sobrescreva remoto com push normal (use `--force-with-lease`); resolva conflitos olhando o **intento** dos dois lados, não só o texto.
## Conexoes

- [[cluster-hub-programacao]]
- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[padrao-hub-padroes]]