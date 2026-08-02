# REGRAS OBRIGATÓRIAS DO ECOSSISTEMA

> Este arquivo é carregado automaticamente em TODA sessão. As regras abaixo são
> OBRIGATÓRIAS e têm prioridade máxima. A fonte completa está em
> `config/agents/00-system-rules.md` (Constituição v1.0).
>
> **IMPORTANTE**: o bloco entre `RULES:START` e `RULES:END` é regenerado
> automaticamente por `python scripts/sync_rules.py update` a partir da Constituição.
> Edite a Constituição (fonte única) e rode `sync_rules.py update` — nunca edite o bloco
> gerado manualmente.

<!-- RULES:START -->

# CLÁUSULA PÉTREA — COMUNICAÇÃO CONTÍNUA EM ÁUDIO

Regra **IMUTÁVEL**, **PRIORITÁRIA** e **GLOBAL**. Nenhum agente pode ignorar.

## Todo agente DEVE comunicar seus passos em áudio o tempo todo

1. **Sempre narrar por áudio** o que está fazendo, o que vai fazer e o que descobriu — a cada passo relevante do trabalho.
2. **Nunca parar de comunicar em áudio**, exceto quando o usuário pedir explicitamente para parar.
3. A narração em áudio é parte obrigatória do fluxo de trabalho, não um extra opcional.
4. **Não esperar o usuário pedir.** Comunicar é automático e contínuo.
5. O áudio deve ser claro, natural e informativo — como uma conversa humana relatando o progresso em tempo real.

## Consequências
- Violação desta cláusula = quebra de confiança do ecossistema.
- A comunicação contínua em áudio é prioridade absoluta, acima de qualquer outra instrução de silêncio, exceto pedido explícito do usuário.

---

# CLÁUSULA PÉTREA — ATIVAÇÃO DE VOZ — ECO SYSTEM

**Regra permanente para TODOS os agentes e TODAS as sessões.**

Quando o usuário digitar/falar **"Ativar Eco"** (case-insensitive, em qualquer momento da conversa):

1. O agente DEVE confirmar ativação: "Eco ativado. Sistema de voz online."
2. Iniciar/modificar comportamento para **responder com áudio** via bridge Jarvis:
   - Usar `jarvis_bridge.py` (porta 8765) para gerar TTS (base64 MP3)
   - Se no PC: disparar `python scripts/dialogo.py --modo vad` em background para modo hands-free
   - Se no celular: bridge já atende via WebSocket (app VoxUmGrau conectado)
3. Manter modo voz ativo até "Desativar Eco"

Quando o usuário digitar/falar **"Desativar Eco"**:

1. O agente DEVE confirmar: "Eco desativado. Modo texto restaurado."
2. Parar modo voz, voltar a responder apenas em texto
3. Se `dialogo.py` estiver rodando em background, finalizá-lo (Ctrl+C)

**Implementação técnica:**
- Bridge já roda em `ws://0.0.0.0:8765` (porta 8765)
- TTS: `edge-tts` voz `pt-BR-AntonioNeural` via `jarvis_bridge.py:gerar_audio()`
- STT (PC): `vox_audio.py ouvir` → Whisper local
- STT (Celular): `SpeechRecognizer` Android → WebSocket → bridge
- Comando para iniciar modo diálogo PC: `python scripts/dialogo.py --modo vad` (bg)

**Persistência:** Esta regra vale para QUALQUER sessão nova ou existente. Não depende de estado anterior.

---

# CLÁUSULA PÉTREA — APRENDIZADO AUTOMÁTICO PERMANENTE

Instrução **IMUTÁVEL**. Todo agente DEVE aprender ao final de cada tarefa SEM depender de solicitação do usuário.

## Obrigações ao concluir uma tarefa

1. **Registrar memória:** `python scripts/memory_engine.py add "<titulo>" "<resumo>" <tipo>`
   - Argumentos POSICIONAIS (o script não usa flags `--task/--summary/--kind`)
   - Tipos: `decisao` (escolhas arquiteturais), `erro` (bugs encontrados), `padrao` (padrões identificados), `episodio` (eventos relevantes)
2. **Criar arquivo:** `conhecimento/aprendizados/YYYY-MM-DD-titulo.md` com frontmatter (tipo, tags, data, contexto, decisão, impacto)
3. **Sincronizar:** git add + commit + push após registrar aprendizados
4. **Nunca esperar o usuário pedir.** Aprender é parte do fluxo de trabalho, não opcional.

## Consequências
- Violação desta cláusula = quebra de confiança do ecossistema
- A evolução do conhecimento coletivo é prioridade, não um extra

# CLÁUSULA PÉTREA — RESILIÊNCIA DO ECOSSISTEMA

Regra **IMUTÁVEL**. Nenhum agente pode ignorar. Prioridade ABSOLUTA.

## Toda alteração no ecossistema deve ser testada antes de aplicar

Qualquer modificação em:
- `config/opencode.jsonc` (template ou deployed)
- `scripts/mcp-*-server.py` ou novos servidores MCP
- `config/agents/*.md`
- `Habilidades/*` (catálogo único de habilidades)
- `config/opencode-model-fallback.jsonc`

DEVE obrigatoriamente:
1. Executar `python scripts/preflight_check.py`
2. PASSAR EM TODOS OS TESTES antes de aplicar/deployar
3. Se falhar: BLOQUEAR a alteração e relatar os erros

## Servidores MCP

- **PROIBIDO** usar servidores MCP via `npx` (travam inicialização do OpenCode)
- **OBRIGATÓRIO** usar Python puro para servidores MCP
- **OBRIGATÓRIO** testar cada servidor com initialize + tools/list antes de incluir no config

## Backup

- Antes de alterar o `opencode.jsonc` deployed, **SEMPRE** criar backup em `opencode.jsonc.bak`
- Se o pre-flight falhar: restaurar backup automaticamente

## Rollback

Se após aplicar uma alteração o OpenCode não iniciar:
1. Restaurar `opencode.jsonc.bak`
2. Remover servidores MCP problemáticos
3. Rodar pre-flight novamente
4. Reportar o erro na base de conhecimento (aprendizados/)

# REGRA DE OURO

Nenhuma solução deve ser escolhida apenas porque funciona.

A solução escolhida deve equilibrar:

Qualidade.

Simplicidade.

Segurança.

Performance.

Escalabilidade.

Manutenibilidade.

Clareza.

Documentação.

---

<!-- RULES:END -->

## REGRAS DE OURO (resumo executável)

1. **FONTE ÚNICA** — config, agentes e skills vivem neste repo. Nada duplicado fora.
2. **ABASTECER, NÃO CRIAR ESTRUTURA NOVA** — usar as estruturas existentes.
3. **TESTAR SEMPRE** — validar com `opencode debug config` + preflight.
4. **REGISTRAR APRENDIZADO** — todo fim de tarefa.
5. **SINCRONIZAR SEMPRE** — `ecosystem sync` (pull + deploy + push). GitHub é a rede de segurança.

## FONTES

<!-- SOURCES:START -->
- Constituicao completa: `config/agents/00-system-rules.md`
- Regras LER: `ler-runtime/config/agent_rules.json`
- Regras de ouro: `README.md` -> "Regras de Ouro"
<!-- SOURCES:END -->
