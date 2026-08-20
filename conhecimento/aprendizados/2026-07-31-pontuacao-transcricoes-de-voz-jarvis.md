# Aprendizado — 2026-07-31 — Pontuação automática de transcrições de voz (Jarvis)

## Contexto
- O Android STT (SpeechRecognizer) devolve texto corrido, sem pontuação e **sem prosódia** (a melodia da fala não chega à bridge). O usuário pediu: `?` em perguntas, pontuação correta e **primeira letra maiúscula** sempre.
- Já existia `fix_punctuation()` básico; a reivisão ampliou regras e corrigiu um bug de acentuação.

## O que foi feito (`scripts/jarvis_bridge.py`)
1. **Classificação pergunta vs afirmação (linguística, não prosódica)**:
   - Pergunta (`?`): palavras interrogativas iniciais (`qual, quem, onde, quando, como, o que, que horas, quanto...`), auxiliares/verbos iniciais (`tem como, tem, da pra, posso, pode, e possivel, e verdade, esta certo, sera que, vai, existe...`) e pedidos diretos (`me diz, me fala, sabe me dizer, consegue, gostaria, quero saber...`).
   - Afirmação (`.`): todo o resto (inclui ordens: "liga a luz", "toca uma musica").
2. **Regra do usuário**: primeira letra SEMPRE maiúscula; maiúscula também após `.`, `?` e `!`.
3. **Acentuação**: `_sem_acentos()` (NFD + strip diacríticos) antes do match — STT manda "esta tudo" e "qual e", não "está tudo"/"qual é". Detecção virou insensível a acento.
4. **Aberturas**: saudação inicial vira vírgula ("Oi,", "Bom dia,"); marcas de assentimento/pausa (`tudo bem`, `ta bom`, `ok`, `e voce`...) quebram a cláusula e viram sentença própria.
5. `test_vox.py`: ganhou `teste_fix_punctuation()` (asserts offline) e envia transcrições cruas via WebSocket.

## Heurísticas registradas
- **STT é texto sem prosódia**: para pontuar fala, usar pistas LINGUÃSTICAS (palavras interrogativas, ordem verbo-inicial, padrões de pedido), não tentar analisar entonação que não existe no texto.
- **Normalizar acentos antes do match**: `unicodedata.normalize('NFD')` + filtro de categoria `Mn`; fazer a regex SEM acentos evita duplicar variantes ("e possivel" cobre "é possível").
- **Saudação â‰  pergunta**: a classificação deve olhar DEPOIS da saudação ("Bom dia, que horas são?" — "que horas" decide).

## Estado
- Bridge reiniciada; log real: `"esta tudo pronto para o deploy" -> "Esta tudo pronto para o deploy?"`, `"qual o resumo das ultimas tarefas" -> "Qual o resumo das ultimas tarefas?"`, `"me de um resumo do que fizemos hoje" -> "Me de um resumo do que fizemos hoje."`.
- 21 casos offline + 3 casos no caminho WebSocket validados.
