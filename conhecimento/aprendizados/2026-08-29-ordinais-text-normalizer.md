---
tipo: erro
tags: [tts, ordinal, text_normalizer, pronuncia, placeholder]
data: 2026-08-29
contexto: text_normalizer.py expandia 1º/2ª como "umº" (sufixo ordinal mantido), pois _normalize_numbers só tratava inteiros/percentuais. Correção necessária para expandir ordinais por extenso.
decisao: Adicionar ordinal_por_extenso(n, genero) (1..999, masc/fem) e regex (?<![\d.,])(\d{1,3})([ºª]) com placeholder "=ORDO<chave_letras>M/F=" (chave só-de-letras via _letras_de para a regex de inteiros não capturar o dígito) restaurado no _final_cleanup via dict self._ordinais. O placeholder evita que a palavra expandida vire conector inicial/meio ("Primeiro,") no pipeline de capitalização/respiração. Testes: "1º lugar"→"primeiro lugar", "2ª edição"→"segunda edição", "21º ano"→"vigésimo primeiro ano", "101ª turma"→"centésima primeira turma".
impacto: Ordinais falados corretamente no TTS. test_vox offline: fix_punctuation 7/7, horas 5/5 (era 5/5; module reports 7/7 a versão atual conta 5 casos), normalizar_hora_display 10/10, caminho_rapido 14/14, audio_sem_ssml 7/7 (inclui 1º colocado + 10% + data 31/07/2026), pronuncia 8/8. Preflight: TODOS PASSARAM. Obs: teste WebSocket do test_vox falha por timeout da API externa (bridge), não relacionado.
---
