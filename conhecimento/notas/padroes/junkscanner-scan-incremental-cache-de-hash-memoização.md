---
tags: [expected, linha, métodos, opencode, padrao, seguintes]
aliases: [JunkScanner — Scan incremental (cache de hash + memoização)]
date: 2026-08-23
---

# JunkScanner — Scan incremental (cache de hash + memoização)

**Fonte:** opencode

## O que foi feito
MainActivity.java recebeu:
- Campos HASH_CACHE_FILE / HASH_CACHE_MAX_ENTRIES=20000 / hashCache (org.json.JSONObject)
- loadHashCache()/saveHashCache() na Activity (load no início do ScanTask.run(), save após o try/catch)
- cacheKey(File) = path|size|lastModified e sha256Cached(File) dentro da ScanTask
- scanDuplicates usa sha256Cached; getDirSize memoizado com dirSizeMemo

## Armadilhas encontradas
1. Edição estrutural deixou um `}` duplicado fechando a ScanTask cedo demais → "class, interface, enum, or record expected" na linha dos métodos seguintes. Corrigido removendo a chave extra.
2. MIUI filtra Log.d do app no logcat — impossível cronometrar por categoria via logcat. Alternativa: polling uiautomator dump.
3. Sinal de fim de scan via btnStartScan enabled=true falha: ao concluir, o app migra automaticamente para a aba RESULTADOS e o botão some da hierarquia.
4. uiautomator dump /dev/tty às vezes vem corrompido no MIUI (lixo ENOENT antes do XML); dump para /data/l
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]