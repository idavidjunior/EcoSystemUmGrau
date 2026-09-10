# 2026-09-09 - Decisão de segurança web — middleware OWASP próprio em stdlib (bloco I)

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema. O Ciclo 6 (Segurança OWASP, bloco I) precisa aplicar proteções da lista OWASP sem adicionar dependências externas ao backend já decidido (ThreadingHTTPServer stdlib, ADR-003). Não há FastAPI/Flask instalado (ADR-003 manteve stdlib), e o ecossistema evita estrutura nova desnecessária.
**Projeto:** EcoSystemUmGrau

## Decisão

Implementar **SecurityMiddleware próprio como mixin reutilizável de `BaseHTTPRequestHandler`**, 100% stdlib, com: headers OWASP em toda resposta (X-Content-Type-Options nosniff, X-Frame-Options DENY, X-XSS-Protection, Referrer-Policy, CSP `default-src 'self'`), rate limit por IP (token bucket 50/min adjutável), limite de body (1MB), validação de Content-Type (JSON only → 415), sanitização de entrada (escape HTML + remoção de null bytes), tratamento de erros sem vazar internals, bloqueio de SQL injection e CORS configurável.

## Alternativas consideradas

1. **Alternativa A — Middleware próprio stdlib** — zero dependência, alinhado ao ADR-003, reutilizável e testável; 34 checks passando com evidência. Bucket de rate limit e refill são atributos de classe (não por instância, pois `BaseHTTPRequestHandler` processa a request ANTES do `__init__` da subclasse retornar, o que invalidava inicialização por handler) e o rate limit roda também em GET/DELETE/OPTIONS (não só em escrita).
2. **Alternativa B — Flask/FastAPI com extension de segurança** — pronto e maduro, porém contraria o ADR-003 (stdlib mantida) e adiciona dependência e estrutura nova sem necessidade real no Ciclo 6.
3. **Alternativa C — OnlyHTTPS / nginx externo** — desloca a proteção para infraestrutura externa; fora do escopo do lab servido pela própria aplicação.

## Por quê

O Ciclo 6 entregou evidência real: 34/34 checks passando, incluindo adversarial (body 2MB → conexão fechada/413; 250 requests → rate limit bloqueia; body 2MB sobre Content-Type aceito; `/api/explode` retorna 500 sem vazar Traceback/File; sanitização de XSS com null bytes; rota inexistente mantém headers). Pelo princípio da mudança mínima segura e REUTILIZAR > ADAPTAR > ESTENDER > CRIAR, a segurança fica no próprio servidor sem framework novo. A pendência registrada no roadmap (ADR-006) é encerrada por este documento.