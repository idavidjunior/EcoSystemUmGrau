---
id: spec-evolution-radar
versao: 0.1.0
status: proposta
componente: scripts/evolution_radar_collect.py
tags: [evolucao, radar, autonomia, pesquisa, auto-evolucao]
data: 2026-08-14
---

# Evolution Radar — Banco de Pesquisa para Auto-Evolução Curada

## Objetivo
Criar um sistema passivo e contínuo que descobre, filtra, valida e propõe melhorias evolutivas para o EcoSystemUmGrau — **sem intervenção manual constante**, **com permissão do administrador**, **em pacotes versionados** e **sem quebrar a arquitetura**.

---

## Requisitos

1. **Coleta passiva** de fontes confiáveis (GitHub releases, dependabot, feeds curados) — 100% stdlib, sem API keys obrigatórias.
2. **Filtro de relevância automático**: só o que serve ao nosso stack (Python stdlib, Android puro, LER, MCP, OpenCode, vigilante, skills, Constituição).
3. **Análise de integração simulada**: roda `preflight_check.py` + `sync_rules.py audit` em modo dry-run antes de propor.
4. **Banco de propostas versionado**: cada proposta é um arquivo markdown com ganho, esforço, risco, breaking, POC.
5. **Ciclo controlado pelo vigilante**: intervalo mínimo **3-4 horas** (configurável, padrão 4h), só roda se houver permissão do administrador.
6. **Entrega em pacotes**: agrupa propostas validadas em "pacote de evolução" (ex: `evolution-pack-2026-08-14-v1.json`) — não aplica uma a uma.
7. **Apresentação ao administrador**: relatório claro "Tem X propostas no pacote Y. Aplicar? [sim/nao/ver]".
8. **Rollback automático**: se pacote aplicado quebrar preflight, restaura estado anterior via `persistencia.ps1`.

---

## Restrições

- **Zero dependências externas** além do que já existe no ecossistema (requests se já tiver, senão urllib).
- **Não modifica código diretamente** — só gera propostas e pacotes; aplicação passa pelo gate (`persistencia.ps1`).
- **Respeita as 3 camadas de regras**: Constituição → AGENTS.md → Deployed. Qualquer proposta que cause divergência é rejeitada.
- **Não cria Frankenstein**: proposta que exija wrapper > 50 linhas, nova dep externa, ou mudar estrutura de pastas = rejeitada.
- **Fail-soft total**: se coletor falha, loga e continua; nunca trava o vigilante.
- **Admin permission obrigatória**: variável de ambiente `EVOLUTION_RADAR_ADMIN=1` ou arquivo `.evolution_admin_ok` na raiz.

---

## Dependências

- `scripts/preflight_check.py` (validação técnica)
- `scripts/sync_rules.py` (auditoria de regras)
- `scripts/persistencia.ps1` (gate de persistência)
- `scripts/memory_engine.py` (registro de aprendizado)
- `mcp/nucleo/habilidades/compreensao-pedidos/compreensao.py` (filtro de relevância LLM opcional)
- Vigilante (timer + log + lock)

---

## Premissas

- O ecossistema já roda `vigilante.ps1` continuamente (PID file, log, timers).
- `preflight_check.py` e `sync_rules.py audit` rodam em < 30s.
- Fontes curadas são mantidas manualmente em `config/evolution_sources.json` (lista de repos/feeds confiáveis).
- Administrador define permissão via flag/env — padrão **desligado**.

---

## Entradas e Saídas

### Entradas
- `config/evolution_sources.json` — lista de fontes (GitHub repos, RSS, changelogs)
- `EVOLUTION_RADAR_ADMIN=1` ou `.evolution_admin_ok` — permissão
- `runtime/state.json` — estado atual (versões, deps, skills ativas)

### Saídas
- `conhecimento/evolution-radar/bruto/YYYY-MM-DD-HHMMSS-<source>.jsonl` — coleta crua
- `conhecimento/evolution-radar/filtrado/YYYY-MM-DD-<slug>.md` — propostas individuais validadas
- `conhecimento/evolution-radar/pacotes/evolution-pack-YYYY-MM-DD-v<N>.json` — pacote pronto para aplicação
- `conhecimento/evolution-radar/aplicados/evolution-pack-YYYY-MM-DD-v<N>-aplicado.json` — histórico

---

## Casos de Borda

- Coleta falha (rede, rate limit) → loga, mantém último estado, não propõe lixo.
- Fonte retorna breaking change conhecido (ex: Python 3.13 remove módulo) → marca `breaking: true`, exige POC.
- Proposta conflita com skill existente → marca `conflito: <skill>`, sugere consolidação.
- Pacote aplicado falha no preflight → rollback automático + registro em `aplicados` com status `revertido`.
- Vigilante reiniciado no meio do ciclo → retoma do último checkpoint (arquivo de estado em `runtime/evolution_radar_state.json`).

