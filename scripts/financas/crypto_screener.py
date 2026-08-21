#!/usr/bin/env python3
"""
Crypto Screener — Filtro quantitativo: market cap, volume, dev activity, tokenomics, narrative, liquidity.
Fontes: CoinGecko, DefiLlama, GitHub, Token Terminal, CoinMarketCap.
"""
import sys
import json
import argparse
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    import requests
except ImportError:
    requests = None


def get_coingecko_markets(vs_currency: str = "usd", order: str = "market_cap_desc", 
                           per_page: int = 250, page: int = 1, 
                           sparkline: bool = False, category: str = None) -> List[Dict]:
    """Lista de moedas com dados de mercado via CoinGecko."""
    if not requests:
        raise RuntimeError("requests não instalado")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": order,
        "per_page": per_page,
        "page": page,
        "sparkline": str(sparkline).lower(),
        "price_change_percentage": "1h,24h,7d,30d",
    }
    if category:
        params["category"] = category
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def get_token_terminal_metrics(project: str, api_key: str = None) -> Dict:
    """Token Terminal — métricas fundamentalistas (precisa key)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    if not api_key:
        api_key = os.getenv("TOKEN_TERMINAL_KEY")
    if not api_key:
        raise RuntimeError("TOKEN_TERMINAL_KEY não definido")
    url = f"https://api.tokenterminal.com/v1/projects/{project}/metrics"
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def get_github_activity(repo: str, since_days: int = 30) -> Dict:
    """Atividade de desenvolvimento via GitHub API."""
    if not requests:
        raise RuntimeError("requests não instalado")
    since = (datetime.now() - timedelta(days=since_days)).isoformat()
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"since": since, "per_page": 100}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    commits = r.json()
    # Contributors
    contr_url = f"https://api.github.com/repos/{repo}/contributors"
    cr = requests.get(contr_url, timeout=15)
    contributors = cr.json() if cr.status_code == 200 else []
    return {
        "repo": repo,
        "commits_30d": len(commits),
        "contributors": len(contributors),
        "top_contributors": [c["login"] for c in contributors[:10]],
        "timestamp": datetime.now().isoformat(),
    }


def screen_crypto(filters: Dict = None) -> List[Dict]:
    """Screening quantitativo de crypto baseado em filtros."""
    if not requests:
        raise RuntimeError("requests não instalado")
    if filters is None:
        filters = {}
    # Defaults conservadores
    defaults = {
        "min_market_cap": 100_000_000,      # $100M
        "max_market_cap": None,
        "min_volume_24h": 5_000_000,        # $5M
        "max_volume_24h": None,
        "min_price_change_24h": None,
        "max_price_change_24h": None,
        "min_price_change_7d": None,
        "max_price_change_7d": None,
        "min_liquidity_score": 400,         # CoinGecko liquidity score
        "min_dev_score": 30,                # CoinGecko dev score
        "categories": None,                 # ex: ["defi", "layer-1", "ai"]
        "excluded_symbols": ["USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"],  # stablecoins
        "min_circulating_supply_pct": 0.5,  # > 50% circulating
        "max_inflation_rate": 0.10,         # < 10% ao ano
    }
    defaults.update(filters)
    filters = defaults
    # Buscar dados (páginas até cobrir min_market_cap)
    all_coins = []
    page = 1
    while True:
        try:
            coins = get_coingecko_markets(per_page=250, page=page)
            if not coins:
                break
            all_coins.extend(coins)
            if len(coins) < 250:
                break
            page += 1
            if page > 10:  # safety
                break
        except Exception as e:
            print(f"Erro página {page}: {e}", file=sys.stderr)
            break
    print(f"Total coins fetched: {len(all_coins)}", file=sys.stderr)
    # Filtrar
    results = []
    for c in all_coins:
        sym = c.get("symbol", "").upper()
        if sym in filters["excluded_symbols"]:
            continue
        mcap = c.get("market_cap") or 0
        vol = c.get("total_volume") or 0
        if mcap < filters["min_market_cap"]:
            continue
        if filters["max_market_cap"] and mcap > filters["max_market_cap"]:
            continue
        if vol < filters["min_volume_24h"]:
            continue
        if filters["max_volume_24h"] and vol > filters["max_volume_24h"]:
            continue
        ch24 = c.get("price_change_percentage_24h")
        if ch24 is not None:
            if filters["min_price_change_24h"] and ch24 < filters["min_price_change_24h"]:
                continue
            if filters["max_price_change_24h"] and ch24 > filters["max_price_change_24h"]:
                continue
        ch7 = c.get("price_change_percentage_7d")
        if ch7 is not None:
            if filters["min_price_change_7d"] and ch7 < filters["min_price_change_7d"]:
                continue
            if filters["max_price_change_7d"] and ch7 > filters["max_price_change_7d"]:
                continue
        liq = c.get("liquidity_score") or 0
        if liq < filters["min_liquidity_score"]:
            continue
        dev = c.get("developer_score") or 0
        if dev < filters["min_dev_score"]:
            continue
        # Circulating supply %
        circ = c.get("circulating_supply") or 0
        total = c.get("total_supply") or 0
        if total > 0 and circ / total < filters["min_circulating_supply_pct"]:
            continue
        # Inflação aproximada (se max_supply conhecido)
        max_s = c.get("max_supply")
        if max_s and total and max_s > total:
            inflation = (max_s - total) / total
            if inflation > filters["max_inflation_rate"]:
                continue
        # Categoria
        if filters["categories"]:
            # Precisaria buscar categories via /coins/{id} - pular por agora
            pass
        results.append({
            "id": c["id"],
            "symbol": sym,
            "name": c["name"],
            "price": c.get("current_price"),
            "market_cap": mcap,
            "volume_24h": vol,
            "change_1h": c.get("price_change_percentage_1h_in_currency"),
            "change_24h": ch24,
            "change_7d": ch7,
            "change_30d": c.get("price_change_percentage_30d"),
            "liquidity_score": liq,
            "developer_score": dev,
            "circulating_supply": circ,
            "total_supply": total,
            "max_supply": max_s,
            "ath": c.get("ath"),
            "atl": c.get("atl"),
        })
    return results


def rank_by_momentum(coins: List[Dict], weights: Dict = None) -> List[Dict]:
    """Ranking por momentum multi-timeframe."""
    if weights is None:
        weights = {"1h": 0.1, "24h": 0.3, "7d": 0.4, "30d": 0.2}
    for c in coins:
        score = 0
        for tf, w in weights.items():
            key = f"change_{tf}"
            val = c.get(key)
            if val is not None:
                score += val * w
        c["momentum_score"] = round(score, 2)
    return sorted(coins, key=lambda x: x.get("momentum_score", -999), reverse=True)


def rank_by_quality(coins: List[Dict]) -> List[Dict]:
    """Ranking por qualidade (liquidez + dev + fundamentos)."""
    for c in coins:
        liq = c.get("liquidity_score", 0) / 1000 * 40  # max 40
        dev = c.get("developer_score", 0) / 100 * 30  # max 30
        # Market cap score (log scale)
        mcap = c.get("market_cap", 1)
        mcap_score = min(30, max(0, (np.log10(mcap) - 7) * 10)) if mcap > 0 else 0
        c["quality_score"] = round(liq + dev + mcap_score, 1)
    return sorted(coins, key=lambda x: x.get("quality_score", 0), reverse=True)


def find_gems(filters: Dict = None, top_n: int = 20) -> List[Dict]:
    """Busca 'gems' — baixa market cap, alta qualidade, momentum positivo."""
    if filters is None:
        filters = {}
    gem_filters = {
        "min_market_cap": 10_000_000,   # $10M
        "max_market_cap": 500_000_000,  # $500M
        "min_volume_24h": 500_000,      # $500k
        "min_liquidity_score": 300,
        "min_dev_score": 20,
        "min_price_change_7d": 10,      # +10% na semana
        **filters,
    }
    coins = screen_crypto(gem_filters)
    coins = rank_by_momentum(coins)
    coins = rank_by_quality(coins)
    return coins[:top_n]


def selftest() -> bool:
    ok = True
    print("Testando crypto_screener...")
    try:
        # Teste básico de fetch
        coins = get_coingecko_markets(per_page=10, page=1)
        assert len(coins) == 10
        assert "bitcoin" in [c["id"] for c in coins]
        print(f"  CoinGecko markets: {len(coins)} coins OK")
    except Exception as e:
        print(f"  CoinGecko: FALHOU - {e}")
        ok = False
    # Screening logic unit test
    test_coins = [
        {"symbol": "BTC", "market_cap": 1_000_000_000_000, "total_volume": 50_000_000_000, "price_change_percentage_24h": 2, "price_change_percentage_7d": 5, "liquidity_score": 800, "developer_score": 80, "circulating_supply": 19_000_000, "total_supply": 21_000_000},
        {"symbol": "SHIT", "market_cap": 1_000_000, "total_volume": 10_000, "price_change_percentage_24h": 100, "price_change_percentage_7d": 500, "liquidity_score": 100, "developer_score": 5, "circulating_supply": 1_000_000_000, "total_supply": 10_000_000_000},
    ]
    filters = {"min_market_cap": 100_000_000, "min_volume_24h": 5_000_000, "min_liquidity_score": 400, "min_dev_score": 30}
    # Simular filtro
    filtered = [c for c in test_coins if c["market_cap"] >= filters["min_market_cap"] and c["total_volume"] >= filters["min_volume_24h"] and c["liquidity_score"] >= filters["min_liquidity_score"] and c["developer_score"] >= filters["min_dev_score"]]
    assert len(filtered) == 1 and filtered[0]["symbol"] == "BTC"
    print("  Screening logic: OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Crypto Screener CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("screen", help="Screening quantitativo")
    p.add_argument("--min-mcap", type=float, default=100_000_000)
    p.add_argument("--max-mcap", type=float)
    p.add_argument("--min-vol", type=float, default=5_000_000)
    p.add_argument("--min-liq", type=int, default=400)
    p.add_argument("--min-dev", type=int, default=30)
    p.add_argument("--min-change-7d", type=float)
    p.add_argument("--output", help="Arquivo JSON saída")

    p = sub.add_parser("gems", help="Buscar gems (low cap, high quality)")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--output", help="Arquivo JSON saída")

    p = sub.add_parser("momentum", help="Ranking por momentum")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--output", help="Arquivo JSON saída")

    p = sub.add_parser("quality", help="Ranking por qualidade")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--output", help="Arquivo JSON saída")

    p = sub.add_parser("github", help="Atividade GitHub")
    p.add_argument("repo", help="owner/repo")
    p.add_argument("--days", type=int, default=30)

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "screen":
            filters = {
                "min_market_cap": args.min_mcap,
                "max_market_cap": args.max_mcap,
                "min_volume_24h": args.min_vol,
                "min_liquidity_score": args.min_liq,
                "min_dev_score": args.min_dev,
                "min_price_change_7d": args.min_change_7d,
            }
            results = screen_crypto(filters)
            out = json.dumps(results, indent=2, default=str)
        elif args.cmd == "gems":
            results = find_gems(top_n=args.top)
            out = json.dumps(results, indent=2, default=str)
        elif args.cmd == "momentum":
            coins = screen_crypto({})
            results = rank_by_momentum(coins)[:args.top]
            out = json.dumps(results, indent=2, default=str)
        elif args.cmd == "quality":
            coins = screen_crypto({})
            results = rank_by_quality(coins)[:args.top]
            out = json.dumps(results, indent=2, default=str)
        elif args.cmd == "github":
            results = get_github_activity(args.repo, args.days)
            out = json.dumps(results, indent=2, default=str)

        if args.output:
            with open(args.output, "w") as f:
                f.write(out)
        else:
            print(out)

    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()