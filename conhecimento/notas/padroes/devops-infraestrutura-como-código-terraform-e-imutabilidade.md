---
tags: [apt, artefato, criptografia, devops, padrao, troca]
aliases: [DevOps: infraestrutura como código — Terraform e imutabilida]
date: 2026-08-15
---

# DevOps: infraestrutura como código — Terraform e imutabilidade

**Fonte:** devops

Infraestrutura como código (IaC) transforma infraestrutura em dado versionado e revisável. Terraform é o padrão de facto por seu ecossistema de providers.

**Por que IaC:** reproduzível (mesmo código → mesmo ambiente), revisável (PR em infra!), auditável (histórico do git = histórico de mudanças), destrutivo-consciente (destroy é planejado), on-boarding trivial. O estado (terraform.tfstate) é a fonte da verdade da realidade aplicada — trate-o como dado valioso: armazene em backend remoto (S3 + DynamoDB lock, GCS, Terraform Cloud) com locking para impedir corridas, nunca no git, com criptografia.

**Fluxo Terraform:** `init` (baixa providers) → `plan` (diff do estado desejado vs real; é o momento de revisão) → `apply` (aplica). Regras: 1) nunca aplique sem revisar o plan — o diff mostra criação/atualização/remoção; 2) variáveis via tfvars/ambiente, nunca hardcoded secrets; 3) módulos reutilizáveis para padronizar (VPC, EC2, RDS) com versionamento de versão; 4) `terraform fmt` + `validate` no CI; 5) cuidado com `destroy` em produção — use workspaces/env separados e proteções (prevent_destroy, lifecycle).

**Imutabilidade:** infraestrutura imutável = nunca edita uma instância existente; qualquer mudança gera uma nova (mudança de imagem → novo EC2/container, deploy é troca de artefato, não ssh + apt). Benefícios: reproduzível, rollback = voltar a versão anterior da imagem (sem \"deu certo antes, não sei o que mudei\"), menos snowflake servers. No serverless/K8s, isso é nativo (nova revisão/Deployment). Desafios: dados persistentes (RDS, volumes) são mutáveis — separe estado de compute; criaturas com patches ad-hoc quebram imutabilidade: proíba login/ssh para edição.

**Padrões de evolução:** 1) ambiente como cópia (dev = prod com parâmetros menores); 2) destrói e recria barato (efêmero); 3) drift detection: `terraform plan` em CI comparando com o real (drift = realidade divergiu do código — corrija a causa, não force apply); 4) combinar com Pulumi/Ansible/CDK: Terraform para provisão, config management só onde necessário; 5) secrets do estado em chave acessível só a quem opera.
## Conexoes

- [[cluster-hub-programacao]]
- [[devops-containers-camadas-imagens-mínimas-e-non-root]]
- [[devops-observabilidade-logs-estruturados-métricas-e-tracing-]]
- [[devops-pipelines-de-cicd-artefatos-ambientes-e-promoção]]
- [[padrao-hub-padroes]]