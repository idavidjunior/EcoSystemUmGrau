---
tipo: padrao
tags: [financas, analise-financeira, quant, crypto, risco]
data: 2026-08-21
contexto: Sistema completo de análise financeira do ecossistema (/finanças e @finanças)
decisao: |
  Criado sistema de análise financeira em 10 módulos independentes em scripts/financas/,
  cada um com CLI argparse + selftest. Skill mestre em
  mcp/desenvolvimento/habilidades/analise-financeira/skill.md define pipeline de 9 etapas,
  critérios de screening (BR/US/crypto) e regras duras de risco (1% por trade,
  half-Kelly, satélite crypto ≤10%).
impacto: |
  Ecossistema ganha capacidade de análise quantitativa com fontes primárias
  (BCB, FRED, CoinGecko, DefiLlama, Glassnode, Yahoo, Binance, Bybit).
  Zero emoção: toda recomendação passa por VaR/CVaR/stress test.
---

# Sistema de Análise Financeira

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

## Bugs encontrados e corrigidos durante os selftests
1. DefiLlama `/protocol/{slug}` retorna `tvl` como série histórica (lista de pontos),
   não número. Correção: extrair último ponto (`totalLiquidityUSD`).
2. `Dict["pd.Series"]` é inválido — Dict exige 2 argumentos de tipo. Correção:
   `Dict[str, "pd.Series"]` (3 ocorrências em technical.py).
3. Teste de rebalance usava drift exatamente igual ao threshold (0.05 > 0.05 = False).
   Correção: dados de teste com drift inequívoco (0.15).

## Dependências instaladas
pandas 3.0.5, yfinance 1.6.0 (numpy 2.5.1, scipy 1.18.0, requests 2.34.2 já existiam).

## Validação com dados reais
Selic 14,00% (BCB SGS 432), IPCA 12m 4,44% (SGS 13522), VIX 15,9,
BTC ~$77k (Binance/Bybit/CoinGecko consistentes), Lido TVL $22,8B.

## Pendências conhecidas
- API keys opcionais não configuradas: BRAPI_TOKEN, TWELVE_DATA_KEY, GLASSNODE_API_KEY,
  ALPHA_VANTAGE_KEY, FRED_API_KEY, TOKEN_TERMINAL_KEY (em scripts/.env quando necessário).
- HRP implementado como fallback equal-weight (clusterização completa é evolução futura).
- check_macro_events e check_onchain_whales são placeholders (precisam calendário econômico / API whale).
