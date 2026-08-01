# Política de Resposta Rápida — caminhos rápidos constantes no Jarvis

- **Data:** 01/08/2026
- **Sessão:** Ensino permanente de caminhos de resposta rápida + otimização de latência

## Pedido do usuário
"Ensine o Jarvis a SEMPRE procurar caminhos de rápida resposta nas conexões e
caminhos de conexão mais rápidas para respostas mais rápidas. Isso deve ser
constante."

## O que foi feito

### 1. Política permanente no prompt (JARVIS_SYSTEM.md)
Nova seção logo após "Identidade": **"Política de Resposta Rápida — SEMPRE
ATIVA"** com 5 regras: atalhos locais primeiro; não recriar o que já existe;
menos saltos = conexão mais rápida; respostas curtas para TTS; constância em
toda conexão/mensagem. Como o SISTEMA é injetado em todo prompt, vale sempre.

### 2. Caminho rápido SEM LLM na bridge (`caminho_rapido()`)
Atalho local que responde na hora (0 round-trip ao servidor OpenCode) para:
hora, data, bateria do celular, status/online e clima/previsão. Padrões casados
com acento-insensibilidade (`_sem_acentos`). Retorna `None` se não casar — o
fluxo normal (LLM) segue intacto. Log `resposta rapida` para observabilidade.

### 3. Conexão mais rápida: cache de estado (`_estado_cacheado()`)
`_montar()` recomputava `gerar_estado_atual()` a CADA mensagem (rglob no vault
Obsidian com 265+ notas + stats). Agora reusa o estado com TTL de 300s.

## Resultado medido
- "que horas são" via WebSocket: **~1.8s** (era 15-25s com LLM) — sem chamada
  ao LLM no log (`hist=`/`prompt=` ausentes).
- Estado cacheado: 0 I/O de diretório por mensagem.
- 30/30 testes offline OK (7 pontuação + 5 horas fala + 10 hora tela + 8
  caminho_rapido).

## Padrões capturados
- **Latência é desenhada, não esperada:** para dados que a bridge já possui,
  a resposta instantânea deve vir de código, não de uma consulta ao LLM.
- **Regra de ouro aplicada:** o caminho rápido ABastece a estrutura do prompt
  (JARVIS_SYSTEM.md) e a bridge — nada de estrutura nova paralela.
- **Divisão clara:** `caminho_rapido` = respostas fáceis (dados locais); LLM =
  raciocínio e tarefas. Mantém a tela `HH:MM` e o áudio por extenso (reuso de
  `normalizar_hora_display` + `melhorar_fala` no fluxo único).

## Validação
- `test_vox.py` ganhou `teste_caminho_rapido()` (8 casos deterministas).
- WebSocket real: saudação → "que horas são" (1.8s) → "qual a data de hoje"
  (≈1.8s de TTS), com `resposta rapida` no `bridge_log.txt`.
