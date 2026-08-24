# Pacote Seguro de Serviços Windows — Aplicação com Backup

## Metadados
- tipo: decisao
- tags: [windows, servicos, otimizacao, seguranca, tailscale, teamviewer, sshd, rdp]
- data: 2026-08-23
- contexto: Máquina com 3,9 GB RAM (0,6 GB livre) e 5 canais de acesso remoto ativos. Usuário confirmou uso de Tailscale e TeamViewer; aprovou execução do pacote seguro após verificação de impacto no EcoSystemUmGrau.

## Decisão
Desativar 27 serviços inúteis para este perfil de uso (desenvolvimento local, WSL2, ADB, acesso remoto via Tailscale/TeamViewer): SysMain, Spooler, DoSvc, TrkWks, PcaSvc, CertPropSvc, SharedAccess, SEMgrSvc, TabletInputService, FontCache3.0.0.0, QWAVE, DusmSvc, DPS, WdiServiceHost, WdiSystemHost, lmhosts, WinHttpAutoProxySvc, SSDPSRV, fdPHost, FDResPub, IKEEXT, PolicyAgent, SstpSvc, sshd, TermService, SessionEnv, UmRdpService.

## Verificações pré-execução (obrigatórias, todas feitas)
1. Privilégio admin ausente no shell → elevação UAC via Start-Process -Verb RunAs -Wait.
2. Grep no repositório por ssh/scp/mstsc/3389 → nenhum uso real pelo ecossistema (só menções didáticas).
3. Bluetooth: rádio presente mas zero dispositivos conectados → trio BT deixado FORA por cautela.
4. Stack WSL2 (WSLService/vmcompute/hns/HvHost) preservado explicitamente.
5. Snapshot ANTES exportado antes de qualquer mudança.

## Resultado verificado
- 25/27 parados imediatamente; 2 (TabletInputService, WinHttpAutoProxySvc) desativados no registro, param no reboot.
- Portas 22 e 3389 deixaram de escutar.
- Tailscale, TeamViewer e Chrome Remote Desktop intactos rodando.
- RAM livre: 600 MB → 750 MB.

## Lições técnicas
- DoSvc e WinHttpAutoProxySvc recusam Set-Service → fallback reg add Start=4 funciona.
- WinHttpAutoProxySvc é protegido contra Stop-Service em builds recentes; Disabled no registro basta.
- Start-Process -Verb RunAs -Wait pode estourar timeout da ferramenta se o usuário demorar no UAC; o log em arquivo permite verificar depois sem re-executar.
- Reversão individual documentada no cabeçalho do script e no backup_antes.csv.

## Impacto
Superfície de ataque reduzida de 5 para 3 canais remotos, menos I/O e memória de fundo numa máquina de pouca RAM, zero impacto no OpenCode desktop, WSL2, ADB e pontes do ecossistema.

## Conexoes

- [[segurança-autenticação-e-gestão-de-sessões-seguras]]
- [[segurança-controle-de-acesso-rbacabac-e-menor-privilégio]]
- [[segurança-criptografia-hashing-cifras-tls-e-segredos]]
- [[segurança-hardening-e-dependências-vulneráveis-sbom-cve-e-su]]
- [[segurança-owasp-top-10-aplicado-na-prática]]