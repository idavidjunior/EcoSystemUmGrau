---
tipo: padrao
tags: [junkscanner, android, performance, cache, benchmark, scan-incremental]
data: 2026-08-23
contexto: Validação em produção do cache de hash SHA-256 persistente (pendencia #2 do JunkScanner). Benchmark comparativo executado com carga sintética controlada.
decisao: Manter o cache de hash (path|size|lastModified) e a memoização dirSizeMemo. Benchmark confirmou eliminação completa do hashing no rescan.
impacto: Rescan de duplicados não recalcula hashes de arquivos inalterados. Ganho escala com volume de dados e lentidão de I/O.
---

# JunkScanner — Benchmark do scan incremental

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
3. uiautomator dump às vezes cospe stacktrace ENOENT de theme_compatibility junto; dump para arquivo + cat é mais confiável
4. No XML do uiautomator, text= vem ANTES de resource-id=; checked= vem DEPOIS — parsers precisam considerar a ordem
5. O dataset real mudou entre sessões (3335 itens → 5): usuário limpou mídia/dados do app durante uso humano; cache antigo apagado por intervenção externa, não por bug

## Estado das pendências JunkScanner
- #2 scan incremental: VALIDADA (esta sessão)
- Restantes: #1 índice SQLite dedup, #3 export CSV/JSON, #4 widget homescreen, #5 Shizuku/ADB root

## Conexoes

- [[espera-adaptativa-por-tipo-de-recurso]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]