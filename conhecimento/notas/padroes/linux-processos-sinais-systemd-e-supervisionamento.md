---
tags: [custom, linux, padrao, pausar, retomar, sigusr1]
aliases: [Linux: processos, sinais, systemd e supervisionamento]
date: 2026-08-22
---

# Linux: processos, sinais, systemd e supervisionamento

**Fonte:** linux

Um processo é uma instância de programa com PID, espaço de endereço, contexto e relações de parentesco (PPID). Supervisão correta de processos é o que separa serviços que morrem silenciosamente dos que sobrevivem a crash.

**Processos:** `ps auxf` (árvore de processos), `top`/`htop` (CPU/RAM), `pgrep`, `kill`. Estados: running, sleeping (interruptible/uninterruptible — D = I/O), zombie (Z: filho terminou, pai não fez wait — geralmente bug do pai). Use `systemd-cgtop`/`systemd-analyze` para recursos por serviço.

**Sinais:** são mensagens assíncronas ao processo. Principais: `SIGTERM` (15) — pedido gracioso de término (default), `SIGKILL` (9) — imposição, não tratável, `SIGHUP` (1) — recarregar config (daemons), `SIGINT` (2) — Ctrl+C, `SIGSTOP`/`SIGCONT` — pausar/retomar, `SIGUSR1/2` — custom. Sequência correta: tente `SIGTERM`, aguarde timeout, depois `SIGKILL`. Em docker/k8s o mesmo: envie TERM, app deve capturar e fazer graceful shutdown (fechar conexões, drenar trabalhos). Nunca `kill -9` como primeiro recurso — corrompe estado (DB, filas).

**Systemd:** o init padrão. `systemctl start/stop/restart/status/enable/daemon-reload`. Unidade = arquivo `.service` com `[Unit]` (After, Wants), `[Service]` (ExecStart, Restart=on-failure, User=, EnvironmentFile=, TimeoutStopSec=) e `[Install]` (WantedBy=multi-user.target). Conceitos-chave: 1) `Restart=` — systemd supervisiona e revive processos (on-failure com `RestartSec`); 2) `Type=notify` — serviço avisa quando está pronto (`sd_notify`), habilita dependências corretas; 3) `LimitNOFILE`, `LimitMEMLOCK` para hardening; 4) `journalctl -u servico` para logs centralizados; 5) `systemd-analyze blame` para boot lento; 6) timers (`systemd-timer`) substituem cron com log e dependências.

**Supervisionamento em escala:** no container, o PID 1 deve reaper zombies e repassar sinais — use `exec` no CMD ou tini/s6. Fora do systemd: keepalived, supervisor, pm2 para node. Checklist: processo reinicia sozinho? Logs persistem e rotacionam? Sinal TERM faz shutdown gracioso? Métricas de restarts monitoradas?
## Conexoes

- [[cluster-hub-programacao]]
- [[linux-arquivos-permissões-filesystems-inodes-e-links]]
- [[linux-shell-pipelines-jq-e-automação-via-ssh]]
- [[padrao-hub-padroes]]