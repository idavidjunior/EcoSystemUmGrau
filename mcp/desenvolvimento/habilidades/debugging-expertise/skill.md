---
name: debugging-expertise
description: |
  Debugging expert: deteccao de bugs, crashes, duplicacao, UI disfuncional, code smells, links quebrados.
  Autopesquisa, autocorrecao, sem tentativas redundantes. Ferramentas: breakpoints, logs, memory profiling, static analysis, sanitizers.
  Trigger keywords: debug, depurar, crash, bug, erro, falha, duplicado, code smell, UI quebrada, link quebrado, memory leak, performance, stack trace, root cause.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, WebSearch, WebFetch, Task
version: 1.0.0
---

# Debugging Expertise — Perícia em Depuração

## Objetivo

Transformar o ecossistema em perito em encontrar e corrigir falhas: crashes, bugs lógicos, código duplicado, interface disfuncional, sujeira técnica (code smells), links quebrados, memory leaks, race conditions. Capacidade de autopesquisa e autocorreção sem tentativas redundantes.

---

## 1. METODOLOGIA CIENTÍFICA DE DEBUG

### 1.1 Ciclo Científico (Obrigatório)
```
OBSERVAR → HIPOTETIZAR → TESTAR → VALIDAR → CORRIGIR → REGISTRAR
```
**Nunca** pule etapas. Cada hipótese deve ser falsificável e testada isoladamente.

### 1.2 Princípios Inquebráveis
- **Uma hipótese por vez** — não teste múltiplas causas simultaneamente
- **Reproduzir antes de corrigir** — sem reprodução, não há bug confirmado
- **Mudança mínima** — corrija a causa raiz, não o sintoma
- **Validar a correção** — teste de regressão obrigatório
- **Registrar aprendizado** — `memory_engine.py add` + `conhecimento/aprendizados/`

### 1.3 Classificação de Criticidade (para priorização)
| Nível | Critérios | SLA |
|-------|-----------|-----|
| **P0 - Crítico** | Crash, data loss, security, produção parada | Imediato |
| **P1 - Alto** | Funcionalidade core quebrada, performance degradada severa | < 4h |
| **P2 - Médio** | Bug não-bloqueante, UI inconsistente, warning | < 24h |
| **P3 - Baixo** | Code smell, duplicação, tech debt, melhoria | Próxima sprint |

---

## 2. FERRAMENTAS DE DEBUG (Stack Completa)

### 2.1 Debuggers Interativos
| Linguagem | Ferramenta | Comando-chave |
|-----------|------------|---------------|
| Python | `pdb` / `ipdb` / `debugpy` | `breakpoint()`, `python -m pdb script.py` |
| JavaScript/Node | `ndb` / Chrome DevTools / VS Code | `node --inspect-brk`, `debugger` |
| TypeScript | `ts-node-dev` + VS Code | `launch.json` config |
| Go | `delve` | `dlv debug` |
| Rust | `gdb` / `lldb` / `rust-gdb` | `cargo run -- --debug` |
| Java | `jdb` / IDE | `-agentlib:jdwp` |
| C/C++ | `gdb` / `lldb` | `gdb ./bin` |

### 2.2 Logging Estruturado (Obrigatório)
```python
# Python - structlog padrão do ecossistema
import structlog
log = structlog.get_logger()
log.error("falha_critica", modulo="auth", user_id=123, erro=str(e), stack=traceback.format_exc())
```

```javascript
// JS - pino padrão
const pino = require('pino')({ level: process.env.LOG_LEVEL || 'info' });
pino.error({ err, context: 'payment', userId }, 'falha ao processar');
```

**Níveis:** `trace` < `debug` < `info` < `warn` < `error` < `fatal`
**Sempre** incluir: `timestamp`, `level`, `service`, `trace_id`, `span_id`

### 2.3 Análise Estática (Lint/Typecheck/Semgrep)
| Ferramenta | Uso | Comando |
|------------|-----|---------|
| `ruff` / `mypy` | Python lint + typecheck | `ruff check . && mypy .` |
| `eslint` + `tsc` | JS/TS lint + typecheck | `eslint . && tsc --noEmit` |
| `semgrep` | Security/bug patterns | `semgrep scan --config=auto .` |
| `sonarqube` | Quality gate | CI integration |
| `bandit` | Python security | `bandit -r .` |
| `gosec` | Go security | `gosec ./...` |
| `cargo clippy` | Rust lint | `cargo clippy -- -D warnings` |

