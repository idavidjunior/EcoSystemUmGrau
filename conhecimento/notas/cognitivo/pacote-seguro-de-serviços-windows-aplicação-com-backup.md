---
tags: [ativos, cognitivo, ecosystemumgrau, general, rdp, sshd]
aliases: [Pacote Seguro de Serviços Windows — Aplicação com Backup]
date: 2026-08-23
---

# Pacote Seguro de Serviços Windows — Aplicação com Backup

**Dominio:** general

# Pacote Seguro de Serviços Windows — Aplicação com Backup

## Metadados
- tipo: decisao
- tags: [windows, servicos, otimizacao, seguranca, tailscale, teamviewer, sshd, rdp]
- data: 2026-08-23
- contexto: Máquina com 3,9 GB RAM (0,6 GB livre) e 5 canais de acesso remoto ativos. Usuário confirmou uso de Tailscale e TeamViewer; aprovou execução do pacote seguro após verificação de impacto no EcoSystemUmGrau.

## Decisão
Desativar 27 serviços inúteis para este perfil de uso (desenvolvimento local, 

## Ferramenta de limpeza do disco C: (Windows)

Criado `scripts/limpeza_disco.py` como ferramenta permanente do ecossistema para
diagnóstico e limpeza segura do disco C:.

### Bug corrigido na medição
`_size_gb` usava `os.walk` (retornava 0 para arquivos simples) e a condição
`gb > 0` impedia a remoção de arquivos. Corrigido tratando `path.is_file()` e
removendo incondicionalmente após o fix. Por isso a limpeza foi executada em 2
rodadas: a 1ª removeu pastas e a 2ª removeu os arquivos individuais.

### Alvos de limpeza segura
- npm-cache (`AppData\Local\npm-cache`)
- Temp do usuário (`AppData\Local\Temp`)
- VSIX cache (`Roaming\Code\CachedExtensionVSIXs`)
- balena nupkg (`Roaming\balena-etcher`)
- zips do Flutter em `.flutter_auto`
- lixo `is-*.tmp` do Ollama (`cuda_v13`)

### O que NÃO toca
- pagefile.sys (8 GB)
- WSL ext4.vhdx
- opencode.db (~5,89 GB)
- ProgramData\Microsoft, programas instalados
- modelos Ollama (OLLAMA_MODELS aponta para E:\Ollama\models)

### Medição
Get-ChildItem
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]