# Análise Financeira — Mercado, Investimentos, Crypto, Renda

## Objetivo
Análise técnica, fundamental e quantitativa de mercados financeiros: ações (BR/US), cripto, forex, renda fixa, derivativos. Geração de renda, alocação, gestão de risco, detecção de oportunidades. Trigger: `/finanças` ou `@finanças`.

## Quando ativar
- Pedido explícito: `/finanças` ou `@finanças`
- Análise de ativo, carteira, estratégia
- Monitoramento de mercado / alertas de oportunidade
- Estudo de renda extra, day trade, crypto, alocação

## Princípios inegociáveis
- **Zero emoção, zero delírio** — apenas dados, probabilidades, evidência
- **Risco primeiro** — toda recomendação traz: risco de ruína, drawdown máximo, correlação, liquidez
- **Fontes primárias** — dados de bolsa (B3, NYSE/NASDAQ), on-chain (Glassnode, CoinGecko, DefiLlama), BCB, CVM, SEC, FRED
- **Validação adversária** — testar contra cenários de cauda (crash 2008, 2020, crypto winter, Luna/FTX)
- **Transparência total** — metodologia,假设, limitações, conflitos expostos

## Estrutura de dados (scripts em `scripts/financas/`)

| Script | Função | Fonte |
|--------|--------|-------|
| `market_data.py` | Cotações, OHLCV, order book, funding rates | Yahoo Finance, Binance, Bybit, B3, Twelve Data, Alpha Vantage |
| `onchain.py` | Métricas on-chain: NVT, MVRV, SOPR, exchange flows, whale alerts | Glassnode API, CoinGecko, DefiLlama, Blockchain.com |
| `fundamental.py` | Fundamentos: P/L, P/VP, ROE, FCF yield, D/E, dividendos, growth | Yahoo Finance, Status Invest, Fundamentus, SEC EDGAR |
| `technical.py` | Indicadores: RSI, MACD, Bollinger, VWAP, OBV, order flow, Wyckoff | Pandas-ta, TA-Lib, implementação própria |
| `risk.py` | VaR, CVaR, stress test, correlação, Kelly criterion, position sizing | Monte Carlo, historical simulation |
| `portfolio.py` | Otimização: Markowitz, HRP, Black-Litterman, risk parity, rebalance | PyPortfolioOpt, implementação própria |
| `alerts.py` | Monitoramento contínuo: breakouts, volume anômalo, funding rate extremo, whale moves | Webhook, polling, websocket |
| `crypto_screener.py` | Filtro: market cap, volume, dev activity, tokenomics, narrative, liquidity | CoinGecko, DefiLlama, GitHub, Token Terminal |
| `macro.py` | Dados macro: Selic, IPCA, DXY, yields, VIX, PMI, payroll, CPI/PPI | BCB, FRED, TradingEconomics, Investing.com |
| `income_strategies.py` | Renda: covered calls, cash-secured puts, staking, lending, yield farming, dividends, arbitragem | Cálculo próprio + APIs |

## Metodologia de análise (pipeline obrigatório)

```
1. DEFINIR UNIVERSO → filtrar por liquidez, mercado, narrativa
2. COLETAR DADOS → market_data + onchain + fundamental + macro
3. SCREENING QUANTITATIVO → filtros objetivos (ex: volume > $10M/d, mcap > $100M)
4. ANÁLISE TÉCNICA → estrutura de preço, volume, order flow, fase Wyckoff
5. ANÁLISE FUNDAMENTAL/ON-CHAIN → valuation, health, adoption, tokenomics
6. ANÁLISE DE RISCO → VaR 99%, max drawdown histórico, correlação carteira, tail risk
7. SIZING & EXECUTION → Kelly fraction, risk/reward, entry/stop/target, time horizon
8. MONITORAMENTO → alertas de invalidation, take-profit parcial, rebalance triggers
9. REGISTRO → memory_engine.add (decisao/erro/padrao) + conhecimento/aprendizados/
```

## Critérios de screening (exemplos — ajustáveis)

### Ações (BR)
- Liquidez: ADTV > R$ 5M
- P/L < setor, ROE > 15%, D/E < 0.5, FCF yield > 8%
- Dividend yield > 6% + histórico 5 anos crescente

