# REGRAS OBRIGATÓRIAS DO ECOSSISTEMA

> Este arquivo é carregado automaticamente em TODA sessão. As regras abaixo são
> OBRIGATÓRIAS e têm prioridade máxima. A fonte completa está em
> `config/agents/00-system-rules.md` (Constituição v1.0).

## CLÁUSULAS PÉTREAS (IMUTÁVEIS — NÃO PODEM SER IGNORADAS)

### 1. Comunicar passos em áudio
Narrar por áudio cada passo relevante: o que está fazendo, o que vai fazer e o que
descobriu. Nunca parar de comunicar, exceto se o usuário pedir explicitamente.

### 2. Aprender ao final de toda tarefa (sem esperar o usuário pedir)
1. Registrar memória: `python scripts/memory_engine.py add "<titulo>" "<resumo>" <tipo>`
   (argumentos POSICIONAIS; tipos: decisao, erro, padrao, episodio)
2. Criar `conhecimento/aprendizados/YYYY-MM-DD-titulo.md` com frontmatter
3. Sincronizar: git add + commit + push

### 3. Testar antes de aplicar
Qualquer mudança em `opencode.jsonc`, agents, skills, MCP ou fallback DEVE passar
`python scripts/preflight_check.py` (TODOS os testes) antes de aplicar. Se falhar:
BLOQUEAR e reportar.

## REGRAS DE OURO

1. **FONTE ÚNICA** — config, agentes e skills vivem neste repo. Nada duplicado fora.
2. **ABASTECER, NÃO CRIAR ESTRUTURA NOVA** — usar as estruturas existentes.
3. **TESTAR SEMPRE** — validar com `opencode debug config` + preflight.
4. **REGISTRAR APRENDIZADO** — todo fim de tarefa.
5. **SINCRONIZAR SEMPRE** — `ecosystem sync` (pull + deploy + push). GitHub é a rede de segurança.

## FONTES
- Constituição completa: `config/agents/00-system-rules.md`
- Regras LER: `ler-runtime/config/agent_rules.json`
- Regras de ouro: `README.md` → "Regras de Ouro"
