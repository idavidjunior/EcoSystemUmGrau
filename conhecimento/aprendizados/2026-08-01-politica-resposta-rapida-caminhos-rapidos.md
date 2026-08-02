# PolÃ­tica de Resposta RÃ¡pida â€” caminhos rÃ¡pidos constantes no Jarvis

- **Data:** 01/08/2026
- **SessÃ£o:** Ensino permanente de caminhos de resposta rÃ¡pida + otimizaÃ§Ã£o de latÃªncia

## Pedido do usuÃ¡rio
"Ensine o Jarvis a SEMPRE procurar caminhos de rÃ¡pida resposta nas conexÃµes e
caminhos de conexÃ£o mais rÃ¡pidas para respostas mais rÃ¡pidas. Isso deve ser
constante."

## O que foi feito

### 1. PolÃ­tica permanente no prompt (JARVIS_SYSTEM.md)
Nova seÃ§Ã£o logo apÃ³s "Identidade": **"PolÃ­tica de Resposta RÃ¡pida â€” SEMPRE
ATIVA"** com 5 regras: atalhos locais primeiro; nÃ£o recriar o que jÃ¡ existe;
menos saltos = conexÃ£o mais rÃ¡pida; respostas curtas para TTS; constÃ¢ncia em
toda conexÃ£o/mensagem. Como o SISTEMA Ã© injetado em todo prompt, vale sempre.

### 2. Caminho rÃ¡pido SEM LLM na bridge (`caminho_rapido()`)
Atalho local que responde na hora (0 round-trip ao servidor OpenCode) para:
hora, data, bateria do celular, status/online e clima/previsÃ£o. PadrÃµes casados
com acento-insensibilidade (`_sem_acentos`). Retorna `None` se nÃ£o casar â€” o
fluxo normal (LLM) segue intacto. Log `resposta rapida` para observabilidade.

### 3. ConexÃ£o mais rÃ¡pida: cache de estado (`_estado_cacheado()`)
`_montar()` recomputava `gerar_estado_atual()` a CADA mensagem (rglob no vault
Obsidian com 265+ notas + stats). Agora reusa o estado com TTL de 300s.

## Resultado medido
- "que horas sÃ£o" via WebSocket: **~1.8s** (era 15-25s com LLM) â€” sem chamada
  ao LLM no log (`hist=`/`prompt=` ausentes).
- Estado cacheado: 0 I/O de diretÃ³rio por mensagem.
- 30/30 testes offline OK (7 pontuaÃ§Ã£o + 5 horas fala + 10 hora tela + 8
  caminho_rapido).

## PadrÃµes capturados
- **LatÃªncia Ã© desenhada, nÃ£o esperada:** para dados que a bridge jÃ¡ possui,
  a resposta instantÃ¢nea deve vir de cÃ³digo, nÃ£o de uma consulta ao LLM.
- **Regra de ouro aplicada:** o caminho rÃ¡pido ABastece a estrutura do prompt
  (JARVIS_SYSTEM.md) e a bridge â€” nada de estrutura nova paralela.
- **DivisÃ£o clara:** `caminho_rapido` = respostas fÃ¡ceis (dados locais); LLM =
  raciocÃ­nio e tarefas. MantÃ©m a tela `HH:MM` e o Ã¡udio por extenso (reuso de
  `normalizar_hora_display` + `melhorar_fala` no fluxo Ãºnico).

## ValidaÃ§Ã£o
- `test_vox.py` ganhou `teste_caminho_rapido()` (8 casos deterministas).
- WebSocket real: saudaÃ§Ã£o â†’ "que horas sÃ£o" (1.8s) â†’ "qual a data de hoje"
  (â‰ˆ1.8s de TTS), com `resposta rapida` no `bridge_log.txt`.
