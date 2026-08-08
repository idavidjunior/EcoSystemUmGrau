---
tipo: padrao
tags: [compreensao, llm, opencode, resiliencia, mcp]
data: 2026-08-08
contexto: Modulo compreensao-pedidos refinava via NVIDIA/OpenAI/Anthropic (lentas/indisponiveis). Usuario pediu conectar a LLM padrao do opencode como primaria e manter NVIDIA como backup.
decisao: Refino usa `opencode run --agent compreensao-refino -m <modelo> --format json` (LLM da sessao, sem chave extra). Backup: NVIDIA -> OpenAI -> Anthropic. Fail-soft preservado.
impacto: Refino estruturado em ~20-26s (antes: timeout NVIDIA). Resiliencia em cadeia: se a primaria nao responde, o backup entra; se tudo falha, `llm_refino.usado:false` e a compreensao estatica nunca quebra.
---

# Compreensao de pedidos: refino com a LLM do opencode (primaria) + backups

## Problema
O refino opcional do modulo `compreensao-pedidos` chamava NVIDIA via litellm.
NVIDIA dava timeout (30/60s) e o refino ficava inutil na pratica.

## Solucao implementada
1. **`_refinar_via_opencode`** em `compreensao.py`: chama `opencode run --agent
   compreensao-refino -m {COMPREENSAO_MODELO_OPENCODE|LLM_MODEL|opencode/big-pickle}
   --format json "<prompt>"` e extrai os eventos `type=text` do stream.
2. **Agente `compreensao-refino`** no config (template + deployed): `permission: {"*": "deny"}`
   (texto puro, sem ferramentas) + `prompt` de sistema que forca JSON unico
   `{"objetivo_corrigido", "lacunas", "melhorias", "observacao"}`.
3. **Cadeia em `refinar_com_llm`**: opencode (primaria) -> NVIDIA -> OpenAI -> Anthropic.
4. **`sys.stdout.reconfigure(encoding='utf-8')`** no CLI: respostas do opencode contem
   emoji/unicode e quebravam o print cp1252 (`UnicodeEncodeError`).

## Descobertas tecnicas (lições)
- **`opencode run` headless com prompt longo NAO trava por recursao, mas o agente usa
  ferramentas** (carrega AGENTS.md/Constituicao via `instructions` e "executa" a tarefa:
  rodou preflight, buscou runtime...). Com `permission:*:deny` o agente responde texto
  direto (~15-20s vs 65s+ com tools).
- **`{{LLM_MODEL}}` nao resolvido em `opencode run` headless** -> `Model not found:
  {{LLM_MODEL}}/.`. Sempre passar `-m <modelo>` explicito.
- **`COMPREENSAO_EM_REFINO=1`** como guarda anti-recursao (se o agente headless chamasse
  a propria tool `refinar_entendimento`).
- **cwd neutro** (`runtime/refino`, gitignored) evita AGENTS.md do projeto na sessao aninhada.
- Start-Process + `2>$null` + `Out-File` no PS 5.1 pode engolir/corromper saida JSON;
  preferir RedirectStandardOutput para arquivo e parsear com Python.

## Validacao
- `compreensao.py "<pedido>" --refinar --json` -> `llm_refino.usado:true, provedor:opencode`,
  critica estruturada (objetivo_corrigido + 4 lacunas + 3 melhorias), ~26s.
- Failover: `COMPREENSAO_MODELO_OPENCODE=opencode/modelo-inexistente` -> caiu para NVIDIA,
  timeout, `usado:false` com motivo (fail-soft) — resiliencia comprovada.
- `preflight_check.py`: TODOS TESTES PASSARAM. `sync_rules.py update`: 3 camadas OK (13 regras).

## Conexoes

- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]