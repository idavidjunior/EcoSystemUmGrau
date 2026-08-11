---
tipo: padrao
tags: [debug, expertise, methodology, tools, patterns, automation, self-research, self-correction]
data: 2026-08-09
contexto: "Usuário solicitou que o ecossistema aprendesse tudo sobre debugar programas: ferramentas necessárias, auto-pesquisa, autocorreção eficiente, sem tentativas redundantes. Perícia em encontrar falhas, crashes, código duplicado, UI disfuncional, sujeira técnica, links quebrados."
decisao: "Criada skill debugging-expertise completa em mcp/desenvolvimento/habilidades/debugging-expertise/skill.md com metodologia científica, catálogo de ferramentas por linguagem, padrões de falha com detecção automática, protocolo de auto-pesquisa/autocorreção com cache de tentativas, checklists por categoria, e 7 scripts de debug integrados."
impacto: "Ecossistema agora tem capacidade nativa de debug perito: health check completo, detecção duplicação (pylint/jscpd/generic), code smells (ruff/pylint/radon/eslint), links quebrados (markdown/html/imports), memory leaks (tracemalloc/gc), race conditions (stress testing), comando unificado. Auto-aprendizado via memory_engine + debug-patterns."
---

# Aprendizado: Debugging Expertise Skill

## Resumo

Implementada expertise completa de debugging no EcoSystemUmGrau através de:

### 1. Skill Declarativa (`mcp/desenvolvimento/habilidades/debugging-expertise/skill.md`)
- Metodologia científica obrigatória (Observar → Hipotetizar → Testar → Validar → Corrigir → Registrar)
- Classificação de criticidade P0-P3 com SLA
- Ferramentas por linguagem: debuggers, logging estruturado, análise estática, sanitizers, profilers, memory leak detectors, race detectors
- Padrões de falha catalogados: crashes, null refs, resource leaks, duplicação, 10 code smells, UI disfuncional, links quebrados, config/secrets
- Protocolo de auto-pesquisa/autocorreção com algoritmo que evita tentativas redundantes via cache persistente
- Base de conhecimento auto-expansível em `conhecimento/debug-patterns/`
- Checklists por categoria (crash, logic, perf, ui, dup, smell, link)
- Integração com outras skills (search-first, refactoring, code-review, tech-debt, observability, etc.)

### 2. Scripts de Debug Integrados (`scripts/`)
- `debug_health_check.py` - Health check completo (Python: ruff, mypy, pytest, bandit, pylint, vulture, pyflakes; JS/TS: eslint, tsc, jest, npm audit, jscpd, madge; Generic: git, gitleaks, large files, TODO/FIXME)
- `find_duplicates.py` - Detecção multiplataforma (pylint para Python, jscpd para JS/TS, hash genérico fallback)
- `detect_smells.py` - Code smells (ruff + pylint + radon CC/MI + vulture para Python; eslint para JS/TS)
- `check_links.py` - Links quebrados assíncrono (Markdown, HTML, imports Python/JS/TS, locais e externos)
- `memory_leak_hunter.py` - Memory leaks Python (tracemalloc + psutil + gc.get_objects tracking)
- `race_stress.py` - Race conditions via stress testing multi-thread com detecção de data races
- `debug.py` - Comando unificado que orquestra tudo

### 3. Integração com Runtime
- Passa pelo pipeline: runtime_boot → kernel → context → debugging-expertise → auditor → memory_engine
- Registra aprendizados automaticamente em `memory_engine` (kind=erro/padrao) e `conhecimento/debug-patterns/`
- Cache de tentativas redundantes via `memory_engine.query(kind="erro", tags=["debug", "tentativa"])`
- Checkpoint salvo: `20260809_084442`

### 4. Próximos Passos
- Expandir `conhecimento/debug-patterns/` com padrões reais encontrados
- Adicionar suporte a mais linguagens (Go, Rust, Java, C++)
- Integrar com CI/CD para gate de qualidade automático
- Criar dashboard de métricas de debug (MTTR, recorrência, categorias)
