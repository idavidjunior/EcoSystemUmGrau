---
id: os-maintenance-windows
categoria: os
nome: os-maintenance-windows
descricao: "Manutenção nativa do Windows - ferramentas built-in para diagnóstico, reparo, otimização e saúde do sistema. Unifica chkdsk, sfc, dism, defrag, storage health, event logs, boot config, windows update, e mais."
entrypoint: windows_maintenance.py
script: mcp/os/habilidades/os-maintenance/Windows/windows_maintenance.py
---

# Windows Native Maintenance Tools — Domínio Completo

## Visão Geral

Este núcleo domina **todas as ferramentas nativas do Windows** para manutenção, diagnóstico, reparo e otimização. Zero dependências externas — apenas o que o Windows já fornece.

---

## Ferramentas Cobertas

### 1. Sistema de Arquivos & Disco

| Ferramenta | Função | Requer Admin |
|------------|--------|--------------|
| **chkdsk** | Verifica e corrige erros no sistema de arquivos (NTFS/FAT32/exFAT) | Sim (para /F, /R) |
| **defrag / Optimize-Volume** | Desfragmentação HDD / Retrim SSD / Otimização em camadas | Não (análise), Sim (operações) |
| **format** | Formata volumes | Sim |
| **diskpart** | Gerenciamento avançado de partições/discos | Sim |
| **Storage Module (PowerShell)** | Get-StorageHealthReport, Repair-Volume, Optimize-Volume, Get-PhysicalDisk | Variável |

### 2. Integridade do Sistema (System Integrity)

| Ferramenta | Função | Requer Admin |
|------------|--------|--------------|
| **sfc /scannow** | System File Checker - repara arquivos de sistema corrompidos | **Sim** |
| **DISM /Online /Cleanup-Image /RestoreHealth** | Repara o component store (WinSxS) | **Sim** |
| **DISM /Online /Cleanup-Image /StartComponentCleanup** | Limpa component store | **Sim** |
| **DISM /Online /Cleanup-Image /AnalyzeComponentStore** | Analisa tamanho do component store | **Sim** |

### 3. Saúde de Armazenamento (Storage Health - PowerShell)

```powershell
Get-StorageHealthReport        # Relatório SMART/NVMe health
Get-PhysicalDisk               # Info discos físicos (MediaType, HealthStatus, OperationalStatus)
Get-StorageHealthAction        # Ações recomendadas
Repair-Volume                  # Repara volume (equiv. chkdsk /F online)
Optimize-Volume                # Desfrag/Retrim/TierOptimize
```

### 4. Logs de Eventos & Diagnóstico

| Ferramenta | Função |
|------------|--------|
| **wevtutil** | Query, export, clear, archive event logs |
| **Get-WinEvent (PowerShell)** | Query avançada com XPath filtering |
| **Get-EventLog (Legacy)** | Logs clássicos (System, Application, Security) |

### 5. Configuração de Inicialização (Boot)

| Ferramenta | Função | Requer Admin |
|------------|--------|--------------|
| **bcdedit** | Edita BCD (boot config data) | **Sim** |
| **bcdedit /export** | Backup BCD | **Sim** |
| **bcdedit /import** | Restore BCD | **Sim** |
| **reagentc** | Configura WinRE (Recovery Environment) | **Sim** |

### 6. Windows Update

| Ferramenta | Função |
|------------|--------|
| **Get-WindowsUpdateLog** | Gera log legível do Windows Update |
| **wuauclt /detectnow /updatenow** | Força detecção/instalação (legacy) |
| **Uso moderno: USOClient /Installer /Updater** | Cliente Windows Update moderno |
| **PSWindowsUpdate module** | Module PowerShell comunitário (opcional) |

### 7. Serviços & Processos

| Ferramenta | Função |
|------------|--------|
| **sc query / config / start / stop** | Service Control Manager CLI |
| **Get-Service / Set-Service / Restart-Service** | PowerShell |
| **tasklist / taskkill** | Processos |
| **Get-Process / Stop-Process / Wait-Process** | PowerShell |

### 8. Rede & Conectividade

| Ferramenta | Função |
|------------|--------|
| **netsh** | Configuração rede avançada (winsock reset, interface reset, firewall) |
| **ipconfig / flushdns / registerdns / release / renew** | DNS/IP |
| **Test-NetConnection (PowerShell)** | Teste conectividade (TCP, ICMP, rota) |
| **Resolve-DnsName** | DNS lookup PowerShell |

