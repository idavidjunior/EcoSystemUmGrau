#!/usr/bin/env python3
"""
Fundamental Analysis — P/L, P/VP, ROE, FCF yield, D/E, dividendos, growth.
Fontes: Yahoo Finance (yfinance), Status Invest, Fundamentus, SEC EDGAR, Alpha Vantage.
"""
import sys
import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import requests
except ImportError:
    requests = None

_cache = {}
_CACHE_TTL = 3600  # 1h para fundamental


def _cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        val, ts = _cache[key]
        if (datetime.now() - ts).total_seconds() < _CACHE_TTL:
            return val
    return None


def _cache_set(key: str, val: Any):
    _cache[key] = (val, datetime.now())


def get_yahoo_fundamental(symbol: str) -> Dict:
    """Fundamentais via yfinance.info."""
    if not yf:
        raise RuntimeError("yfinance não instalado")
    cached = _cache_get(f"yf_fund:{symbol}")
    if cached:
        return cached
    ticker = yf.Ticker(symbol)
    info = ticker.info
    if not info or "symbol" not in info:
        raise ValueError(f"Sem dados fundamental para {symbol}")
    result = {
        "symbol": symbol,
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "pb_ratio": info.get("priceToBook"),
        "ps_ratio": info.get("priceToSalesTrailing12Months"),
        "ev_revenue": info.get("enterpriseToRevenue"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "roi": info.get("returnOnInvestment"),
        "revenue_ttm": info.get("totalRevenue"),
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "earnings_growth_yoy": info.get("earningsGrowth"),
        "ebitda": info.get("ebitda"),
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
        "total_debt": info.get("totalDebt"),
        "total_cash": info.get("totalCash"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "dividend_yield": info.get("dividendYield"),
        "dividend_rate": info.get("dividendRate"),
        "payout_ratio": info.get("payoutRatio"),
        "dividend_growth_5y": info.get("dividendGrowthRate5Year"),
        "beta": info.get("beta"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "float_shares": info.get("floatShares"),
        "held_insiders_pct": info.get("heldPercentInsiders"),
        "held_institutions_pct": info.get("heldPercentInstitutions"),
        "short_ratio": info.get("shortRatio"),
        "target_price": info.get("targetMeanPrice"),
        "recommendation": info.get("recommendationKey"),
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set(f"yf_fund:{symbol}", result)
    return result


def get_fundamentus(ticker: str) -> Dict:
    """Fundamentus (BR) via scraping — placeholder, requer implementação robusta."""
    return {"symbol": ticker, "note": "Implementar scraping Fundamentus ou usar API paga", "timestamp": datetime.now().isoformat()}


def get_status_invest(ticker: str) -> Dict:
    """Status Invest (BR) — placeholder."""
    return {"symbol": ticker, "note": "Implementar API Status Invest", "timestamp": datetime.now().isoformat()}


def get_alpha_vantage_overview(symbol: str, api_key: str = None) -> Dict:
    """Alpha Vantage OVERVIEW — precisa key gratuita."""
    if not requests:
        raise RuntimeError("requests não instalado")
    if not api_key:
        api_key = os.getenv("ALPHA_VANTAGE_KEY")
    if not api_key:
        raise RuntimeError("ALPHA_VANTAGE_KEY não definido")
    cached = _cache_get(f"av:{symbol}")
    if cached:
        return cached
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": symbol, "apikey": api_key}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "Symbol" not in data:
        raise ValueError(f"Alpha Vantage erro: {data}")
    result = {k.lower(): v for k, v in data.items()}
    result["timestamp"] = datetime.now().isoformat()
    _cache_set(f"av:{symbol}", result)
    return result


def get_sec_filings(ticker: str, form_type: str = "10-K", count: int = 5) -> List[Dict]:
    """SEC EDGAR filings — via sec-api.io ou scraping."""
    return [{"symbol": ticker, "note": "Implementar com sec-api.io", "timestamp": datetime.now().isoformat()}]


def score_fundamental(data: Dict) -> Dict:
    """Score simples 0-100 baseado em critérios de qualidade."""
    score = 0
    reasons = []
    # Profitability
    if data.get("roe") and data["roe"] > 0.15:
        score += 15; reasons.append("ROE > 15%")
    elif data.get("roe") and data["roe"] > 0.10:
        score += 10; reasons.append("ROE > 10%")
    if data.get("profit_margin") and data["profit_margin"] > 0.15:
        score += 10; reasons.append("Margem líquida > 15%")
    # Growth
    if data.get("revenue_growth_yoy") and data["revenue_growth_yoy"] > 0.15:
        score += 15; reasons.append("Receita crescendo > 15% a.a.")
    elif data.get("revenue_growth_yoy") and data["revenue_growth_yoy"] > 0.05:
        score += 10; reasons.append("Receita crescendo > 5% a.a.")
    if data.get("earnings_growth_yoy") and data["earnings_growth_yoy"] > 0.15:
        score += 10; reasons.append("Lucro crescendo > 15% a.a.")
    # Financial health
    if data.get("debt_to_equity") and data["debt_to_equity"] < 0.5:
        score += 15; reasons.append("D/E < 0.5")
    elif data.get("debt_to_equity") and data["debt_to_equity"] < 1.0:
        score += 10; reasons.append("D/E < 1.0")
    if data.get("current_ratio") and data["current_ratio"] > 1.5:
        score += 10; reasons.append("Current ratio > 1.5")
    if data.get("free_cashflow") and data["free_cashflow"] > 0:
        score += 10; reasons.append("FCF positivo")
    # Valuation
    if data.get("pe_ratio") and 0 < data["pe_ratio"] < 15:
        score += 10; reasons.append("P/L atrativo < 15")
    if data.get("dividend_yield") and data["dividend_yield"] > 0.04:
        score += 5; reasons.append("Div yield > 4%")
    return {"score": min(score, 100), "reasons": reasons, "timestamp": datetime.now().isoformat()}


def selftest() -> bool:
    ok = True
    print("Testando fundamental...")
    try:
        d = get_yahoo_fundamental("AAPL")
        assert "pe_ratio" in d and d["pe_ratio"]
        print(f"  Yahoo AAPL: P/L={d['pe_ratio']:.1f}, ROE={d.get('roe', 'N/A')}, FCF=${d.get('free_cashflow', 0)/1e9:.1f}B OK")
    except Exception as e:
        print(f"  Yahoo: FALHOU - {e}")
        ok = False
    # Score unit test
    test_data = {"roe": 0.20, "profit_margin": 0.25, "revenue_growth_yoy": 0.10, "earnings_growth_yoy": 0.18, "debt_to_equity": 0.3, "current_ratio": 2.0, "free_cashflow": 1e9, "pe_ratio": 12, "dividend_yield": 0.01}
    s = score_fundamental(test_data)
    assert s["score"] > 70
    print(f"  Score test: {s['score']}/100 OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Fundamental Analysis CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("yahoo", help="Yahoo Finance fundamental")
    p.add_argument("symbol")

    p = sub.add_parser("alphavantage", help="Alpha Vantage overview")
    p.add_argument("symbol")
    p.add_argument("--key")

    p = sub.add_parser("score", help="Score fundamental de dict JSON")
    p.add_argument("json_file")

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "yahoo":
            print(json.dumps(get_yahoo_fundamental(args.symbol), indent=2, default=str))
        elif args.cmd == "alphavantage":
            print(json.dumps(get_alpha_vantage_overview(args.symbol, args.key), indent=2, default=str))
        elif args.cmd == "score":
            with open(args.json_file) as f:
                data = json.load(f)
            print(json.dumps(score_fundamental(data), indent=2, default=str))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()