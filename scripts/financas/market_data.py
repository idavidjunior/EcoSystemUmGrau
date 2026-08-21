#!/usr/bin/env python3
"""
Market Data — Cotações, OHLCV, order book, funding rates.
Fontes: Yahoo Finance (yfinance), Binance, Bybit, B3 (via brapi), Twelve Data, Alpha Vantage.
Todas as funções retornam dict padronizado ou levantam exceção clara.
"""
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import requests
except ImportError:
    requests = None

try:
    import pandas as pd
except ImportError:
    pd = None

# Cache simples em memória
_cache = {}
_CACHE_TTL = 60  # segundos


def _cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        val, ts = _cache[key]
        if (datetime.now() - ts).total_seconds() < _CACHE_TTL:
            return val
    return None


def _cache_set(key: str, val: Any):
    _cache[key] = (val, datetime.now())


def get_yahoo(symbol: str, period: str = "1mo", interval: str = "1d") -> Dict:
    """Cotação + OHLCV via yfinance."""
    if not yf:
        raise RuntimeError("yfinance não instalado: pip install yfinance")
    cached = _cache_get(f"yahoo:{symbol}:{period}:{interval}")
    if cached:
        return cached
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)
    info = ticker.info
    if hist.empty:
        raise ValueError(f"Sem dados para {symbol}")
    last = hist.iloc[-1]
    result = {
        "symbol": symbol,
        "price": float(last["Close"]),
        "open": float(last["Open"]),
        "high": float(last["High"]),
        "low": float(last["Low"]),
        "volume": int(last["Volume"]),
        "change_pct": float((last["Close"] - last["Open"]) / last["Open"] * 100),
        "timestamp": datetime.now().isoformat(),
        "info": {
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "free_cashflow": info.get("freeCashflow"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "return_on_equity": info.get("returnOnEquity"),
            "profit_margins": info.get("profitMargins"),
        },
        "ohlcv": hist[["Open", "High", "Low", "Close", "Volume"]].tail(20).to_dict(orient="records"),
    }
    _cache_set(f"yahoo:{symbol}:{period}:{interval}", result)
    return result


def get_binance(symbol: str, interval: str = "1h", limit: int = 500) -> Dict:
    """OHLCV + funding rate via Binance public API (spot + futures)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    # Spot klines
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"Sem dados Binance para {symbol}")
    klines = [{
        "open_time": datetime.fromtimestamp(k[0]/1000).isoformat(),
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
        "close_time": datetime.fromtimestamp(k[6]/1000).isoformat(),
        "quote_volume": float(k[7]),
        "trades": int(k[8]),
    } for k in data]
    # Ticker 24h
    ticker_url = "https://api.binance.com/api/v3/ticker/24hr"
    tr = requests.get(ticker_url, params={"symbol": symbol.upper()}, timeout=10)
    tr.raise_for_status()
    t24 = tr.json()
    # Funding rate (futures)
    funding = None
    try:
        fund_url = "https://fapi.binance.com/fapi/v1/fundingRate"
        fr = requests.get(fund_url, params={"symbol": symbol.upper(), "limit": 1}, timeout=10)
        if fr.status_code == 200:
            fdata = fr.json()
            if fdata:
                funding = {
                    "rate": float(fdata[0]["fundingRate"]),
                    "timestamp": datetime.fromtimestamp(fdata[0]["fundingTime"]/1000).isoformat(),
                }
    except Exception:
        pass
    result = {
        "symbol": symbol.upper(),
        "price": float(t24["lastPrice"]),
        "change_pct": float(t24["priceChangePercent"]),
        "volume_24h": float(t24["volume"]),
        "quote_volume_24h": float(t24["quoteVolume"]),
        "high_24h": float(t24["highPrice"]),
        "low_24h": float(t24["lowPrice"]),
        "open_24h": float(t24["openPrice"]),
        "timestamp": datetime.now().isoformat(),
        "klines": klines,
        "funding_rate": funding,
    }
    _cache_set(f"binance:{symbol}:{interval}:{limit}", result)
    return result


def get_bybit(symbol: str, interval: str = "60", limit: int = 200) -> Dict:
    """OHLCV via Bybit public API (linear/perp)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "linear", "symbol": symbol.upper(), "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data["retCode"] != 0 or not data["result"]["list"]:
        raise ValueError(f"Sem dados Bybit para {symbol}")
    klines = [{
        "open_time": datetime.fromtimestamp(int(k[0])/1000).isoformat(),
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
        "turnover": float(k[6]),
    } for k in reversed(data["result"]["list"])]  # Bybit retorna mais antigo primeiro
    # Ticker
    ticker_url = "https://api.bybit.com/v5/market/tickers"
    tr = requests.get(ticker_url, params={"category": "linear", "symbol": symbol.upper()}, timeout=10)
    tr.raise_for_status()
    td = tr.json()
    t24 = td["result"]["list"][0] if td["retCode"] == 0 and td["result"]["list"] else {}
    result = {
        "symbol": symbol.upper(),
        "price": float(t24.get("lastPrice", klines[-1]["close"])),
        "change_pct": float(t24.get("price24hPcnt", 0)) * 100,
        "volume_24h": float(t24.get("volume24h", 0)),
        "turnover_24h": float(t24.get("turnover24h", 0)),
        "high_24h": float(t24.get("highPrice24h", 0)),
        "low_24h": float(t24.get("lowPrice24h", 0)),
        "timestamp": datetime.now().isoformat(),
        "klines": klines,
    }
    _cache_set(f"bybit:{symbol}:{interval}:{limit}", result)
    return result


def get_brapi(symbol: str) -> Dict:
    """Cotação B3 via brapi.dev (gratuito, rate limited)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    token = os.getenv("BRAPI_TOKEN")
    if not token:
        raise RuntimeError("BRAPI_TOKEN não definido em .env")
    url = f"https://brapi.dev/api/quote/{symbol.upper()}"
    r = requests.get(url, params={"token": token}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise ValueError(f"Sem dados B3 para {symbol}")
    q = data["results"][0]
    result = {
        "symbol": symbol.upper(),
        "price": q.get("regularMarketPrice"),
        "change_pct": q.get("regularMarketChangePercent"),
        "volume": q.get("regularMarketVolume"),
        "market_cap": q.get("marketCap"),
        "pe_ratio": q.get("trailingPE"),
        "dividend_yield": q.get("dividendYield"),
        "currency": q.get("currency"),
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set(f"brapi:{symbol}", result)
    return result


def get_twelve_data(symbol: str, interval: str = "1day", outputsize: int = 100) -> Dict:
    """Via Twelve Data (precisa API key)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    key = os.getenv("TWELVE_DATA_KEY")
    if not key:
        raise RuntimeError("TWELVE_DATA_KEY não definido")
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": symbol, "interval": interval, "outputsize": outputsize, "apikey": key}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if "values" not in data:
        raise ValueError(f"Erro Twelve Data: {data}")
    values = data["values"]
    latest = values[0]
    result = {
        "symbol": symbol,
        "price": float(latest["close"]),
        "open": float(latest["open"]),
        "high": float(latest["high"]),
        "low": float(latest["low"]),
        "volume": int(latest["volume"]),
        "timestamp": datetime.now().isoformat(),
        "ohlcv": [{
            "datetime": v["datetime"],
            "open": float(v["open"]),
            "high": float(v["high"]),
            "low": float(v["low"]),
            "close": float(v["close"]),
            "volume": int(v["volume"]),
        } for v in values],
    }
    _cache_set(f"twelve:{symbol}:{interval}:{outputsize}", result)
    return result


def search_symbols(query: str, source: str = "yahoo") -> List[Dict]:
    """Busca símbolos (Yahoo Finance via yfinance search)."""
    if source == "yahoo" and yf:
        # yfinance não tem search oficial; usar fallback simples
        return [{"symbol": query.upper(), "source": "yahoo"}]
    return []


def selftest() -> bool:
    ok = True
    print("Testando market_data...")
    # Teste Yahoo (ação US)
    try:
        d = get_yahoo("AAPL", "1d", "1m")
        assert "price" in d and d["price"] > 0
        print(f"  Yahoo AAPL: ${d['price']:.2f} OK")
    except Exception as e:
        print(f"  Yahoo AAPL: FALHOU - {e}")
        ok = False
    # Teste Binance
    try:
        d = get_binance("BTCUSDT", "1h", 10)
        assert "price" in d and d["price"] > 0
        print(f"  Binance BTCUSDT: ${d['price']:.2f} OK")
    except Exception as e:
        print(f"  Binance: FALHOU - {e}")
        ok = False
    # Teste Bybit
    try:
        d = get_bybit("BTCUSDT", "60", 10)
        assert "price" in d and d["price"] > 0
        print(f"  Bybit BTCUSDT: ${d['price']:.2f} OK")
    except Exception as e:
        print(f"  Bybit: FALHOU - {e}")
        ok = False
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Market Data CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("yahoo", help="Yahoo Finance")
    p.add_argument("symbol")
    p.add_argument("-p", "--period", default="1mo")
    p.add_argument("-i", "--interval", default="1d")

    p = sub.add_parser("binance", help="Binance Spot")
    p.add_argument("symbol")
    p.add_argument("-i", "--interval", default="1h")
    p.add_argument("-l", "--limit", type=int, default=500)

    p = sub.add_parser("bybit", help="Bybit Linear/Perp")
    p.add_argument("symbol")
    p.add_argument("-i", "--interval", default="60")
    p.add_argument("-l", "--limit", type=int, default=200)

    p = sub.add_parser("brapi", help="B3 via brapi.dev")
    p.add_argument("symbol")

    p = sub.add_parser("twelve", help="Twelve Data")
    p.add_argument("symbol")
    p.add_argument("-i", "--interval", default="1day")
    p.add_argument("-o", "--outputsize", type=int, default=100)

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "yahoo":
            print(json.dumps(get_yahoo(args.symbol, args.period, args.interval), indent=2, default=str))
        elif args.cmd == "binance":
            print(json.dumps(get_binance(args.symbol, args.interval, args.limit), indent=2, default=str))
        elif args.cmd == "bybit":
            print(json.dumps(get_bybit(args.symbol, args.interval, args.limit), indent=2, default=str))
        elif args.cmd == "brapi":
            print(json.dumps(get_brapi(args.symbol), indent=2, default=str))
        elif args.cmd == "twelve":
            print(json.dumps(get_twelve_data(args.symbol, args.interval, args.outputsize), indent=2, default=str))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()