### 9. Registro & Perfil

| Ferramenta | Função |
|------------|--------|
| **reg query / add / delete / export / import** | Registry CLI |
| **Get-ItemProperty / Set-ItemProperty (PowerShell)** | Registry PS |

### 10. Drivers & Hardware

| Ferramenta | Função |
|------------|--------|
| **pnputil** | Driver store (add, delete, export, enum) |
| **devcon** | Device manager CLI (Windows SDK) |
| **Get-PnpDevice (PowerShell)** | Enumera dispositivos |

### 11. WinFR — Windows File Recovery (Microsoft Store)

> **Nota:** `winfr` **não vem pré-instalado**. Deve ser instalado via Microsoft Store (`Microsoft.WindowsFileRecovery`).

```cmd
winfr C: D: /regular /n *.docx /n *.pdf     # Modo regular (NTFS)
winfr C: D: /extensive /n *                 # Modo extensivo (qualquer FS)
winfr C: D: /segment /n *.jpg               # Modo segment (recuperar por segmento)
```

**Modos:**
- `/regular` — NTFS, arquivos deletados recentemente
- `/extensive` — Qualquer FS, busca profunda por assinatura
- `/segment` — NTFS, recupera por segmentos de registro

**Filtros:** `/n <padrão>`, `/y:<tipo>` (doc, pic, vid, etc.), `/k` (recupera arquivos de sistema)

---

## Script Principal: windows_maintenance.py

### Estrutura de Comandos

```bash
# Health check completo
python windows_maintenance.py health

# Disco: análise + reparo
python windows_maintenance.py disk --analyze --repair

# Sistema: sfc + dism
python windows_maintenance.py system --sfc --dism

# Otimização: defrag/trim/retim
python windows_maintenance.py optimize --all

# Logs: exportar erros recentes
python windows_maintenance.py logs --errors --days 7 --output logs_erros.evtx

# Boot: backup BCD
python windows_maintenance.py boot --backup-bcd

# Update: status + log
python windows_maintenance.py update --status --log

# Drivers: listar problemas
python windows_maintenance.py drivers --problems

# Relatório completo (JSON)
python windows_maintenance.py report --json --output report.json
```

### Classes Principais

- `WindowsMaintenance` — Orquestrador principal
- `DiskHealth` — chkdsk, defrag, Storage Health, SMART
- `SystemIntegrity` — sfc, DISM, component store
- `EventLogManager` — wevtutil, Get-WinEvent
- `BootConfig` — bcdedit, reagentc
- `WindowsUpdateManager` — Get-WindowsUpdateLog, USOClient
- `ServiceManager` — sc, Get-Service
- `NetworkDiagnostics` — netsh, Test-NetConnection
- `DriverManager` — pnputil, Get-PnpDevice

---

## Exemplo de Uso Programático

```python
from windows_maintenance import WindowsMaintenance

wm = WindowsMaintenance()

# Health check completo
report = wm.full_health_check()
print(report.summary)

# Reparo de disco
wm.disk.repair_volume("C:")

# Verificar integridade sistema
wm.system.run_sfc()
wm.system.run_dism_restore()

# Otimizar SSD
wm.disk.optimize_volume("C:", "Retrim")

# Exportar logs de erro dos últimos 3 dias
wm.logs.export_errors(days=3, output="errors.evtx")
```

---

## Pré-requisitos

- Windows 10/11
- PowerShell 5.1+ (nativo)
- **Admin rights** para operações de reparo (sfc, dism, chkdsk /F, bcdedit)
- WinFR opcional: `winget install Microsoft.WindowsFileRecovery`

---

## Segurança & Boas Práticas

1. **Sempre execute como Admin** para operações destrutivas/reparadoras
2. **Backup BCD** antes de mexer em boot (`bcdedit /export`)
3. **Crie ponto de restauração** antes de DISM/sfc grandes
4. **Use `/scan` antes de `/spotfix`** no chkdsk (online primeiro)
5. **Monitore Storage Health** antes de reparos agressivos
6. **Log tudo** — o script gera auditoria automática em `%TEMP%\os-maintenance\`

---

## Integração com EcoSystemUmGrau

- Registra aprendizados via `memory_engine.py` (tipo: `padrao`, tags: `windows,maintenance`)
- Checkpoint de estado via `runtime_state.py`
- Compatível com `@sync` para versionamento
- Auditoria via `preflight_check.py` antes de operações críticas