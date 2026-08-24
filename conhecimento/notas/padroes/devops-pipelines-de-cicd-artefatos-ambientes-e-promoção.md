---
tags: [automático, blue, canary, devops, green, padrao]
aliases: [DevOps: pipelines de CI/CD — artefatos, ambientes e promoção]
date: 2026-08-10
---

# DevOps: pipelines de CI/CD — artefatos, ambientes e promoção

**Fonte:** devops

Pipeline bom é caixa de vidro: qualquer pessoa lê o YAML e sabe o que roda, por que e o que promove o artefato de um ambiente ao próximo.

**Princípios:** 1) artefato único — o mesmo build binário/imagem que passa nos testes é o que vai para produção; nada de reconstruir por ambiente (build once, promote everywhere). 2) Pipeline declarativo e versionado junto ao código (GitHub Actions, GitLab CI, Jenkinsfile declarative); o código define a pipeline, não o servidor. 3) Determinístico: nada de flaky tests, estado escondido, variável mágica; se falhou, correção vai para o pipeline, não workaround. 4) Rápido feedback: camadas — lint/typecheck (1min), testes rápidos, testes pesados, build de artefato; falha precoce economiza fila.

**Estrutura típica:** stage lint → unit → build → scan (SAST/DAST/SCA/licença) → teste de integração → push de artefato/imagem (tag com SHA do commit, não `latest`) → deploy em staging → smoke test → espera de aprovação manual → promoção para produção → canary/blue-green e rollback automático.

**Artefatos:** registry de imagens (ECR, GHCR, Artifactory) ou de pacotes, imutáveis por tag; retenção e `--immutable` para impedir overwrite; assinatura (cosign) e SBOM anexados.

**Ambientes e promoção:** ambiente = contexto configurado (staging, qa, prod). Promoção = mover o mesmo artefato mudando apenas configuração (env/secret). Nunca promova código recompilado. Gate de promoção: testes verdes + scan ok + aprovação; em produção, deploy incremental com healthcheck e rollback (deploy anterior já pronto para voltar).

**Não vire caixa preta:** 1) visibilidade: logs de cada stage, duração, custo; 2) versionamento da própria pipeline e testes da pipeline (dry-run, falha de stage é auditável); 3) secrets via vault/inject, nunca em YAML; 4) metadados rastreáveis (build number, SHA, autor, mudanças incluídas) registrados no deploy; 5) um pipeline por caminho de entrega — separar CI (construir/validar) de CD (implantar) permite gate independente.
## Conexoes

- [[cluster-hub-programacao]]
- [[devops-containers-camadas-imagens-mínimas-e-non-root]]
- [[devops-infraestrutura-como-código-terraform-e-imutabilidade]]
- [[devops-observabilidade-logs-estruturados-métricas-e-tracing-]]
- [[padrao-hub-padroes]]