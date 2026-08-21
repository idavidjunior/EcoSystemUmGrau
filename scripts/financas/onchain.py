#!/usr/bin/env python3
"""
On-chain Metrics — NVT, MVRV, SOPR, exchange flows, whale alerts, staking.
Fontes: Glassnode (precisa API key), CoinGecko (gratuito), DefiLlama (gratuito), Blockchain.com, CryptoQuant.
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

_cache = {}
_CACHE_TTL = 300  # 5 min para on-chain


def _cache_get(key: str) -> Optional[Any]:
    if key in _cache:
        val, ts = _cache[key]
        if (datetime.now() - ts).total_seconds() < _CACHE_TTL:
            return val
    return None


def _cache_set(key: str, val: Any):
    _cache[key] = (val, datetime.now())


def get_coingecko_coin(coin_id: str) -> Dict:
    """Dados básicos + market data via CoinGecko (gratuito, rate limited)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get(f"coingecko:{coin_id}")
    if cached:
        return cached
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "true",
        "developer_data": "true",
        "sparkline": "false",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    md = data.get("market_data", {})
    result = {
        "id": data["id"],
        "symbol": data["symbol"].upper(),
        "name": data["name"],
        "price_usd": md.get("current_price", {}).get("usd"),
        "price_btc": md.get("current_price", {}).get("btc"),
        "market_cap_usd": md.get("market_cap", {}).get("usd"),
        "volume_24h_usd": md.get("total_volume", {}).get("usd"),
        "change_24h": md.get("price_change_percentage_24h"),
        "change_7d": md.get("price_change_percentage_7d"),
        "change_30d": md.get("price_change_percentage_30d"),
        "ath": md.get("ath", {}).get("usd"),
        "ath_change_pct": md.get("ath_change_percentage", {}).get("usd"),
        "atl": md.get("atl", {}).get("usd"),
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "developer_score": data.get("developer_score"),
        "community_score": data.get("community_score"),
        "liquidity_score": data.get("liquidity_score"),
        "public_interest_score": data.get("public_interest_score"),
        "last_updated": md.get("last_updated"),
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set(f"coingecko:{coin_id}", result)
    return result


def get_defillama_protocol(slug: str) -> Dict:
    """TVL, revenue, fees, chain breakdown via DefiLlama."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get(f"defillama:{slug}")
    if cached:
        return cached
    url = f"https://api.llama.fi/protocol/{slug}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    # API retorna tvl como série histórica [{date, totalLiquidityUSD}, ...]
    tvl_series = data.get("tvl") or []
    current_tvl = None
    if isinstance(tvl_series, list) and tvl_series:
        last_point = tvl_series[-1]
        if isinstance(last_point, dict):
            current_tvl = last_point.get("totalLiquidityUSD")
        elif isinstance(last_point, (int, float)):
            current_tvl = last_point
    result = {
        "name": data.get("name"),
        "slug": data.get("slug"),
        "tvl": current_tvl,
        "chain_tvls": data.get("chainTvls"),
        "category": data.get("category"),
        "chains": data.get("chains"),
        "github": data.get("github"),
        "twitter": data.get("twitter"),
        "url": data.get("url"),
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set(f"defillama:{slug}", result)
    return result


def get_defillama_chains() -> List[Dict]:
    """TVL por chain."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get("defillama:chains")
    if cached:
        return cached
    url = "https://api.llama.fi/v2/chains"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    _cache_set("defillama:chains", data)
    return data


def get_glassnode_metric(metric: str, asset: str = "BTC", interval: str = "24h", since: int = None, until: int = None, api_key: str = None) -> Dict:
    """Glassnode API — precisa key paga. Retorna série temporal."""
    if not requests:
        raise RuntimeError("requests não instalado")
    if not api_key:
        api_key = os.getenv("GLASSNODE_API_KEY")
    if not api_key:
        raise RuntimeError("GLASSNODE_API_KEY não definido")
    url = f"https://api.glassnode.com/v1/metrics/{metric}"
    params = {"a": asset, "i": interval, "api_key": api_key}
    if since:
        params["s"] = since
    if until:
        params["u"] = until
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return {"metric": metric, "asset": asset, "data": data, "timestamp": datetime.now().isoformat()}


def get_blockchain_com_charts(metric: str, timespan: str = "30days") -> Dict:
    """Blockchain.com charts públicos (gratuito). Metrics: market-price, trade-volume, estimated-transaction-volume, n-transactions, n-unique-addresses, hash-rate, difficulty, miners-revenue, transaction-fees, mempool-size, avg-block-size, utxo-count."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get(f"blockchain:{metric}:{timespan}")
    if cached:
        return cached
    url = f"https://api.blockchain.info/charts/{metric}"
    params = {"timespan": timespan, "format": "json", "cors": "true"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    result = {"metric": metric, "timespan": timespan, "data": data.get("values", []), "timestamp": datetime.now().isoformat()}
    _cache_set(f"blockchain:{metric}:{timespan}", result)
    return result


def compute_nvt(market_cap_usd: float, tx_volume_usd_24h: float) -> Optional[float]:
    """NVT = Market Cap / Transacted Volume (24h). Alto = sobrevalorizado."""
    if tx_volume_usd_24h and tx_volume_usd_24h > 0:
        return market_cap_usd / tx_volume_usd_24h
    return None


def compute_mvrv(market_cap_usd: float, realized_cap_usd: float) -> Optional[float]:
    """MVRV = Market Cap / Realized Cap. > 3.5 = topo histórico, < 1 = fundo."""
    if realized_cap_usd and realized_cap_usd > 0:
        return market_cap_usd / realized_cap_usd
    return None


def compute_sopr(realized_value_usd: float, created_value_usd: float) -> Optional[float]:
    """SOPR = Realized Value / Created Value. > 1 = lucro, < 1 = prejuízo."""
    if created_value_usd and created_value_usd > 0:
        return realized_value_usd / created_value_usd
    return None


def get_exchange_flows(asset: str = "BTC", api_key: str = None) -> Dict:
    """Exchange netflow via CryptoQuant/Glassnode (precisa key). Placeholder para estrutura."""
    if not requests:
        raise RuntimeError("requests não instalado")
    # Implementar com CryptoQuant API se tiver key
    return {"asset": asset, "note": "Requer API key CryptoQuant ou Glassnode", "timestamp": datetime.now().isoformat()}


def get_whale_alerts(min_usd: float = 1000000, api_key: str = None) -> List[Dict]:
    """Whale Alert API (precisa key). Placeholder."""
    return [{"note": "Requer Whale Alert API key", "timestamp": datetime.now().isoformat()}]


def get_staking_data(asset: str) -> Dict:
    """Staking ratio, yield, validators via Staking Rewards / Beaconcha.in / DefiLlama."""
    if not requests:
        raise RuntimeError("requests não instalado")
    # Placeholder - integrar com APIs específicas
    return {"asset": asset, "note": "Implementar com Staking Rewards API / Beaconcha.in", "timestamp": datetime.now().isoformat()}


def selftest() -> bool:
    ok = True
    print("Testando onchain...")
    try:
        d = get_coingecko_coin("bitcoin")
        assert "price_usd" in d and d["price_usd"] > 0
        print(f"  CoinGecko BTC: ${d['price_usd']:,.0f} OK")
    except Exception as e:
        print(f"  CoinGecko: FALHOU - {e}")
        ok = False
    try:
        d = get_defillama_protocol("lido")
        assert "tvl" in d and d["tvl"] > 0
        print(f"  DefiLlama Lido: TVL ${d['tvl']:,.0f} OK")
    except Exception as e:
        print(f"  DefiLlama: FALHOU - {e}")
        ok = False
    try:
        chains = get_defillama_chains()
        assert len(chains) > 10
        print(f"  DefiLlama Chains: {len(chains)} chains OK")
    except Exception as e:
        print(f"  Chains: FALHOU - {e}")
        ok = False
    # NVT/MVRV/SOPR unit tests
    assert compute_nvt(1_000_000_000, 100_000_000) == 10.0
    assert compute_mvrv(1_000_000_000, 500_000_000) == 2.0
    assert compute_sopr(110, 100) == 1.1
    print("  Métricas calculadas: OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="On-chain Metrics CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("coingecko", help="CoinGecko coin data")
    p.add_argument("coin_id")

    p = sub.add_parser("defillama", help="DefiLlama protocol")
    p.add_argument("slug")

    p = sub.add_parser("chains", help="DefiLlama chains TVL")

    p = sub.add_parser("glassnode", help="Glassnode metric (precisa key)")
    p.add_argument("metric")
    p.add_argument("-a", "--asset", default="BTC")
    p.add_argument("-i", "--interval", default="24h")
    p.add_argument("--since", type=int)
    p.add_argument("--until", type=int)
    p.add_argument("--key")

    p = sub.add_parser("blockchain", help="Blockchain.com chart")
    p.add_argument("metric")
    p.add_argument("-t", "--timespan", default="30days")

    p = sub.add_parser("nvt", help="Calcular NVT")
    p.add_argument("market_cap", type=float)
    p.add_argument("tx_volume", type=float)

    p = sub.add_parser("mvrv", help="Calcular MVRV")
    p.add_argument("market_cap", type=float)
    p.add_argument("realized_cap", type=float)

    p = sub.add_parser("sopr", help="Calcular SOPR")
    p.add_argument("realized", type=float)
    p.add_argument("created", type=float)

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "coingecko":
            print(json.dumps(get_coingecko_coin(args.coin_id), indent=2, default=str))
        elif args.cmd == "defillama":
            print(json.dumps(get_defillama_protocol(args.slug), indent=2, default=str))
        elif args.cmd == "chains":
            print(json.dumps(get_defillama_chains(), indent=2, default=str))
        elif args.cmd == "glassnode":
            print(json.dumps(get_glassnode_metric(args.metric, args.asset, args.interval, args.since, args.until, args.key), indent=2, default=str))
        elif args.cmd == "blockchain":
            print(json.dumps(get_blockchain_com_charts(args.metric, args.timespan), indent=2, default=str))
        elif args.cmd == "nvt":
            print(f"NVT: {compute_nvt(args.market_cap, args.tx_volume):.2f}")
        elif args.cmd == "mvrv":
            print(f"MVRV: {compute_mvrv(args.market_cap, args.realized_cap):.2f}")
        elif args.cmd == "sopr":
            print(f"SOPR: {compute_sopr(args.realized, args.created):.4f}")
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()