### 2.4 Sanitizers & Dynamic Analysis
| Tipo | Ferramenta | Linguagens |
|------|------------|------------|
| AddressSanitizer (ASan) | `-fsanitize=address` | C/C++, Rust, Go |
| ThreadSanitizer (TSan) | `-fsanitize=thread` | C/C++, Go |
| MemorySanitizer (MSan) | `-fsanitize=memory` | C/C++ |
| LeakSanitizer (LSan) | Built-in ASan | C/C++ |
| Valgrind | Memcheck, Helgrind, DRD | C/C++, Python (via `--tool=memcheck`) |
| `tracemalloc` | Python memory | `python -X tracemalloc=5 script.py` |
| `objgraph` | Python object leaks | `pip install objgraph` |

### 2.5 Profiling & Performance
| Ferramenta | Foco | Comando |
|------------|------|---------|
| `py-spy` | Python CPU profiling | `py-spy record -o profile.svg -- python script.py` |
| `scalene` | Python CPU+Memory+GPU | `scalene script.py` |
| `cProfile` | Python built-in | `python -m cProfile -o stats.prof script.py` |
| `node --inspect` + `clinic.js` | Node.js | `clinic doctor -- node script.js` |
| `pprof` | Go/Rust | `go tool pprof` |
| `perf` | Linux system-wide | `perf record -g -- python script.py` |
| `flamegraph` | Visualização | `flamegraph.pl` |

### 2.6 Memory Leak Detection
```bash
# Python
python -X tracemalloc=25 script.py
# Depois: tracemalloc.take_snapshot().filter_traces(...).statistics('lineno')

# Node.js
node --inspect --trace-gc script.js
# Chrome DevTools → Memory → Heap snapshots (3x: baseline, load, after GC)

# Go
go test -memprofile=mem.prof -run=XXX ./...
go tool pprof mem.prof

# Valgrind (C/C++)
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./bin
```

### 2.7 Race Condition & Concurrency
| Ferramenta | Uso |
|------------|-----|
| ThreadSanitizer (TSan) | Data races em C/C++/Go/Rust |
| `go test -race` | Go race detector |
| `helgrind` (Valgrind) | POSIX threads races |
| `drd` (Valgrind) | Thread API misuse |
| `loom` (Rust) | Model checking concurrency |
| `py-spy` + `threading` | Python GIL contention |

---

## 3. PADRÕES DE FALHA E DETECÇÃO AUTOMÁTICA

### 3.1 Crashes & Exceções Não Tratadas
```python
# Padrão: try/except vazio ou genérico
try:
    risco()
except:  # ERRO: engole tudo
    pass

# Correto: específico + log + re-raise ou tratamento
try:
    risco()
except SpecificError as e:
    log.error("falha_especifica", erro=str(e))
    raise  # ou handle graciosamente
```

**Detecção automática:** `semgrep --config=p/python --config=p/ci`

### 3.2 Null/Undefined Reference
```typescript
// TypeScript: strictNullChecks + optional chaining
const user = getUser();
console.log(user?.profile?.name ?? 'anon'); // seguro

// Python: Optional + guard clause
def process(user: Optional[User]) -> Result:
    if user is None:
        return Err("user_required")
    return Ok(user.process())
```

**Detecção:** `mypy --strict`, `tsc --strictNullChecks`

### 3.3 Resource Leaks (files, sockets, DB connections)
```python
# ERRADO
f = open('file.txt')
data = f.read()
# f nunca fechado se exceção

# CORRETO: context manager
with open('file.txt') as f:
    data = f.read()

# Pool connections
with pool.connection() as conn:
    with conn.cursor() as cur:
        cur.execute(...)
```

**Detecção:** `ruff` (PY-PLACEHOLDER), `pylint` (R1732), `bandit` (B108)

### 3.4 Código Duplicado (DRY Violation)
```bash
# Detecção automática
# Python
jscpd --pattern "*.py" --min-lines 5 --min-tokens 70 .
# OU
pylint --disable=all --enable=duplicate-code .

# JS/TS
jscpd --pattern "*.{js,ts,tsx}" --min-lines 5 .
# ESLint
npm install eslint-plugin-import eslint-plugin-sonarjs
# rule: sonarjs/no-duplicate-code
```

**Métrica:** > 6 linhas idênticas = candidato a extração

