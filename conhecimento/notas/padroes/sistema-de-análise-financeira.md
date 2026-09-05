---
tags: [fred, local, markets, opencode, padrao, webhook]
aliases: [Sistema de Análise Financeira]
date: 2026-08-21
---

# Sistema de Análise Financeira

**Fonte:** opencode

## Módulos criados (scripts/financas/)
| Script | Função | Fontes |
|---|---|---|
| market_data.py | Preços OHLCV, funding rate | Yahoo, Binance, Bybit, brapi, TwelveData |
| onchain.py | TVL, NVT, MVRV, SOPR | CoinGecko, DefiLlama, Glassnode, Blockchain.com |
| fundamental.py | P/L, ROE, FCF, score 0-100 | yfinance |
| technical.py | RSI, MACD, Bollinger, VWAP, OBV, ATR, ADX, Wyckoff, S/R | cálculo local |
| risk.py | VaR/CVaR (hist/param/MC), max DD, Kelly, stress test | cálculo local |
| portfolio.py | Markowitz, Risk Parity, HRP, Black-Litterman, rebalance | scipy |
| alerts.py | Breakout Donchian, volume spike, funding extremo, RSI extremo | polling + webhook |
| crypto_screener.py | Filtro mcap/volume/liquidez/dev/inflação, gems, momentum | CoinGecko markets |
| macro.py | Selic, IPCA, PTAX, yield curve, VIX | BCB SGS/PTAX, FRED, Yahoo |
| income_strategies.py | Covered call, CSP, staking, farming, dividendos, arbitragem, projeção | cálculo local |

## Bugs encontrados e corrigid
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]