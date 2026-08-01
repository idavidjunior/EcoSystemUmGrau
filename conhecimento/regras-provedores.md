# Regras e Limites dos Provedores (OpenCode + NVIDIA NIM)
**Atualizado:** 01/08/2026 | **Fonte:** nvidia-nim rate-limits.yml, OmniRoute, forums NVIDIA, docs oficiais

---

## NVIDIA NIM (Provedor principal configurado)

### Limites Oficiais (conta free tier)

| Limite | Valor | Escopo | Observação |
|--------|-------|--------|------------|
| **RPM (Requests/Min)** | **40** | Por API key (conta) | **Account-wide**, não por modelo. Compartilhado entre todos os 77+ modelos. |
| **Concorrência (in-flight)** | **5** | Por API key | Máximo 5 requests simultâneos. |
| **Créditos iniciais** | **1.000** | Por conta (signup) | Consumidos por request; modelos grandes gastam mais. |
| **Max output tokens** | **4.096** | Por request | Pode variar por modelo (alguns suportam mais). |
| **Max input tokens** | **128.000** | Por request | Modelos long-context (Llama 3.1/3.3, Nemotron) até ~128K. |
| **SSE keepalive** | **60s** | Por stream | Conexões idle >60s fechadas pelo gateway. |
| **Créditos** | Variável | Por request | Modelos leves (Llama 8B) = fração; grandes (DeepSeek-R1 671B) = mais créditos. |

### Regras Críticas (não documentadas oficialmente, mas confirmadas)

1. **40 RPM é account-wide** — NÃO por modelo. Trocar de modelo não reseta o limite.
2. **Limites não publicados por modelo** — modelos populares (Kimi, Nemotron) podem throttlear **abaixo de 40 RPM**.
3. **Sem API de uso/quota** — NVIDIA confirmou: não existe endpoint `/usage` ou `/credits`. O único lugar para ver o teto é o UI do build.nvidia.com.
4. **Sem aumento de limite no free tier** — Staff NVIDIA: não aprovam aumentos; free tier é para prototipagem.
4. **429 incluem `Retry-After`** — respeitar o header para backoff.
5. **Concorrência 5** — bursts de agentes (OpenCode, Cursor) estouram fácil. Cap recomendado: 4-8 in-flight.
6. **Modelos populares throttlear mais** — Kimi K2.6, Nemotron relatados abaixo de 40 RPM.
7. **Registro por família** — alguns modelos exigem clicar "Try API" na página do build.nvidia.com antes de aceitar a key.

### Headers de resposta para monitorar
- `Retry-After` (em 429) — segundos para esperar
- `X-RateLimit-*` — não documentados hoje, mas capturar para futuro

---

## Modelos FREE (opencode/*) — 7 disponíveis

| Ordem | Modelo | Perfil |
|-------|--------|--------|
| 1 | `opencode/nemotron-3-ultra-free` | Topo — raciocínio/código pesado |
| 2 | `opencode/deepseek-v4-flash-free` | Rápido, bom código |
| 3 | `opencode/laguna-s-2.1-free` | Foco código |
| 4 | `opencode/ling-3.0-flash-free` | Rápido, geral |
| 5 | `opencode/mimo-v2.5-free` | Médio |
| 6 | `opencode/north-mini-code-free` | Pequeno, código |
| 7 | `opencode/big-pickle` | Último recurso |

**Cadeia configurada** no `opencode.jsonc` nessa ordem (mais capaz → menos capaz).

---

## Configuração de Fallback Proativo (já aplicada)

```json
"@razroo/opencode-model-fallback": {
  "enabled": true,
  "retry_on_errors": [429, 500, 502, 503, 504],
  "retryable_error_patterns": ["rate limit", "quota exceeded", "insufficient quota", "too many requests", "capacity exceeded"],
  "max_fallback_attempts": 5,
  "cooldown_seconds": 2,
  "timeout_seconds": 15,
  "notify_on_fallback": true,
  "fallback_models": [
    "opencode/nemotron-3-ultra-free",
    "opencode/deepseek-v4-flash-free",
    "opencode/laguna-s-2.1-free",
    "opencode/ling-3.0-flash-free",
    "opencode/mimo-v2.5-free",
    "opencode/north-mini-code-free",
    "opencode/big-pickle"
  ]
}
```

**Lógica:** timeout 15s detecta stall cedo; cooldown 2s acelera; 5 tentativas sobem a cadeia completa; patterns capturam "quota exceeded" etc.

---

## OpenCode — Regras de Uso

- **Modelo padrão:** `opencode/deepseek-v4-flash-free` (config global)
- **Providers disponíveis:** `opencode` (free), `nvidia` (configurado), `deepseek`, `openai`
- **Plugin fallback:** `@razroo/opencode-model-fallback` v0.3.2 instalado
- **Comandos úteis:**
  - `npx opencode models` — lista modelos atuais
  - `npx opencode providers list` — provedores e credenciais
  - `npx opencode debug config` — config resolvida

---

## Monitoramento Contínuo (Para não sermos pegos de surpresa)

### Ações recomendadas (implementar no ecossistema)
1. **Client-side RPM tracker** — token bucket local por conexão NVIDIA (budget 40/min, respeita `Retry-After`).
2. **Concurrency cap** — max 4-5 in-flight requests para NVIDIA (evita burst 429).
3. **Classificação de erro** — 429 = rate limit (backoff + conta no budget); 502/504/timeout = saturação/gateway (não encolhe budget aprendido).
4. **Dashboard local** — mostrar RPM atual vs budget, modelos ativos, fallbacks usados.
5. **Empirical RPM probe** — script periódico pingando modelos para medir headroom real.

### Scripts a criar
- `scripts/nvidia_quota_monitor.py` — monitora RPM local, alerta se >80% do budget.
- `scripts/model_health_check.py` — testa todos modelos free + NVIDIA, loga latência/429.
- `scripts/quota_dashboard.py` — painel simples TXT/JSON para o bridge consultar.

---

## Referências Oficiais / Comunitárias

- **Rate limits YAML:** https://github.com/api-evangelist/nvidia-nim/blob/main/rate-limits/nvidia-nim-rate-limits.yml
- **OmniRoute issue (quota tracking):** https://github.com/diegosouzapw/OmniRoute/issues/6846
- **NVIDIA forums (no rate increase):** https://forums.developer.nvidia.com/t/clarity-on-nim-api-free-tier-rate-limit-increases/369624
- **NVIDIA forums (no usage API):** https://forums.developer.nvidia.com/t/usage-tracking-in-nvidia-nim-api/367730
- **build.nvidia.com (UI quota):** https://build.nvidia.com
- **NVIDIA NIM docs (limits):** https://docs.api.nvidia.com/nim/reference/limits

---

## Próximos Passos (Para o Ecossistema)

- [ ] Implementar `nvidia_quota_monitor.py` com token bucket + Retry-After
- [ ] Adicionar concurrency cap no `jarvis_bridge.py` para chamadas NVIDIA
- [ ] Criar `model_health_check.py` rodando a cada 30min (cron)
- [ ] Dashboard de quotas acessível via `jarvis_bridge` (comando `/quota`)
- [ ] Registrar aprendizado toda vez que houver 429 ou fallback ativado

---

**Última verificação:** 01/08/2026 | **Próxima revisão:** semanal ou após qualquer 429 inesperado.