### 3.5 Code Smells (Catálogo)
| Smell | Sinal | Ferramenta |
|-------|-------|------------|
| **Long Function** | > 50 linhas / > 4 params | `ruff` (PLR0912), `sonarjs` |
| **Large Class** | > 500 linhas / > 10 métodos | `pylint` (R0901) |
| **Long Parameter List** | > 4 parâmetros | `ruff` (PLR0913) |
| **Data Clumps** | Mesmo grupo de params repetido | Manual / `sonarjs` |
| **Primitive Obsession** | Excesso de `str`/`int` para domínio | Type-driven design |
| **Switch Statements** | `if/elif` chains / `match` longos | Polymorphism/Strategy |
| **Speculative Generality** | Código "para o futuro" não usado | YAGNI + delete |
| **Dead Code** | Unused imports, functions, vars | `ruff` (F401, F841), `vulture` |
| **God Object** | Uma classe faz tudo | Coupling metrics |
| **Feature Envy** | Método usa mais dados de outra classe | Move method |

### 3.6 UI Disfuncional (Frontend)
| Problema | Detecção | Ferramenta |
|----------|----------|------------|
| Layout shift (CLS) | `layout-shift` entries | Lighthouse, Web Vitals |
| Unresponsive interactions | `longtask` > 50ms | `web-vitals`, `PerformanceObserver` |
| Memory growth | Heap snapshots diff | Chrome DevTools Memory |
| Event listener leaks | `addEventListener` sem `remove` | `why-did-you-render` (React) |
| Unnecessary re-renders | React DevTools Profiler | `why-did-you-render` |
| Broken accessibility | `axe-core` violations | `npm test -- --watch=false` + axe |
| CSS conflicts | Duplicate selectors, specificity wars | `stylelint`, `css-stats` |

### 3.7 Links Quebrados & Referências Mortas
```bash
# Markdown/HTML
markdown-link-check **/*.md
# HTML
linkchecker http://localhost:3000
# API endpoints
swagger-codegen validate -i openapi.yaml
# Imports (Python)
pyflakes . | grep "imported but unused"
# Imports (JS/TS)
npm run lint -- --rule 'import/no-unresolved: error'
# Require/import paths
madge --circular --extensions js,ts src/
```

### 3.8 Configuração & Environment
| Problema | Detecção |
|----------|----------|
| Secrets em código | `gitleaks`, `truffleHog`, `semgrep --config=p/secrets` |
| Config hardcoded | `grep -r "localhost\|127.0.0.1\|password\|api_key" --include="*.py" --include="*.js"` |
| Env vars ausentes | `python -c "import os; [print(k) for k in ['VAR1','VAR2'] if not os.getenv(k)]"` |
| Version mismatch | `pip check`, `npm audit`, `cargo audit` |

---

## 4. PROTOCOLO DE AUTO-PESQUISA E AUTOCORREÇÃO

### 4.1 Algoritmo de Debug Autônomo
```python
def debug_autonomo(sintoma: str, codigo: str) -> Correcao:
    # 1. CLASSIFICAR
    categoria = classificar(sintoma)  # crash, logic, perf, ui, config
    
    # 2. COLETAR EVIDÊNCIAS (não assumir)
    evidencias = coletar_evidencias(codigo, categoria)
    # - stack trace completo
    # - logs estruturados
    # - estado de variáveis no momento
    # - diff recente (git log -p)
    # - ambiente (versões, OS, config)
    
    # 3. FORMULAR HIPÓTESES ORDENADAS (probabilidade x impacto)
    hipoteses = gerar_hipoteses(evidencias, categoria)
    # Priorizar: mais provável E maior impacto se verdadeiro
    
    # 4. TESTAR UMA POR VEZ (ciclo científico)
    for h in hipoteses:
        teste = desenhar_teste_minimo(h)
        resultado = executar_teste(teste)
        if resultado.confirma(h):
            causa_raiz = h
            break
        registrar_tentativa(h, resultado)  # evita repetição
    
    # 5. CORRIGIR CAUSA RAIZ (mudança mínima)
    correcao = gerar_correcao_minima(causa_raiz)
    aplicar(correcao)
    
    # 6. VALIDAR (regressão + caso original)
    assert test_original_passa()
    assert test_regressao_passa()
    assert nao_quebrou_outros()
    
    # 7. REGISTRAR APRENDIZADO
    memory_engine.add(
        task=f"Debug: {sintoma}",
        summary=f"Causa: {causa_raiz}. Correção: {correcao}. Evitou: {hipoteses_descartadas}",
        kind="erro",
        tags=["debug", categoria, "root-cause"]
    )
    
    return correcao
```

