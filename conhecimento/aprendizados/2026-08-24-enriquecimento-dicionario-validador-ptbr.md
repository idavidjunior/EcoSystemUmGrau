---
tipo: erro
tags: [validador, pt-br, dicionario, nlp, correção]
data: 2026-08-24
contexto: Respostas 100% pt-BR reprovadas 3x seguidas pelo gate validar_resposta.py durante sessão de sugestão de investimento
decisao: Enriquecer PALAVRAS_PT (600 → 5511 palavras) e reformular calcular_score_pt com métrica por palavra
impacto: Gate pt-BR deixa de gerar falso negativo em texto legítimo denso em termos técnicos; espanhol e inglês continuam reprovados
---

# Enriquecimento do validador pt-BR

## Problema detectado
Resposta financeira legítima em português reprovada com score 19.5 (threshold 30).
Causas raiz encontradas na inspeção de validar_idioma.py:

1. Dicionário PALAVRAS_PT incompleto — não conhecia nem "sobre", "dia", "mês", "sistema"
2. Componente de acentos calculado sobre caracteres TOTAIS do texto (~3-5% em pt real), diluindo o score
3. Sem penalidade para palavras estrangeiras inequívocas

## Correções aplicadas (scripts/validar_idioma.py)

### Vocabulário (4 fontes)
- Corpus interno: Constituição, AGENTS.md, README + aprendizados (392 palavras com marca pt inequívoca, freq >= 3)
- Bloco manual curado: meses, dias, números por extenso, saudações, verbos supercomuns, advérbios, vocabulário financeiro
- Wiktionary BrazilianPortuguese_wordlist (OpenSubtitles top 4971): extraídas via regex `[[palavra#Portuguese|...]]</span> freq`; filtro `[a-zà-ú]+` elimina mojibake da fonte; anti-contaminação cruzando rank com en_50k.txt do FrequencyWords (descarta se rank inglês < 2500) → 4296 aceitas
- stopwords-iso/stopwords-pt: 89 novas após filtro de forma

### Métrica (calcular_score_pt)
- Novo componente marcas-pt POR PALAVRA (15%): caracteres ã õ á à â é ê í ó ô ú ç + dígrafos nh lh ç ão ões — não dilui mais no total de caracteres
- Peso de chars-no-texto reduzido 20% → 10%
- SUFIXOS_PT ampliado: terminações verbais (-ando -endo -indo -ava -iam -aria -eria), nomes (-ança -ença -ório -ória -ário -ária -dade -eira -eiro)
- Penalidade (máx -40, 4 pts/palavra) para PALAVRAS_NAO_PT: funcionais inequívocas de espanhol (el los del pero también año...) e inglês (the and with would...)

### Blindagem de processo
- Escrita atômica sempre (tmp + os.replace)
- compile() do novo conteúdo ANTES de tocar o disco
- Backup .bak antes de cada inserção

## Resultados (bateria adversarial 8/8)
| Caso | Antes | Depois |
|---|---|---|
| resposta financeira real | 19.5 REPROVADO | 51.7 aprovado |
| inglês puro | (nd) | 3.8 reprovado |
| espanhol | (nd) | 28.3 reprovado |
| pt simples | (nd) | 53.7 aprovado |
| técnico misto runtime/kernel | (nd) | 41.0 aprovado |

## Bug colateral corrigido
memories.json entry sintética (id 497) gravada com chave 'created' em vez de 'created_at' quebrava memory_engine stats (KeyError). Fix duplo: registro normalizado no dado + _decay_score tolerante (last_accessed → created_at → created → agora).

## Lições
1. Listas públicas OpenSubtitles/FrequencyWords vêm com mojibake nos acentos — filtrar por forma `[a-zà-ú]+` resolve sem perder volume
2. Console PowerShell exibe UTF-8 como mojibake — verificar bytes antes de diagnosticar corrupção inexistente
3. Score baseado em razão sobre caracteres totais é armadilha: métricas linguísticas devem ser por palavra
4. pip install --target falhou silenciosamente neste ambiente (exit 15, pasta não criada) — preferir fontes raw quando possível

## Conexoes

- [[estrangeirismos-no-pt-br-anglicismos-aceitos-aportuguesament]]
- [[formas-de-tratamento-em-pt-br-você-tu-senhora-e-concordância]]
- [[norma-culta-x-coloquial-no-pt-br-quando-usar-cada-registro-n]]
- [[regionalismos-brasileiros-como-traduzir-sem-cair-em-gírias-m]]
- [[siglas-acrônimos-e-nomes-próprios-manter-traduzir-ou-adaptar]]
- [[variações-pt-pt-x-pt-br-reescrever-para-o-brasileiro]]