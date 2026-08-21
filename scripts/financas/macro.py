#!/usr/bin/env python3
"""
Macro Data — Selic, IPCA, DXY, yields, VIX, PMI, payroll, CPI/PPI.
Fontes: BCB (Brasil), FRED (US), TradingEconomics, Investing.com.
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
_CACHE_TTL = 3600  # 1h


def _cache_get(key):
    if key in _cache:
        val, ts = _cache[key]
        if (datetime.now() - ts).total_seconds() < _CACHE_TTL:
            return val
    return None


def _cache_set(key, val):
    _cache[key] = (val, datetime.now())


def get_bcb_selic() -> Dict:
    """Selic meta atual via API do Banco Central (gratuito)."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get("bcb_selic")
    if cached:
        return cached
    # SGS série 432 = Selic meta definida pelo Copom
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    result = {
        "indicator": "Selic Meta",
        "value": float(data[-1]["valor"]),
        "date": data[-1]["data"],
        "source": "BCB SGS 432",
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set("bcb_selic", result)
    return result


def get_bcb_ipca() -> Dict:
    """IPCA acumulado 12 meses via BCB."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get("bcb_ipca")
    if cached:
        return cached
    # SGS série 13522 = IPCA acumulado 12 meses
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    result = {
        "indicator": "IPCA 12m",
        "value": float(data[-1]["valor"]),
        "date": data[-1]["data"],
        "source": "BCB SGS 13522",
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set("bcb_ipca", result)
    return result


def get_bcb_dolar() -> Dict:
    """Cotação USD/BRL via BCB."""
    if not requests:
        raise RuntimeError("requests não instalado")
    cached = _cache_get("bcb_dolar")
    if cached:
        return cached
    url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@dataInicial='08-01-2026'&@dataFinalCotacao='08-21-2026'&$format=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    values = data.get("value", [])
    if not values:
        raise ValueError("Sem dados PTAX")
    last = values[-1]
    result = {
        "indicator": "USD/BRL PTAX",
        "value": float(last["cotacaoVenda"]),
        "date": last["dataHoraCotacao"],
        "source": "BCB PTAX",
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set("bcb_dolar", 0)  # cache curto para dólar
    return result


def get_fred_series(series_id: str, api_key: str = None) -> Dict:
    """Série FRED — precisa key gratuita."""
    if not requests:
        raise RuntimeError("requests não instalado")
    if not api_key:
        api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY não definido")
    cached = _cache_get(f"fred:{series_id}")
    if cached:
        return cached
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    obs = data.get("observations", [])
    result = {
        "series": series_id,
        "observations": obs,
        "latest": obs[0] if obs else None,
        "timestamp": datetime.now().isoformat(),
    }
    _cache_set(f"fred:{series_id}", result)
    return result


def get_us_yield_curve(api_key: str = None) -> Dict:
    """Yield curve US via FRED (DGS2, DGS10, DGS30)."""
    results = {}
    for tenor in ["DGS2", "DGS10", "DGS30"]:
        try:
            d = get_fred_series(tenor, api_key)
            results[tenor] = d["latest"]["value"]
        except Exception as e:
            results[tenor] = f"erro: {e}"
    # Inversion check
    try:
        y2 = float(results["DGS2"])
        y10 = float(results["DGS10"])
        results["curve_inverted"] = y2 > y10
        results["spread_2s10s"] = round(y10 - y2, 3)
    except Exception:
        pass
    return results


def get_vix() -> Dict:
    """VIX via Yahoo Finance."""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from market_data import get_yahoo
        d = get_yahoo("^VIX", "5d", "1d")
        return {
            "indicator": "VIX",
            "value": d["price"],
            "change_pct": d["change_pct"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"indicator": "VIX", "error": str(e)}


def get_macro_snapshot(api_key: str = None) -> Dict:
    """Snapshot macro completo BR + US."""
    snapshot = {"timestamp": datetime.now().isoformat()}
    # Brasil
    try:
        snapshot["brasil"] = {
            "selic": get_bcb_selic(),
            "ipca": get_bcb_ipca(),
            "dolar": get_bcb_dolar(),
        }
    except Exception as e:
        snapshot["brasil"] = {"error": str(e)}
    # EUA
    try:
        snapshot["eua"] = {
            "yield_curve": get_us_yield_curve(api_key),
            "vix": get_vix(),
        }
    except Exception as e:
        snapshot["eua"] = {"error": str(e)}
    return snapshot


def selftest() -> bool:
    ok = True
    print("Testando macro...")
    try:
        s = get_bcb_selic()
        assert s["value"] > 0
        print(f"  BCB Selic: {s['value']}% ({s['date']}) OK")
    except Exception as e:
        print(f"  Selic: FALHOU - {e}")
        ok = False
    try:
        i = get_bcb_ipca()
        assert i["value"] >= 0
        print(f"  BCB IPCA 12m: {i['value']}% OK")
    except Exception as e:
        print(f"  IPCA: FALHOU - {e}")
        ok = False
    try:
        v = get_vix()
        if "value" in v:
            print(f"  VIX: {v['value']:.1f} OK")
        else:
            print(f"  VIX: {v.get('error')}")
    except Exception as e:
        print(f"  VIX: FALHOU - {e}")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Macro Data CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("selic", help="Selic meta")
    p = sub.add_parser("ipca", help="IPCA 12m")
    p = sub.add_parser("dolar", help="USD/BRL PTAX")
    p.add_argument("--key", help="FRED API key")

    p = sub.add_parser("fred", help="Série FRED")
    p.add_argument("series_id")
    p.add_argument("--key")

    p = sub.add_parser("yieldcurve", help="Yield curve US")
    p.add_argument("--key")

    p = sub.add_parser("vix", help="VIX")

    p = sub.add_parser("snapshot", help="Snapshot macro completo")
    p.add_argument("--key")

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "selic":
            print(json.dumps(get_bcb_selic(), indent=2))
        elif args.cmd == "ipca":
            print(json.dumps(get_bcb_ipca(), indent=2))
        elif args.cmd == "dolar":
            print(json.dumps(get_bcb_dolar(), indent=2))
        elif args.cmd == "fred":
            print(json.dumps(get_fred_series(args.series_id, args.key), indent=2))
        elif args.cmd == "yieldcurve":
            print(json.dumps(get_us_yield_curve(args.key), indent=2))
        elif args.cmd == "vix":
            print(json.dumps(get_vix(), indent=2))
        elif args.cmd == "snapshot":
            print(json.dumps(get_macro_snapshot(args.key), indent=2))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()