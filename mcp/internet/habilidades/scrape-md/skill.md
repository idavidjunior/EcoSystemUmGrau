---
name: scrape-md
description: |
  Scrape local de paginas web para Markdown limpo, 100% stdlib (sem dependencias).
  Assimila os padroes centrais do Firecrawl com independencia total: extracao de
  conteudo principal (heuristica article/main), conversao HTML->Markdown,
  crawl BFS no mesmo dominio, cache TTL 24h e robots.txt conforme RFC 9309.
  Trigger keywords: "scrape", "raspar pagina", "extrair conteudo web",
  "converter para markdown", "crawl site", "scrape-md".
version: 1.0.0
---

# scrape-md — Scrape Web Local para Markdown

## Objetivo

Converter paginas web em Markdown limpo para consumo por LLMs e indexacao,
executando localmente sem servicos externos. Para paginas JavaScript pesadas,
o script detecta e recomenda fallback para Playwright/browser-mcp.

## Como usar

```bash
# Pagina unica -> JSON {url, titulo, markdown, avisos}
python mcp/internet/habilidades/scrape-md/scrape_md.py <url>

# Crawl BFS ate N paginas do mesmo dominio (rate limit 0.4s)
python mcp/internet/habilidades/scrape-md/scrape_md.py <url> --crawl 5

# Ignorar cache / gravar resultado
python mcp/internet/habilidades/scrape-md/scrape_md.py <url> --sem-cache
python mcp/internet/habilidades/scrape-md/scrape_md.py <url> --salvar saida.md
```

## Garantias de deteccao

- robots.txt correto (RFC 9309): ausencia = livre; regra explicita = respeitada;
  rede fora = erro classificado (nunca falso "proibido").
- Erros tipados: http_404, timeout, rede:<motivo>, tipo_nao_suportado, robots_proibe.
- Aviso pagina_aparenta_js quando ha pouco texto + scripts (SPA) -> usar Playwright.
- Charset do header com fallback para meta charset do corpo; limite 800KB.

## Estrategia de extracao

1. Candidatos de conteudo principal pontuados por densidade de texto
   (article > main); menor candidato descartado (< 200 chars).
2. Conversor HTML->Markdown proprio: titulos, listas, tabelas simples,
   blockquotes, codigo inline, links absolutos via urljoin.
3. Lixo removido: nav/footer/header/aside/script/style/form/svg/iframe.

## Limitacoes honestas

- Nao executa JavaScript (SPA chega vazia com aviso; usar navegacao-perita).
- Tabelas complexas viram linhas simplificadas.
- Anti-bot corporativo (Cloudflare hard) pode bloquear; nao contornar.

## Integracao ecossistema

- Cache em runtime/scrape_md_cache/ (sha1 da URL normalizada, TTL 24h).
- Complementa busca-web (estrategia) e navegacao-perita (paginas dinamicas).
- Origem dos padroes: Firecrawl v2 (AGPL) assimilado, zero dependencia.
