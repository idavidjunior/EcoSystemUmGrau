---
tipo: padrao
tags: [fidelity, roundtrip, pyembroidery, pes, embroidery, teste]
data: 2026-09-13
contexto: Missão de implementar src/validation/fidelity_report.py no EmbroideryEngine — relatório de fidelidade render vs original e verificação de round-trip PES (escrita + leitura) com evidências numéricas.
decisao: Módulo novo em src/validation/ (build_report com SSIM + DICE por cor + PNG/JSON; verify_roundtrip com writers pyembroidery/native). Gold standard via pyembroidery; encoder nativo NÃO modificado, bug documentado com números.
impacto: Gate de fidelidade objetivo — qualquer regressão de encoder ou digitizer vira falha numérica, não opinião. 12 testes novos, 92 no total, todos verdes.
---

# Fidelity Report & Round-trip PES (EmbroideryEngine)

## Resultados obtidos (test_image.png, 631 stitches, 4 cores, 32x33mm)

| Métrica | Valor |
|---|---|
| SSIM (render vs original) | 0.6238 |
| DICE Color_0 (29,80,199) | 0.8744 |
| DICE Color_1 (200,40,39) | 0.3731 |
| DICE Color_2 (39,159,59) | 0.7626 |
| DICE Color_3 (240,199,29) | 0.7906 |
| Roundtrip GOLD pyembroidery | ok=True, exp=631 read=631, max_err=0.0mm |
| Roundtrip NATIVE (PESWriter) | ok=False, exp=631 read=639, max_err=1608.66mm |

## Evidência do bug do encoder nativo (PESWriter)

O gold standard (pyembroidery, referência) escreve e lê o mesmo design com erro 0.0mm.
O encoder nativo produz PES que, relidos, geram 639 pontos com erro máximo de 1608mm
(≈1.6 metro) — lixo geométrico. Causas já mapeadas: offset PEC 235 em vez de ~251,
header `#PEC` (4 bytes) em vez de `#PEC0001`, 524 bytes antes dos stitches.

## Aprendizados técnicos (reutilizáveis)

1. pyembroidery `EmbThread`: usar `th.set_color(r, g, b)` (3 args → color int).
   NUNCA `pattern.add_thread({...})` — o `__hash__` faz `self.color & 0xFFFFFF` e
   explode se color não for int (`TypeError: __hash__ method should return an integer`).
2. Comparação de round-trip PES: filtrar SÓ stitches de costura (comando 0).
   O pyembroidery insere jump inicial de entrada (posicionamento) — contar/medir
   jumps polui a métrica (632 vs 631, erro 16mm fantasma).
3. `EmbroideryDesign.add_object` NÃO popula `palette.threads` — designs manuais
   precisam de fallback: `_effective_threads(design)` deriva cores dos objetos.
4. PowerShell 5.1 recusa `python -c` multi-linha ("ScriptBlock s deve ser..."):
   escrever script em arquivo tmp e rodar `python arquivo.py`.
5. `np.array_equal(a, b)` não compara shape (100,4) com (4,) — usar `.all()` com
   broadcasting ou comparar pixel único.

## Arquivos

- `src/validation/fidelity_report.py` (módulo)
- `tests/test_fidelity_report.py` (12 testes)
- Artefatos: `Temp/fidelity_report.png`, `Temp/fidelity_report.json`