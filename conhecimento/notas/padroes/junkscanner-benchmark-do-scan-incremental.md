---
tags: [dessas, hasheados, opencode, padrao, raízes, são]
aliases: [JunkScanner — Benchmark do scan incremental]
date: 2026-08-23
---

# JunkScanner — Benchmark do scan incremental

**Fonte:** opencode

## Metodologia
1. Carga sintética: 40 arquivos (10 conteúdos únicos × 4 cópias) de 20MB cada = 800MB em /sdcard/Download/bench_dup
2. Cronometragem pelo mtime do files/hash_cache.json (gravado ao fim do scan) contra date +%s do device — resolução 1s, zero drift
3. Sinal de conclusão: switchTab(1) roda dentro do uiHandler.post final → tabResults selected=true = fim do scan

## Resultados
- Scan SEM cache: 2s (hasheou os 800MB)
- Scan COM cache quente: <1s (mesmo segundo; zero hashing)
- Cache: 40 entradas, 5825 bytes; chaves path|size|lastModified; duplicados com mesmo conteúdo compartilham hash esperado (o1.bin == c1_1.bin == c1_2.bin)
- Carga sintética removida após o teste (Download intacto)

## Descobertas operacionais (MIUI)
1. Categoria duplicates varre SOMENTE Download/DCIM/Pictures/Movies/Music/WhatsApp/Telegram (getRootsForCategory) — arquivos fora dessas raízes nunca são hasheados
2. MIUI filtra Log.d de apps no logcat — impossível cronometrar via logcat
3. uiautomator dump às
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]