---

## Critérios de Aceitação

- [arquivo:scripts/evolution_radar_collect.py] — coletor principal existe e roda `python scripts/evolution_radar_collect.py --check` sem erro
- [arquivo:scripts/evolution_radar_collect.py] — flag `--collect` faz coleta + filtro + validação + salva propostas
- [arquivo:scripts/evolution_radar_collect.py] --flag `--package` gera pacote a partir de propostas validadas não empacotadas
- [arquivo:scripts/evolution_radar_collect.py] --flag `--apply <pacote.json>` aplica pacote via gate + rollback se falhar
- [arquivo:config/evolution_sources.json] — existe com pelo menos 3 fontes curadas (ex: python/cpython, modelcontextprotocol/spec, opencode-ai/opencode)
- [comando:python scripts/preflight_check.py] — passa após simulação de proposta
- [comando:python scripts/sync_rules.py audit] — passa após simulação de proposta
- [comando:python scripts/monitor_opencode_cache.py --check] — continua passando (não quebra cache)
- [comando:powershell -c "& 'scripts/persistencia.ps1' status"] — mostra modo AUTO

---

## Definition of Done

- Coletor 100% stdlib (ou requests se já no projeto), < 300 linhas, segue padrão `audit_triagem.py`.
- Timer no `vigilante.ps1` com intervalo **configurável** (default 4h = 14400000ms), respeita `EVOLUTION_RADAR_ADMIN`.
- Log no `.vigilante.log` padrão: `EVOLUTION RADAR: coletou X, filtrado Y, pacote Z gerado`.
- Relatório ao admin via `jarvis_bridge.py` (TTS/texto): "Evolution Radar: 3 propostas no pacote evolution-pack-2026-08-14-v1. Aplicar?"
- Memória registrada via `memory_engine.py add` a cada ciclo.
- Testado: `python scripts/evolution_radar_collect.py --collect --package` → gera pacote → `--apply` (dry-run) → rollback ok.

---

## Riscos

- **Rate limit GitHub** → mitigação: cache local + backoff exponencial + fontes alternativas.
- **Falso positivo (propõe lixo)** → mitigação: filtro LLM opcional + validação preflight obrigatória.
- **Pacote grande demais** → mitigação: limite de 5 propostas/pacote, prioriza ganho/baixo risco.
- **Admin esquece de dar permissão** → mitigação: loga "sem permissão, pulando" + notifica na próxima interação.
- **Conflito com vigilante existente** → mitigação: usa mesmo lock PID, mesmo log, mesmo padrão de timer.

---

## Testes Relacionados

- `scripts/test_evolution_radar.py` — testa coleta, filtro, package, apply/rollback (mock fontes)
- `scripts/test-ecosystem.ps1` — inclui `Test-EvolutionRadar` (roda collect --check)
- Integração: vigilante roda 1 ciclo completo (collect → package → notify) sem erro

---

## Integração com Vigilante

```powershell
# Em vigilante.ps1, novo timer (intervalo configurável via $evolutionRadarInterval = 14400000)
$evolutionRadarTimer = New-Object System.Timers.Timer
$evolutionRadarTimer.Interval = $evolutionRadarInterval  # default 4h
$evolutionRadarTimer.AutoReset = $true

$onEvolutionRadar = {
    if (-not (Test-Path "$ecoDir\.evolution_admin_ok") -and $env:EVOLUTION_RADAR_ADMIN -ne "1") {
        Write-Log "EVOLUTION RADAR: sem permissão admin, pulando."
        return
    }
    Write-Log "EVOLUTION RADAR: iniciando ciclo..."
    try {
        $out = python "$ecoDir\scripts\evolution_radar_collect.py" --collect --package 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
        # Notifica admin via bridge (TTS/texto)
        $pack = Get-ChildItem "$ecoDir\conhecimento\evolution-radar\pacotes" -Filter "evolution-pack-*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($pack) {
            $msg = "Evolution Radar: pacote $($pack.BaseName) pronto com $($pack.Content | ConvertFrom-Json).propostas.Count propostas. Aplicar?"
            python "$ecoDir\scripts\jarvis_bridge.py" notify "$msg" 2>$null
        }
    } catch { Write-Log "EVOLUTION RADAR: erro: $_" }
}
Register-ObjectEvent $evolutionRadarTimer "Elapsed" -Action $onEvolutionRadar > $null
$evolutionRadarTimer.Start()
```

---

## Próximos Passos (após spec aprovada)

1. Criar `config/evolution_sources.json` com fontes iniciais.
2. Implementar `scripts/evolution_radar_collect.py` (stdlib, padrão `audit_triagem.py`).
3. Adicionar timer no `vigilante.ps1` (intervalo 4h, variável `$evolutionRadarInterval`).
4. Testar ciclo completo: collect → package → notify → apply (dry-run) → rollback.
5. Registrar aprendizado e persistir via gate.