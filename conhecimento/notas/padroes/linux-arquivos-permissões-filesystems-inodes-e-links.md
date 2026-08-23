---
tags: [container, containers, left, linux, negadas, padrao]
aliases: [Linux: arquivos, permissões, filesystems, inodes e links]
date: 2026-08-23
---

# Linux: arquivos, permissões, filesystems, inodes e links

**Fonte:** linux

No Linux, tudo é arquivo — entender a camada de filesystem explica metade dos bugs de produção (disco cheio, \"no space left\", permissões negadas em container).

**Inodes e estrutura:** um arquivo = inode (metadados: dono, permissões, tamanho, blocos, timestamps) + conteúdo em blocos + nome no diretório. Diretório é uma tabela nome→inode. Consequências: 1) disco pode estar com espaço livre mas `ENOSPC` por falta de inodes (`df -i`); 2) mover arquivo dentro do mesmo fs é só re-link (rápido), entre filesystems é cópia+delete; 3) arquivos abertos continuam acessíveis após `rm` (o inode vive enquanto há open fd) — padrão para remover arquivo de log sem derrubar o app: `rm` e recriar, ou `: > file`.

**Permissões:** 3 classes (dono, grupo, outros) × 3 bits (r=4, w=2, x=1). `chmod 750` = dono rwx, grupo r-x, outros nada. Sticky bit (`chmod +t`, ex. /tmp): só dono apaga; setuid/setgid: roda com euid do dono — **perigo de segurança**, nunca use em scripts; use capabilities do kernel (ex. `setcap cap_net_bind_service=+ep`) para bind em porta <1024 sem root. ACLs (`setfacl/getfacl`) para permissões finas; SELinux/AppArmor para MAC além das permissões POSIX. Dono/grupo: `chown user:group`.

**Links:** hard link = outro nome para o mesmo inode (mesmo número de inode, compartilha dados; só no mesmo filesystem; o arquivo só morre quando o último link é removido). symlink = ponteiro de caminho (inode próprio, aponta para um path; pode cruzar filesystem; quebra se alvo for movido). Diagnóstico: `stat`, `ls -li` (primeira coluna = inode), `readlink`. Para achar hard links: `find / -samefile alvo`; para symlinks quebrados: `find -xtype l`.

**Filesystems:** ext4 (padrão Linux), XFS (escala), tmpfs (RAM, efêmero — use para caches/tmp, mas perde com reboot), overlayfs (containers). I/O troubleshooting: `df -h`/`df -i`, `du -sh *` para tamanho, `lsof +L1` para arquivos deletados ainda abertos (e por isso não liberados), `iostat`/`iotop` para pressão de I/O. Sincronização: `sync`/`fsync` — dados podem estar em cache; em falha de energia, dados podem sumir sem fsync.
## Conexoes

- [[cluster-hub-programacao]]
- [[linux-processos-sinais-systemd-e-supervisionamento]]
- [[linux-shell-pipelines-jq-e-automação-via-ssh]]
- [[padrao-hub-padroes]]