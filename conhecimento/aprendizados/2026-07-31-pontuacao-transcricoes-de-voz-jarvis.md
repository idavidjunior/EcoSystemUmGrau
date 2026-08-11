# Aprendizado â€” 2026-07-31 â€” PontuaÃ§Ã£o automÃ¡tica de transcriÃ§Ãµes de voz (Jarvis)

## Contexto
- O Android STT (SpeechRecognizer) devolve texto corrido, sem pontuaÃ§Ã£o e **sem prosÃ³dia** (a melodia da fala nÃ£o chega Ã  bridge). O usuÃ¡rio pediu: `?` em perguntas, pontuaÃ§Ã£o correta e **primeira letra maiÃºscula** sempre.
- JÃ¡ existia `fix_punctuation()` bÃ¡sico; a reivisÃ£o ampliou regras e corrigiu um bug de acentuaÃ§Ã£o.

## O que foi feito (`scripts/jarvis_bridge.py`)
1. **ClassificaÃ§Ã£o pergunta vs afirmaÃ§Ã£o (linguÃ­stica, nÃ£o prosÃ³dica)**:
   - Pergunta (`?`): palavras interrogativas iniciais (`qual, quem, onde, quando, como, o que, que horas, quanto...`), auxiliares/verbos iniciais (`tem como, tem, da pra, posso, pode, e possivel, e verdade, esta certo, sera que, vai, existe...`) e pedidos diretos (`me diz, me fala, sabe me dizer, consegue, gostaria, quero saber...`).
   - AfirmaÃ§Ã£o (`.`): todo o resto (inclui ordens: "liga a luz", "toca uma musica").
2. **Regra do usuÃ¡rio**: primeira letra SEMPRE maiÃºscula; maiÃºscula tambÃ©m apÃ³s `.`, `?` e `!`.
3. **AcentuaÃ§Ã£o**: `_sem_acentos()` (NFD + strip diacrÃ­ticos) antes do match â€” STT manda "esta tudo" e "qual e", nÃ£o "estÃ¡ tudo"/"qual Ã©". DetecÃ§Ã£o virou insensÃ­vel a acento.
4. **Aberturas**: saudaÃ§Ã£o inicial vira vÃ­rgula ("Oi,", "Bom dia,"); marcas de assentimento/pausa (`tudo bem`, `ta bom`, `ok`, `e voce`...) quebram a clÃ¡usula e viram sentenÃ§a prÃ³pria.
5. `test_vox.py`: ganhou `teste_fix_punctuation()` (asserts offline) e envia transcriÃ§Ãµes cruas via WebSocket.

## HeurÃ­sticas registradas
- **STT Ã© texto sem prosÃ³dia**: para pontuar fala, usar pistas LINGUÃSTICAS (palavras interrogativas, ordem verbo-inicial, padrÃµes de pedido), nÃ£o tentar analisar entonaÃ§Ã£o que nÃ£o existe no texto.
- **Normalizar acentos antes do match**: `unicodedata.normalize('NFD')` + filtro de categoria `Mn`; fazer a regex SEM acentos evita duplicar variantes ("e possivel" cobre "Ã© possÃ­vel").
- **SaudaÃ§Ã£o â‰  pergunta**: a classificaÃ§Ã£o deve olhar DEPOIS da saudaÃ§Ã£o ("Bom dia, que horas sÃ£o?" â€” "que horas" decide).

## Estado
- Bridge reiniciada; log real: `"esta tudo pronto para o deploy" -> "Esta tudo pronto para o deploy?"`, `"qual o resumo das ultimas tarefas" -> "Qual o resumo das ultimas tarefas?"`, `"me de um resumo do que fizemos hoje" -> "Me de um resumo do que fizemos hoje."`.
- 21 casos offline + 3 casos no caminho WebSocket validados.

## Conexoes

- [[cluster-hub-programacao]]