### 4.2 Base de Conhecimento de Padrões (Auto-expansível)
O ecossistema deve manter e expandir `conhecimento/debug-patterns/` com:

```
conhecimento/debug-patterns/
├── crash-patterns.md          # Stack traces → causas comuns
├── memory-leak-patterns.md    # Sintomas → fontes típicas
├── race-condition-patterns.md # Interleavings → detecção
├── ui-bug-patterns.md         # Visual/behavior → causa
├── config-error-patterns.md   # Env/secret/config → fix
├── duplicate-code-patterns.md # Estruturas → refatoração
├── code-smell-catalog.md      # Smell → remediação
└── broken-link-patterns.md    # Referência → reparo
```

**Auto-atualização:** Após cada debug bem-sucedido, o agente DEVE:
1. Verificar se padrão já existe em `debug-patterns/`
2. Se novo: criar entrada com `sintoma`, `causa_raiz`, `correcao`, `prevencao`
3. Se existe: reforçar (`memory_engine.reinforce`) e expandir se variante nova

### 4.3 Prevenção de Tentativas Redundantes
```python
# Cache de tentativas por sessão + memória persistente
tentativas_registradas = memory_engine.query(
    kind="erro", 
    tags=["debug", "tentativa"],
    text=sintoma
)

# Antes de testar hipótese H:
if any(h.descricao == H.descricao for h in tentativas_registradas):
    pular(H)  # já tentado, não repetir
    
# Registrar tentativa (sucesso ou falha)
memory_engine.add(
    task=f"Tentativa debug: {H.descricao}",
    summary=f"Hipótese: {H}. Resultado: {resultado}. Evidência: {evidencia}",
    kind="erro",
    tags=["debug", "tentativa", categoria]
)
```

---

## 5. FERRAMENTAS ESPECÍFICAS DO ECOSSISTEMA

### 5.1 Scripts de Debug Integrados
```bash
# Health check completo do projeto
python scripts/debug_health_check.py --project .

# Análise de duplicação
python scripts/find_duplicates.py --min-lines 6 --exclude tests/

# Code smell detector
python scripts/detect_smells.py --threshold medium

# Broken link checker
python scripts/check_links.py --recursive --external

# Memory leak hunter (Python)
python scripts/memory_leak_hunter.py --attach-pid <PID> --duration 60

# Race condition stress test
python scripts/race_stress.py --target module.py --iterations 10000
```

### 5.2 Integração com Runtime (Obrigatório)
Todo debug passa pelo pipeline:
```
runtime_boot.py → runtime_kernel.py (validação) → runtime_context.py (contexto)
→ debugging-expertise (execução) → runtime_auditor.py (auditoria) → memory_engine (aprendizado)
```

### 5.3 Comando Unificado de Debug
```bash
# Uso: python scripts/debug.py <alvo> [--categoria crash|logic|perf|ui|config|dup|smell|link]
python scripts/debug.py ./src/auth.py --categoria crash
python scripts/debug.py ./frontend --categoria ui
python scripts/debug.py . --categoria dup --min-lines 10
```

---

## 6. CHECKLISTS DE DEBUG POR CATEGORIA

### 6.1 Crash / Exception
- [ ] Stack trace completo capturado (não truncado)
- [ ] Variáveis locais no frame do crash inspecionadas
- [ ] Versão exata do código reproduzida (git commit)
- [ ] Ambiente replicado (deps, OS, config)
- [ ] Mínimo reproduzir (reduzir input até falhar)
- [ ] Bisect se regressão (git bisect)
- [ ] Fix ataca causa raiz, não sintoma
- [ ] Test de regressão adicionado

### 6.2 Bug Lógico / Comportamento Incorreto
- [ ] Spec/requisito claro (o que DEVERIA acontecer)
- [ ] Input exato que produz bug
- [ ] Estado antes/durante/depois logado
- [ ] Hipóteses priorizadas por evidência
- [ ] Uma hipótese testada por vez
- [ ] Edge cases cobertos (null, empty, boundary, concurrent)
- [ ] Property-based testing se aplicável

### 6.3 Performance / Memory Leak
- [ ] Baseline medido (antes da mudança)
- [ ] Profiler rodado (CPU + Memory)
- [ ] Hotspots identificados (> 5% tempo total)
- [ ] Alocações desnecessárias rastreadas
- [ ] GC pressure analisado (frequência, duração)
- [ ] Fix medido vs baseline (speedup %)

