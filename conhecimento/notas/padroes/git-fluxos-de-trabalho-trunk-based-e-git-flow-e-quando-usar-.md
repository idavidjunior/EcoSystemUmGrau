---
tags: [esconder, forte, git, grandes, incompleto, padrao]
aliases: [Git: fluxos de trabalho (trunk-based e git flow) e quando us]
date: 2026-08-10
---

# Git: fluxos de trabalho (trunk-based e git flow) e quando usar cada

**Fonte:** git

**Git Flow** usa duas branches de longa duração (main e develop) mais branches de feature, release e hotfix. As features entram em develop; release branches congelam e geram versões; hotfixes vão para main e de volta a develop. **Vantagens:** disciplina clara, bom para releases agendadas (SaaS com release train, versões semânticas explícitas) e equipes grandes com QA em ciclo. **Custo:** overhead de merges contínuos main→develop, ciclo mais longo, e complexidade que vira burocracia. **Trunk-based development:** todos integram em uma única branch (trunk/main) em PRs curtos e frequentes, com **feature flags** para esconder trabalho incompleto e **CI forte** com deploy contínuo. Releases são cortes (tag) a partir do trunk ou de release branches de vida curta. **Vantagens:** integração contínua real, conflitos raros e pequenos, deploy a qualquer momento. **Custo:** exige disciplina de PRs pequenos (<~400 linhas), testes rápidos e automáticos, e flags bem gerenciadas. **Como escolher:** equipes pequenas/médias e produto contínuo (web, SaaS) → trunk-based com feature flags e CI. Produtos com releases versionadas obrigatórias, clientes legados com versões suportadas em paralelo ou certificação por release → Git Flow. Muitos times usam um híbrido: trunk para desenvolvimento e branch de release curta no final do ciclo. **Regras universais:** nunca commitar direto na main (exceto emergências documentadas); branch de feature deriva de main recente e é mergida/rebasada logo; teste antes do merge, preferencialmente via CI. O objetivo de qualquer fluxo é **reduzir o tempo entre 'escrito' e 'integrado'** — se o fluxo atrasa isso, ele está errado para o seu contexto.
## Conexoes

- [[cluster-hub-programacao]]
- [[git-conventional-commits-e-versionamento-semântico]]
- [[git-rebase-vs-merge-e-históricos-limpos]]
- [[git-resolver-conflitos-e-reverter-com-segurança-revert-reset]]
- [[padrao-hub-padroes]]