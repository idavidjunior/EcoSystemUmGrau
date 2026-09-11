# RUNBOOK — Operação Web do Ecossistema

Categoria: padrao
Projeto: EcoSystemUmGrau
Dominio: Engenharia Web

## Propósito

Guia de operação da trilha web do ecossistema: como rodar os labs, executar
a suíte de validação, subir o produto integrado, medir Core Web Vitals e
entender o pipeline de CI. Segue o princípio: qualquer lab roda com um
comando documentado, sem depender de memória do operador.

## Stack

- Python 3.12 (stdlib: http.server, sqlite3, threading, asyncio).
- `websockets` (Ciclos 3, 4 e 8 — WS/IA).
- `httpx` (Ciclo 1 — transporte do teste).
- `playwright` (Ciclos 7 e 8 — medição CWV; opcional nos ciclos).
- Serviço MCP `mcp-memoria` (Ciclo 4 — busca no acervo do ecossistema).

## Conteúdo do diretório

```
conhecimento/web/
├── README.md               <- mapa de competências (blocos A–N)
├── adrs/                   <- decisões de arquitetura web
├── labs/                   <- micro-labs executados e validados
├── benchmarks/             <- métricas medidas (CWV, suite, etc.)
├── RUNBOOK-OPERACAO-WEB.md <- este arquivo
└── run_suite.py            <- build/run reproduzível (Ciclo 9)
```

## Como rodar a suíte completa (recomendado)

```bash
python conhecimento/web/run_suite.py
```

Executa os 5 labs determinísticos (Ciclos 1, 2, 3, 5 e 6) em sequência,
cada um no próprio diretório. O Ciclo 6 sobe e derruba o servidor sozinho.
Saída esperada:

```
  STATUS: OK (5 labs aprovados, 0 falhas, 0 skips)
```

Exit code 0 = sucesso. Cada execução grava
`conhecimento/web/benchmarks/ciclo-9-run-suite.json`.

Para incluir os labs de IA e Playwright (Ciclos 4, 7 e 8 — exige chave de
IA ativa e playwright instalado):

```bash
python conhecimento/web/run_suite.py --tudo
```

## Como rodar um lab isolado

Todos os labs seguem o padrão: teste executado dentro da pasta do lab.

```bash
# Ciclo 1 — Fundamentos (servidor stdlib)
python conhecimento/web/labs/ciclo-1-fundamentos/test_server.py

# Ciclo 2 — Backend estruturado
python conhecimento/web/labs/ciclo-2-backend-estruturado/test_server.py

# Ciclo 3 — WebSocket realtime
python conhecimento/web/labs/ciclo-3-websocket/test_ws.py

# Ciclo 4 — Chat IA (requer MCP mcp-memoria + chave de IA)
python conhecimento/web/labs/ciclo-4-ia-chat/test_ia_chat.py

# Ciclo 5 — Persistência sqlite3
python conhecimento/web/labs/ciclo-5-persistencia-web/test_persistencia.py

# Ciclo 6 — Segurança OWASP (NÃO é auto-contido: suba o servidor antes)
cd conhecimento/web/labs/ciclo-6-seguranca-owasp
python server.py 8096
# em outro terminal:
python conhecimento/web/labs/ciclo-6-seguranca-owasp/test_seguranca.py 8096
# derrube o servidor ao terminar (Ctrl+C)

# Ciclo 7 — Performance/a11y (requer playwright)
cd conhecimento/web/labs/ciclo-7-performance-acessibilidade
python test_performance.py

# Ciclo 8 — Produto integrado (auto-contido: HTTP+WS+sqlite+IA)
cd conhecimento/web/labs/ciclo-8-produto-quadro-notas
python test_produto.py
```

## Como subir o produto integrado (Ciclo 8)

```bash
python conhecimento/web/labs/ciclo-8-produto-quadro-notas/server.py
# http://127.0.0.1:8098 | ws://127.0.0.1:8099/ws
```

Portas: HTTP 8098, WebSocket 8099 (override por argumentos posicionais:
`python server.py [:porta] [:porta_ws]`). O servidor sobe WS em thread
asyncio separada e o produto usa sqlite persistente em `data/produto.db`.

## Como medir Core Web Vitals

```bash
cd conhecimento/web/labs/ciclo-8-produto-quadro-notas
python medir_cwv.py [porta]
```

Salva em `conhecimento/web/benchmarks/ciclo-8-cwv.json`. Requer o servidor
do Ciclo 8 de pé e playwright com chromium instalado. Bandas: LCP ≤ 2,5s,
INP ≤ 200ms, CLS ≤ 0,1 (Good).

## Como funciona o CI (publicação via pipe existente)

`.github/workflows/web-ci.yml` roda em todo push e pull request:

1. checkout do repositório + Python 3.12.
2. `pip install httpx websockets`.
3. `python conhecimento/web/run_suite.py` (suíte determinística).

Não usa Docker (ausente no ambiente); GitHub Actions é o pipe existente do
ecossistema. O CI é o garante de que nenhum lab determinístico regride em
mudanças futuras.

## Troubleshooting

- "Servidor não encontrado em 127.0.0.1:8096": o teste do Ciclo 6 precisa
  do servidor de pé; rode `python server.py 8096` na pasta do lab antes.
- Falha no Ciclo 3/4/8 por `ModuleNotFoundError: websockets`: instale
  `pip install websockets`. Mesmo caso para `httpx` (Ciclo 1).
- Ciclo 4 falha por timeout/busca: o serviço MCP de memória precisa estar
  ativo e a chave de IA configurada em `scripts/.env`.
- Ciclo 7/8 com erro de Playwright: `pip install playwright` e
  `playwright install chromium`.
- `run_suite.py` com "--tudo" e Ciclo 8 demorando: `TIMEOUT_IA_S=90` do
  servidor; a LLM real responde em poucos segundos quando a chave está OK.
- Porta ocupada: os testes de cada lab escolhem porta livre interna; o
  Ciclo 6 usa 8096 fixa (troque pelo argumento, se precisar).