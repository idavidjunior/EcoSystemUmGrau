---
tags: [aponta, cachedextensionvsixs, condição, decisao, etcher, opencode]
aliases: [limpeza disco windows]
date: 2026-08-27
---

# limpeza disco windows

**Fonte:** opencode

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

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]