### 6.4 UI / Frontend
- [ ] Steps to reproduce documentados
- [ ] Browser/device matrix testado
- [ ] Console errors capturados (zero tolerance)
- [ ] Network tab: failed requests, timing
- [ ] React/Vue DevTools: component tree, props, state
- [ ] Accessibility: axe-core zero violations
- [ ] Visual regression: screenshot diff

### 6.5 Código Duplicado
- [ ] `jscpd` / `pylint` rodado
- [ ] Clusters de duplicação > 6 linhas identificados
- [ ] Abstração comum extraída (função, classe, módulo)
- [ ] Testes das abstrações passam
- [ ] Callers migrados para abstração
- [ ] Dead code removido

### 6.6 Code Smells
- [ ] `ruff` / `eslint` / `sonarqube` clean
- [ ] Métricas: CC < 10, LOC/fn < 50, params < 4
- [ ] Nomes expressivos (sem abreviações obscuras)
- [ ] Sem comentários que explicam "o quê" (código claro)
- [ ] Princípios SOLID verificados

### 6.7 Links Quebrados / Referências
- [ ] `markdown-link-check` / `linkchecker` clean
- [ ] Imports internos resolvem
- [ ] API endpoints respondem (2xx)
- [ ] Assets (imagens, fonts, CSS) carregam
- [ ] Redirects funcionam (não 404)

---

## 7. REGRAS DE OURO DO DEBUG NO ECOSSISTEMA

1. **NUNCA debugue às cegas** — sempre colete evidências primeiro
2. **UMA hipótese por vez** — teste isolado, registre resultado
3. **Reproduza SEMPRE** — sem repro, não há bug
4. **Fix mínimo** — cause raiz, não sintoma
5. **Valide regressão** — teste original + testes existentes
6. **Registre TUDO** — memória episódica + `conhecimento/debug-patterns/`
7. **Compartilhe padrões** — evite que outros repitam seu debug
8. **Automatize detecção** — lint, tests, CI gates para prevenir recorrência
9. **Priorize por impacto** — P0/P1 primeiro, tech debt depois
10. **Celebre o aprendizado** — cada debug bem-sucedido fortalece o ecossistema

---

## 8. INTEGRAÇÃO COM OUTRAS SKILLS

| Skill | Sinergia |
|-------|----------|
| `search-first` | Pesquisar soluções conhecidas antes de debugar |
| `refactoring-patterns` | Aplicar ao corrigir code smells/duplicação |
| `code-review` | Checklist de debug em PRs |
| `technical-debt` | Registrar debt encontrado durante debug |
| `observability-stack` | Logs/metrics/traces para evidências |
| `resilience-engineering` | Chaos testing para achar falhas latentes |
| `tdd-workflow` | Testes de regressão pós-fix |
| `secure-coding` | Sanitizers para bugs de segurança |
| `performance-testing` | Baseline e validação de perf fixes |
| `legacy-modernization` | Debug em código legado |
| `fundamentos-computacao` | **Base obrigatória**: ISA reference (latência/throughput), ELF parsing, IEEE 754, stack frames, calling convention, bitwise ops — essenciais para crash analysis, memory leaks, race conditions, performance debugging |

---

## 9. EXEMPLOS DE USO (Triggers)

```
"debugar crash no módulo de pagamento"
"encontrar memory leak no worker de processamento"
"detectar código duplicado no projeto"
"UI não responde no mobile — investigar"
"links quebrados na documentação"
"race condition no cache distribuído"
"code smell: função de 200 linhas"
"configuração de produção falhando silenciosamente"
"exception não tratada no endpoint /api/v1/users"
"performance degradou 40% após deploy"
```

---

## 10. EVOLUÇÃO CONTÍNUA

Esta skill é **viva**. Após cada debug:
1. **Atualize** `conhecimento/debug-patterns/` com novo padrão ou variação
2. **Reforce** memórias relacionadas (`memory_engine.reinforce`)
3. **Melhore** scripts em `scripts/debug_*.py` se gaps encontrados
4. **Expanda** checklists se nova categoria de falha descoberta
5. **Compartilhe** via `memory_engine.add` para todo o ecossistema

**Meta:** Zero bugs recorrentes, zero tentativas redundantes, expertise cumulativa.