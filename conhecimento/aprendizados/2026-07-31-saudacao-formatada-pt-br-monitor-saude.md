# Aprendizado — 2026-07-31 — Saudação formatada em pt-BR + monitor de saúde

## Contexto
- A saudação criativa via LLM já existia (commit 992b0c8), mas o briefing tinha data/hora em formato solto ("Hoje é sexta-feira, 31 de julho. Agora são 21 e 44 minutos") e o usuário pediu formato padronizado e rico, com modelo de inspiração (12 variações de tom/comprimento) e monitoramento de sistema.

## O que foi feito
1. **`scripts/clima_api.py`** — dados estruturados:
   - `get_weather_data()` → dict {temp, sensacao, umidade, descricao, codigo}.
   - `get_forecast_data(days)` → lista de dias {data, tmin, tmax, precip, descricao}.
   - `get_weather()`/`get_forecast()` viraram wrappers; `get_forecast` agora fala de AMANHÃ (`forecast_days=2`, índice 1).
2. **`scripts/jarvis_bridge.py`**:
   - `DIAS`/`MESES` com acentos corretos (terça, sábado, março...).
   - `briefing_espontaneo()` gera fatos no formato pedido:
     `hoje em São Paulo/SP, na Capital, sexta-feira, 31 de julho de 2026, 22:00` +
     `Clima atual: {desc}, {temp}°C, umidade de {hum}%` +
     `Previsão para amanhã (sábado, 01/08): mínima de 13°C e máxima de 28°C, nublado` + feriado/trânsito.
   - `saude_sistema()` monitora PC (bateria/status carregador, CPU, memória, disco C: via PowerShell/CIM) e celular (bateria via ADB `dumpsys battery`), com **cache de 60s** (evita lag da saudação).
   - `saudar()` instrui o LLM com o **JSON de inspiração** (12 variações), regras anti-alucinação (nunca inventar números; usar formatos prontos do briefing) e menção à saúde só quando relevante.

## Heurísticas registradas
- **Formato de data/hora pt-BR para TTS/exibição**: `DIAS[weekday()], dia de MESES[mês-1] de ano, HH:MM` e amanhã `(DIAS[weekday], DD/MM)`.
- **Anti-alucinação em briefing para LLM**: separar FATOS (string pronta com números reais) de INSTRUÇÃO ("use só o briefing; cite os formatos exatos").
- **Monitor de sistema sem lag**: coletar via subprocess PowerShell/CIM e ADB com timeout curto + cache temporal (60s); falhas silenciosas (nunca quebram a saudação).
- **ADB battery**: `adb -s SERIAL shell dumpsys battery` → regex `level: (\d+)`.

## Estado
- Bridge reiniciada; saudação real validada no log: "Boa noite, senhor! São sexta-feira, 31 de julho de 2026, 22:01, com céu predominantemente limpo e 16 graus lá fora..." (já citando bateria).
- Commit `cfd316a` pushed no EcoSystemUmGrau.
- Pendência: os arquivos soltos `bridge_err.txt`, `bridge_out.txt`, `openapi_spec.json` ainda não estão no `.gitignore`.

## Ajuste (mesmo dia, pedido do usuário)
- Jarvis roda no CELULAR → **saúde prioriza o celular** (bateria sempre reportada; crítica ≤20% e aviso ≤35%).
- **PC em segundo plano**: só entra no briefing se houver alerta (bateria ≤30%, CPU ≥80%, memória ≥85%, disco ≥85%).
- Instrução do `saudar()` reforça a prioridade celular→PC. Validado: "Saúde do sistema: celular com bateria em 93%, PC com memória em 85%."
