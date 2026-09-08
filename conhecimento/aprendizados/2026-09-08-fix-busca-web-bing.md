---
tipo: erro
tags: [busca-web, bing, decoder, detecao-correcao]
data: 2026-09-08
contexto: Roteamento de busca web do Vox usava DDG lite, que passou a ser bloqueado por IP. Fallback adicionado para Bing, mas a URL real vem em redirect ck/a com u= base64 prefixado.
decisao: Corrigir _decodifica_url_bing em scripts/jarvis_bridge.py e priorizar a query enxuta sobre a original.
impacto: Buscas de trânsito, promoção e clima agora devolvem dados reais com fonte. DDG segue bloqueado; Bing funcional sem chave.
---

# Fix: decode do redirect do Bing e prioridade da query enxuta

## Sintomas
- `_buscar_web` retornava URLs vazias/quebradas para o fallback Bing.
- Para "como esta o transito agora na marginal tiete", os resultados eram irrelevantes (ESTA, esta-ou-está).

## Causa raiz (2 bugs)
1. **Decoder com `return ""` prematuro**: o loop de prefixos `("a1a1","a1a","a1")` retornava vazio assim que um prefixo casava e o decode falhava. Para `a1aHR0cH...` o prefixo `a1a` casa mas produz lixo binário (erro utf-8 0xcb); o prefixo correto é `a1` (2 chars), que nunca era testado. Identificado com `inspect.getsource` (test_inspect_func.py) e comparando com a versão que funcionava (test_dec_u3.py).
2. **Query original prioritária**: `_buscar_web` tentava a frase original antes da enxuta. "como esta o transito agora na marginal tiete" contém "esta", que o Bing interpreta como ESTA/esta-ou-está e retorna resultados de mercado, não de trânsito.

## Corrigido
- `_decodifica_url_bing`: `continue` quando o prefixo não casa; `return ""` somente após esgotar os 3 prefixos; tenta paddings 0-3; valida `^https?://`.
- `_buscar_web`: inverte a ordem das consultas — enxuta primeiro, original como fallback (mantém cache por chave normalizada e TTL 600s).

## Evidência
- `py_compile` OK (2x).
- `test_parse_bing_dbg.py`: URLs reais decodificadas (tiendeo.com.br, promocaoype.com.br, uol.com.br, magazineluiza.com.br).
- `test_busca_web_final2.py` (cache limpo): trânsito → G1 e Waze; tixan ype → promocaoype; clima → climatempo/UOL/INMET.

## Aprendizado
- Ao testar fallback de buscadores, validar com páginas HTML reais salvas localmente.
- Testes devem rodar via arquivos .py temporários: PowerShell inline destrói `$`, `&` e `"`.
- Query enxuta (stopwords removidas) costuma ser mais precisa que a frase original, especialmente com palavras ambíguas como "esta".