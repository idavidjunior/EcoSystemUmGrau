---
tags: [argumentos, converte, cuidado, espaços, linux, padrao]
aliases: [Linux: shell, pipelines, jq e automação via SSH]
date: 2026-08-23
---

# Linux: shell, pipelines, jq e automação via SSH

**Fonte:** linux

O terminal é a interface de programação do sistema. Fluxo de trabalho de sênior: compor programas pequenos via pipes, nunca escrever script gigante.

**Pipelines:** `cmd1 | cmd2 | cmd3` — stdout do anterior alimenta stdin do próximo. Por padrão, stderr não passa pelo pipe (use `2>&1` para incluir). O exit code do pipe é o do último comando (use `set -o pipefail` para propagar falha — padrão obrigatório em scripts). Filtros clássicos: `grep` (seleciona linhas), `sed` (transforma), `awk` (extrai/agrega colunas), `cut`, `sort`, `uniq -c` (conta duplicados — padrão para top N), `head/tail`, `xargs` (converte stdin em argumentos — cuidado com espaços, use `-0`). Evite `cat | grep`: use `grep arquivo`. Processamento paralelo: `xargs -P`, GNU parallel.

**jq — JSON no terminal:** ferramenta indispensável para APIs e infra. `curl -s api | jq '.data'`; `jq -r '.items[].id'` (raw output sem aspas — útil em loops); `jq 'map(select(.status==\"ok\")) | length'`; agregação com `group_by(.dept) | map({dept: .[0].dept, n: length})`; `--arg` para passar variável; `@csv` para exportar. Sempre `jq -e` para falhar se o JSON for inválido (checagem em scripts).

**SSH seguro e produtivo:** `ssh user@host`; chaves: `ssh-keygen -t ed25519`, `ssh-copy-id`; config `~/.ssh/config` com Hosts (Host dev → HostName, User, IdentityFile) — atalho `ssh dev`. Hardening: `PermitRootLogin no`, `PasswordAuthentication no`, `PubkeyAuthentication yes`; `ControlMaster`/`ControlPersist` para multiplexação (evita re-handshake); `ProxyJump` para bastion; `ssh -o StrictHostKeyChecking=accept-new`. Copiar: `scp`/`rsync -avz --delete`; túneis: `ssh -L 8080:localhost:8080` para port forward. **NUNCA** rode ssh em scripts interativos com senha (use agent/chave + `BatchMode`); **NUNCA** rode comandos destrutivos via loop sem dry-run.

**Hábitos de script:** `set -euo pipefail` sempre; `#!/usr/bin/env bash`; variáveis sempre com `\"...\"`; checar exit code; usar `mktemp` para temp; evitar `eval`; dividir em funções; idempotência. Lint com shellcheck no CI.
## Conexoes

- [[cluster-hub-programacao]]
- [[linux-arquivos-permissões-filesystems-inodes-e-links]]
- [[linux-processos-sinais-systemd-e-supervisionamento]]
- [[padrao-hub-padroes]]