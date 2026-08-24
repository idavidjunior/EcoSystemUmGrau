---
tipo: padrao
tags: [junkscanner, android, performance, cache, scan-incremental]
data: 2026-08-23
contexto: Pendência #2 do JunkScanner — scans repetidos reprocessavam tudo (hash SHA-256 de todos os candidatos a duplicado + rescan das mesmas pastas nas categorias cache/temp/logs).
decisao: Duas otimizações sem mudar semântica dos resultados. (1) Cache persistente de hash chaveado por path|size|lastModified em getFilesDir()/hash_cache.json (org.json.JSONObject, máx 20000 entradas com reset), consultado por sha256Cached() em scanDuplicates — invalidação automática quando arquivo muda. (2) dirSizeMemo (HashMap intra-scan) em getDirSize da ScanTask para não ressomer as mesmas pastas entre categorias.
impacto: Segundo scan deve pular todo o hashing de arquivos inalterados e eliminar somas redundantes de diretório. Build OK, APK instalado no device 6d92eed7, scan completo validado (3335 itens, 176.6 MB) e cache persistido em produção (3937 bytes). Benchmark comparativo pendente.
---

# JunkScanner — Scan incremental (cache de hash + memoização)

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
4. uiautomator dump /dev/tty às vezes vem corrompido no MIUI (lixo ENOENT antes do XML); dump para /data/local/tmp/xxx.xml + cat é mais confiável.

## Estado da validação
- Build OK, install -r OK, scan completo rodou com o código novo (3335 itens).
- hash_cache.json criado e persistido (3937 bytes) — gravação funciona em produção real.
- Benchmark comparativo (sem cache vs com cache) NÃO executado: usuário pegou o device durante o teste e o cache foi apagado por intervenção externa. Repetir quando o aparelho estiver livre.

## Próximos passos
1. Benchmark: apagar cache → scan → anotar duração; scan imediatamente depois → comparar.
2. Se ganho confirmado, pendência #1 (índice SQLite dedup) ou #3 (export CSV/JSON).

## Conexoes

- [[espera-adaptativa-por-tipo-de-recurso]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]