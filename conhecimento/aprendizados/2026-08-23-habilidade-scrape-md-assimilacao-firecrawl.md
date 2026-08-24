# Habilidade scrape-md — Assimilação do Firecrawl com Independência

## Metadados
- tipo: padrao
- tags: [scrape-md, firecrawl, web-scraping, markdown, stdlib, independencia, mcp-internet]
- data: 2026-08-23
- contexto: Usuário pediu que o EcoSystemUmGrau aprenda e assimile tecnologias externas com propósito de INDEPENDÊNCIA. Investigado o Firecrawl (org firecrawl/firecrawl, 171k estrelas, AGPL-3.0) e decidido NÃO integrar o serviço; assimilar os padrões centrais em habilidade própria Python 100% stdlib.

## Decisão
Criada `mcp/internet/habilidades/scrape-md/` (scrape_md.py + skill.md), v1.0:
1. **Extração de conteúdo principal**: Analisador (HTMLParser) pontua candidatos article/main por densidade de texto; alvo = (tag, contador_global_de_abertura).
2. **Conversor HTML→Markdown próprio**: títulos h1-h6, listas, tabelas simples, blockquote, code, links absolutos via urljoin; IGNORAR = nav/footer/script/style/etc.
3. **Crawl BFS** mesmo domínio com rate limit 0.4s e cache.
4. **Cache sha1(url normalizada).json TTL 24h** em runtime/scrape_md_cache/, escrita atômica (tmp+replace).
5. **robots.txt RFC 9309**: ausência (404) = livre; regra explícita = respeitada; rede fora = indeterminado (segue para erro real); file:// pula verificação.

## Descobertas críticas de detecção (aprendizado principal)
- **BUG do robotparser nesta máquina**: `RobotFileParser.read()` com HTTPError 404 seta `disallow_all=True` (bloqueia TUDO). O CPython deveria tratar 400-499 como allow_all, mas o comportamento empírico foi o contrário. Correção: baixar robots.txt manualmente com urllib e parsear com `rp.parse()`. Falso "robots proibe" em example.org revelou isso no primeiro teste real.
- **Sincronia entre duas passadas do mesmo HTML**: contadores globais divergem se uma passada ignora tags que a outra conta. Solução: Conversor incrementa `_n` em TODA starttag (inclusive ignoradas) antes dos checks, casando `(tag, n)` com o alvo do Analisador.
- **Cache por URL não-normalizada**: example.org vs example.org/ gerava cache miss silencioso. Normalizar URL (barra final, esquema default https) antes de tudo.
- **main() descartava avisos**: resultado intermediário tinha `avisos` mas a saída final não propagava. Sempre propagar metadados até a borda.

## Testes adversariais executados
- DNS inexistente → erro classificado `rede:getaddrinfo failed` (não mais falso robots_proibe).
- SPA sintética local → aviso `pagina_aparenta_js:use_playwright_ou_browser_mcp`.
- Cache hit segunda chamada → avisos ["cache"], mesma saída.
- Crawl real blog.python.org --crawl 3 → markdown limpo com títulos/links absolutos.
- Server MCP internet validado: initialize + tools/list = 6 tools, scrape-md presente. Manifesto regenerado: 112 habilidades.

## Impacto
- Ecossistema ganha coleta web local sem serviço externo: scrape único + crawl + cache.
- Padrão de assimilação replicável: investigar repo externo → extrair núcleo conceitual → reimplementar stdlib → testes adversariais → integrar ao MCP por domínio.
- Limitações honestas registradas na skill.md: sem JS (fallback Playwright/navegacao-perita), tabelas simplificadas, anti-bot corporativo não contornado.

## Pendências herdadas
- JunkScanner #1 (SQLite dedup), #3 (export CSV/JSON), #4 (widget), #5 (Shizuku).
