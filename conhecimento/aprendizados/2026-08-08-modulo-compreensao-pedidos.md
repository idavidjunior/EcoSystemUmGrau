---
tipo: padrao
tags: [compreensao-pedidos, mcp, nucleo, stdlib, llm-fail-soft, litellm, nvidia, kernel]
data: 2026-08-08
contexto: Usuário pediu para eliminar o DSPy/prompt-optimization e criar um módulo próprio de compreensão de pedidos, que entende o que o usuário quer e converte em ação
decisao: Criar mcp/nucleo/habilidades/compreensao-pedidos (100% stdlib, refino LLM opcional fail-soft e agnóstico) e integrar no Kernel via contrato-entrada; aposentar prompt-optimization/DSPy
impacto: Pedidos agora são compreendidos (objetivo/ações/conceitos/ambiguidades/score) antes de executar; preflight cobre os dois protocolos MCP; nova cláusula pétrea na Constituição
---

# Módulo de Compreensão de Pedidos (mcp-compreensao-pedidos)

Substitui o pipeline DSPy/PromptWizard de otimização de prompts. Em vez de polir o
prompt, o ecossistema agora COMPREENDE o pedido e o converte em ação estruturada.

## Estrutura

```
mcp/nucleo/habilidades/compreensao-pedidos/
  compreensao.py   # núcleo stdlib, CLI, importável (CPython puro)
  server.py        # MCP server (5 tools), transporte stdio dual
  skill.md         # instruções de uso
```

## O que faz (estático, instantâneo, sem LLM)

- **Ações explícitas** extraídas por radicais de verbo (com variantes c→qu da
  conjugação: `explic|expliqu`, `verific|verifiqu`, `chec|chequ`, `busc|busqu`)
  e **ordenadas por posição de aparição no texto** (não por ordem da regex).
- **Objeto da ação** cortado no próximo verbo e em "e <verbo>" (com split por
  stopwords: "e me diga", "e faça o backup").
- **Verbos auxiliares genéricos** ("faça", "faz") descartados quando imediatamente
  antes de outra ação real.
- **Conceitos** = entidades conhecidas (projetos/skills/scripts) + termos
  capitalizados, filtrando stopwords e verbos capitalizados em início de frase.
- **Score de clareza (0-100)** + julgamento `CLARO`/`PARCIALMENTE_CLARO`/`AMBIGUO`.
- **Riscos de desperdício**: repetição (vs `runtime/state.json last_task`),
  escopo creep, sem entregável claro.

## Refino LLM (opcional, fail-soft, agnóstico)

- Chaves **somente** de `scripts/.env` (NUNCA `.env.example`, que só tem
  placeholders). Guard contra valores `your-*/example/xxxx`.
- Provedores em ordem: NVIDIA → OpenAI → Anthropic.
- **NVIDIA via litellm**: precisa do prefixo `openai/` + `api_base
  https://integrate.api.nvidia.com/v1` — o prefixo `nvidia/` NÃO é reconhecido
  pelo litellm 3.x ("LLM Provider NOT provided").
- Modelo configurável via `COMPREENSAO_MODELO_NVIDIA`
  (default `meta/llama-3.3-70b-instruct`).
- Falha ou ausência de chave → `llm_refino.usado: false` com motivo; a
  compreensão estática NUNCA quebra.

## Integrações

- **Kernel**: `scripts/runtime_kernel.py contrato-entrada` agora chama o módulo e
  alimenta o contrato de entrada (restrições, critérios de sucesso, ações).
- **Config**: `config/opencode.jsonc` + deployed trocam `mcp-prompt-optimization`
  por `mcp-compreensao-pedidos`; comando `otimizar` → `compreender`.
- **Manifesto**: entrada `compreensao-pedidos` no `mcp/manifesto_mcp.json`
  (domínio `nucleo`).
- **Constituição**: cláusula "COMPREENSÃO DE PEDIDOS ANTES DE EXECUTAR" substitui
  "PIPELINE DE OTIMIZAÇÃO DE PROMPTS" (via `sync_rules.py update`, 3 camadas OK).

## Lições técnicas (importantíssimas)

1. **Preflight vs framing MCP**: `preflight_check.py` e os servidores legados
   usam JSON **por linha**; o opencode usa **Content-Length framing**. Servidor
   novo precisa de leitura **dual**: se a 1ª linha começa com `Content-Length:`,
   fazer framing; senão, tratar a linha como JSON cru. (E `preflight_check.py`
   foi atualizado para aceitar as duas formas de resposta.)
2. **Bug clássico de framing**: ao ler o header em duas etapas (`first` + loop),
   o header `Content-Length` é consumido na 1ª leitura e o loop só vê a linha em
   branco → headers vazios → `length=0`. Semear os headers com a primeira linha.
3. **Encoding no Windows**: `Set-Content -Encoding utf8` do PowerShell 5.1 grava
   UTF-8 com BOM e, ao reler com `Get-Content -Raw` (ANSI), corrompe não-ASCII →
   mojibake em regex `[\wÀ-ÿ]`. SEMPRE usar o write tool (UTF-8 limpo).
4. **`setdefault` para variáveis de LLM**: não sobrescrever chaves já presentes
   no ambiente ao carregar `scripts/.env`.

## Verificação

- CLI: `compreensao.py "<pedido>" --json` → objetivo/ações/score corretos.
- Suite de regressão: "me explique…", "Atualize o VoxUmGrau e commita…",
  "Verifique o preflight e busque o erro no log", "rode o preflight_check.py e me
  diga o resultado", "Conserte o bug… e faça o backup antes".
- Probe MCP (framing): INIT + 5 tools + tools/call OK.
- `preflight_check.py`: TODOS TESTES PASSARAM (13 MCPs, incl. o novo).
- `sync_rules.py audit`: 3 camadas consistentes (13 regras).

## Conexoes

- [[cluster-hub-programacao]]