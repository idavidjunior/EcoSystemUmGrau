# 2026-08-16: Detecção automática de inglês no TTS

**Categoria:** padrao
**Contexto:** Evolução do narrador para pronunciar corretamente palavras em inglês no meio do texto PT-BR.

## Implementação

Criado `scripts/detect_english_words.py` que:
1. Carrega lista de frequência de palavras inglesas (~5000 top words) de `config/english_freq.json`
2. Detecta palavras inglesas genéricas via heurísticas:
   - Apenas ASCII letters (sem acentos)
   - Tamanho >= 4 letras (evita stop words: the, and, is, etc.)
   - camelCase/PascalCase (getUserData, saveUserProfile)
   - Acrônimos em maiúscula (API, HTTP, JSON)
   - Presença na lista de frequência
3. Aplica SSML `<lang xml:lang="en-US">palavra</lang>` para TTS neural
4. NÃO duplica termos já cobertos pelo glossário técnico (`pronunciar_termos.py`)

## Integração

- `pipeline_completo_tts(texto)` = glossário técnico + detecção automática
- Integrado em `narrador_desktop.py` no `_flush()` (após `limpar_texto`)
- Também aplicado no `teste_audio()`

## Exemplo

Entrada: `"O erro aconteceu no database connection quando o server caiu. Chame getUserData."`

Saída SSML: `"O erro aconteceu no <lang xml:lang=\"en-US\">database</lang> <lang xml:lang=\"en-US\">connection</lang> quando o <lang xml:lang=\"en-US\">server</lang> caiu. Chame <lang xml:lang=\"en-US\">getUserData</lang>."`

## Arquivos

- `scripts/detect_english_words.py` — módulo principal
- `config/english_freq.json` — lista de frequência (top ~5000 palavras)
- `scripts/narrador_desktop.py` — integração no pipeline de fala
