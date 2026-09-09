# 2026-09-09 - Decisão de persistência web — sqlite3 stdlib como camada de banco (bloco G)

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema (13 fases; FASES 1–4 entregues). O Ciclo 4 (IA como interface web) entregou chat web ligado ao `cognitive_core`; o bloco H está VALIDATED/3. O Ciclo 5 (Persistência web, bloco G) precisa provar estado local real persistido. Decisões externas pendentes no roadmap: PostgreSQL/Redis só "se o produto exigir". O ADR-003 manteve o ThreadingHTTPServer stdlib como backend e adiou uvicorn puro; este ADR fixa a camada de banco para os próximos ciclos web.
**Projeto:** EcoSystemUmGrau

## Decisão

Usar **sqlite3 (stdlib)** como camada de persistência web, operada por fachada `Dashboard` (migrations versionadas via `PRAGMA user_version`, escrita atômica commit/rollback, lock de escrita, WAL e chave estrangeira). Manter o **ThreadingHTTPServer** da stdlib (ADR-003) para servir o CRUD. PostgreSQL/Redis permanecem dependentes de necessidade real do produto.

## Alternativas consideradas

1. **Alternativa A — sqlite3 stdlib** — zero dependências novas, banco em arquivo local, ideal para lab/protótipo e estado local do ecossistema; migrations simples e versionadas; 25 checks passando com evidência.
2. **Alternativa B — PostgreSQL** — robusto e escalável, porém adiciona serviço externo, instalação e operação sem necessidade real no Ciclo 5; permanece como decisão externa "se o produto exigir".
3. **Alternativa C — Redis** — ótimo para cache/filas, não é banco relacional; fora do escopo do Ciclo 5.

## Por quê

O Ciclo 5 entregou evidência real: 25/25 checks passando com sqlite3, incluindo persistência verdadeira entre reinícios do servidor (S2 abre o mesmo banco em disco e recupera a nota), migrations v1→v2 aplicadas em ordem, transações com rollback automático e teste adversarial (rota inexistente, corpo inválido, método incorreto, erro interno 500). Pelo princípio da mudança mínima segura e REUTILIZAR > ADAPTAR > ESTENDER > CRIAR, a persistência permanece em stdlib sem decisão de stack externa. PostgreSQL/Redis serão reavaliados apenas se o produto final (Ciclo 8) exigir.