### Ações (US)
- Liquidez: ADTV > $50M
- Revenue growth > 15% YoY, FCF margin > 15%, net cash position
- Institutional ownership > 40%, insider buying recente

### Crypto (alto risco — apenas para alocação satélite ≤ 5-10% do patrimônio)
- Liquidez: volume 24h > $5M, spread < 0.5%, listado em ≥ 3 CEX top 10
- On-chain: endereços ativos crescendo, hash rate/staking ratio saudável, exchange outflow
- Tokenomics: supply inflation < 10%/a, vesting team > 12 meses, utilidade real
- Narrativa + catalisadores: mainnet, ETF, parceria enterprise, regulamentação favorável
- Dev activity: commits 30d > 50, contributors > 10, repos ativos

### Renda fixa / Caixa
- Tesouro IPCA+ 2035/2045: real yield > IPCA + 5.5%
- CDB/LCI/LCA: > 110% CDI, liquidez diária ou prazo alinhado
- Treasury US: T-bill 6M > 5%, TIPs real yield > 2%

## Gestão de risco (regras duras)

| Regra | Valor |
|-------|-------|
| Risco por trade | ≤ 1% do capital total (2% máximo em cenário excepcional) |
| Drawdown máximo carteira | 15% (trigger: reduzir exposição 50%) |
| Correlação máxima entre posições | 0.7 |
| Alocação crypto (satélite) | ≤ 10% do patrimônio líquido |
| Alocação day trade | ≤ 5% do capital, apenas se track record comprovado > 1 ano |
| Stop loss obrigatório | Sempre — técnico (estrutura) ou volumétrico |
| Position sizing | Kelly fraction limitada a 25% (half-Kelly) |
| Rebalance | Mensal ou quando drift > 10% do target |

## Output padrão para `/finanças`

```
=== ANÁLISE FINANCEIRA ===
Ativo/Universo: [ativo ou filtro]
Data/Hora: [timestamp UTC-3]
Horizonte: [curto/médio/longo]
Perfil de risco: [conservador/moderado/agressivo]

--- DADOS BRUTOS ---
[Resumo: preço, volume, mcap, fundamentais chave, on-chain chave]

--- ANÁLISE TÉCNICA ---
Tendência: [alta/baixa/lateral] | Fase Wyckoff: [A/B/C/D/E]
Suporte/Resistência chave: [níveis]
Indicadores: RSI(14)=[x], MACD=[sinal], VWAP=[posição]
Volume: [anômalo/normal] | Order flow: [comprador/vendedor neutro]

--- ANÁLISE FUNDAMENTAL/ON-CHAIN ---
Valuation: [caro/justo/barato] | Métricas: [P/L, NVT, MVRV, etc.]
Saúde financeira / adoção: [forte/média/fraca]
Catalisadores: [próximos 30-90 dias]

--- RISCO ---
VaR 99% (1d): [%] | Max DD histórico: [%]
Correlação com BTC/IBOV/SPX: [coeficiente]
Liquidez: [alta/média/baixa] | Slippage estimado: [%]

--- RECOMENDAÇÃO ---
Ação: [COMPRAR / VENDER / MANTER / EVITAR / ESTUDAR MAIS]
Entry zone: [faixa] | Stop: [preço] | Targets: [T1, T2, T3]
Position size sugerido: [% do capital] | R:R: [ratio]
Confiança: [baixa/média/alta] — base: [evidência principal]

--- ALERTAS ATIVOS ---
[Se houver: breakout, whale alert, funding extremo, macro event]
```

## Integração com ecossistema
- Skills pré-requisito: `fundamentos-computacao` (math/stats), `data-pipeline` (ETL), `monitoring-alerting` (alertas), `risk-management` (VaR, stress)
- Agentes: `03-realista` (viabilidade), `02-cetico` (contestar), `04-etica` (dever fiduciário), `05-futuro` (tendências macro/tech)
- Scripts: `scripts/financas/*.py` + `scripts/monitoring/*` para alertas contínuos
- Memória: `memory_engine.add` kind `decisao` (trades), `padrao` (setups), `erro` (stops batidos)

## Validação
Antes de usar: `python scripts/financas/market_data.py --selftest`
Preflight: `python scripts/preflight_check.py` (inclui validação de APIs, chaves, rate limits)