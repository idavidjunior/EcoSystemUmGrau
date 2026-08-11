---
tags: [devops, escape, kernel, padrao, runc, toolchain]
aliases: [DevOps: containers — camadas, imagens mínimas e non-root]
date: 2026-08-11
---

# DevOps: containers — camadas, imagens mínimas e non-root

**Fonte:** devops

Contêiner é processo isolado, não máquina virtual. Entender a imagem (UFS — Union File System) muda como você constrói e diagnostica.

**Camadas (layers):** cada instrução do Dockerfile gera uma camada imutável que, se inalterada, é cacheada. Regras de ouro: 1) ordene do menos para o mais mutável (sistema base, dependências do projeto, código); mudar código não rebuiu as camadas de dependências — builds ficam rápidos; 2) combine comandos (`&& apt-get install -y pkg && rm -rf /var/lib/apt/lists/*`) para não empurrar cache e bloat; 3) copie arquivos seletivamente (`COPY package.json` antes de `COPY .`) para invalidação mínima de cache; 4) `.dockerignore` para não enviar `node_modules`/`.git` ao daemon.

**Tamanho e segurança:** base distroless (Google) tem só runtime e libc — menos superfície de ataque e menos CVE a patch; alpine é pequena mas tem musl (binários glibc podem quebrar) e nem sempre mais segura. Prefira bases oficiais com tag distroless ou slim + scan (trivy). Multi-stage build: compile em imagem cheia (golang/node build) e copie só o binário/runtime para a imagem final — artefato mínimo, sem toolchain.

**Non-root é obrigatório:** defina `USER 10001`/`USER app` no final do Dockerfile — rodar como root no contêiner é a mesma coisa que root no host sob escape (CVE de kernel/runC). Permissões: chown de volumes em runtime (init containers) e nunca chmod 777.

**Operação:** PID 1 deve tratar sinais — use `exec` ou tini para reaproveitar zombies; `HEALTHCHECK` com comando simples; não coloque estado dentro do contêiner (stateless + volumes externos); `docker inspect`/`crictl` para diagnóstico; limite recursos (`--memory`, `--cpu-shares`) para evitar neighbor noise. Meta final: imagem pequena, imutável, sem secrets, non-root, assinada e com SBOM.
## Conexoes

- [[cluster-hub-programacao]]
- [[devops-infraestrutura-como-código-terraform-e-imutabilidade]]
- [[devops-observabilidade-logs-estruturados-métricas-e-tracing-]]
- [[devops-pipelines-de-cicd-artefatos-ambientes-e-promoção]]
- [[padrao-hub-padroes]]