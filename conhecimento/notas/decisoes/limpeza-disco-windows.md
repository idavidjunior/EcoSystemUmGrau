---
tags: [conhecidos, decisao, gradle, nupkg, opcional, opencode]
aliases: [limpeza disco windows]
date: 2026-08-27
---

# limpeza disco windows

**Fonte:** opencode

---
tipo: decisao
tags: [limpeza, disco, windows, c-drive, cache, ferramenta, manutencao]
data: 2026-08-27
contexto: Usuário pediu a limpeza segura do disco C: no Windows e uma ferramenta permanente que repita diagnóstico e limpeza automaticamente. Escopo é Windows apenas (não confundir com Android).
decisao: Criar scripts/limpeza_disco.py com diagnóstico + limpeza segura de caches conhecidos (npm-cache, Temp do usuário, VSIX, balena nupkg, zips Flutter em .flutter_auto, lixo is-*.tmp do Ollama em cuda_v13). Não mexe em pagefile, WSL vhdx, opencode.db, ProgramData/Microsoft, Programas instalados ou modelos Ollama (já apontam para E:).
impacto: Espaço livre do C: passou de 11,9 GB para 23,87 GB. Removidos: npm-cache (4,8 GB), Temp (~3,6 GB), VSIX cache (0,85 GB), balena nupkg (0,19 GB), 2 zips Flutter (1,77 + 1,34 GB) e tmp do Ollama (0,45 GB). Ferramenta passo -a: python scripts/limpeza_disco.py --diagnostico (relatório) / --limpar (limpeza) / --limpar --simular (prévia) / --gradle (opcional: caches antigos 8.x). Log em runtime/limpeza_disco.log.
---

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
Get-ChildItem/PowerShell é a medição confiável. `os.walk` do Python é lento em
pastas com muitos arquivos (estourou timeout de 120 s no bash — usar timeout
>= 900000 ms ao rodar via shell). // ---
tipo: decisao
tags: [limpeza, disco, windows, c-drive, cache, ferramenta, manutencao]
data: 2026-08-27
contexto: Usuário pediu a limpeza segura do disco C: no Windows e uma ferramenta permanente que repita diagnóstico e limpeza automaticamente. Escopo é Windows apenas (não confundir com Android).
decisao: Criar scripts/limpeza_disco.py com diagnóstico + limpeza segura de caches conhecidos (npm-cache, Temp do usuário, VSIX, balena nupkg, zips Flutter em .flutter_auto, lixo is-*.tmp do Ollama em cuda_v13). Não mexe em pagefile, WSL vhdx, opencode.db, ProgramData/Microsoft, Programas instalados ou modelos Ollama (já apontam para E:).
impacto: Espaço livre do C: passou de 11,9 GB para 23,87 GB. Removidos: npm-cache (4,8 GB), Temp (~3,6 GB), VSIX cache (0,85 GB), balena nupkg (0,19 GB), 2 zips Flutter (1,77 + 1,34 GB) e tmp do Ollama (0,45 GB). Ferramenta passo -a: python scripts/limpeza_disco.py --diagnostico (relatório) / --limpar (limpeza) / --limpar --simular (prévia) / --gradle (opcional: caches antigos 8.x). Log em runtime/limpeza_disco.log.
---

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
Get-ChildItem/PowerShell é a medição confiável. `os.walk` do Python é lento em
pastas com muitos arquivos (estourou timeout de 120 s no bash — usar timeout
>= 900000 ms ao rodar via shell).

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]