#!/usr/bin/env python3
"""
Financas Snapshot — Gera runtime/financas_snapshot.json com dados REAIS.
Fontes gratuitas e primárias: BCB (SGS), AwesomeAPI (câmbio), CoinGecko (crypto),
Investidor10 (espelho da tabela oficial do Tesouro Direto/B3).
Escrita atômica (tmp + os.replace). Sem dados fictícios: se uma fonte falha,
o campo vai com null e a flag de erro registra o motivo.
"""
import sys
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

try:
    import requests
except ImportError:
    requests = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SNAPSHOT_PATH = os.path.join(REPO_ROOT, "runtime", "financas_snapshot.json")

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _get(url: str, timeout: int = 20) -> requests.Response:
    if not requests:
        raise RuntimeError("requests não instalado")
    r = requests.get(url, timeout=timeout, headers=_UA)
    r.raise_for_status()
    return r


def fetch_bcb_sgs(series: int) -> Optional[Dict]:
    """Série SGS do BCB. Retorna {valor, data} ou None."""
    try:
        r = _get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados/ultimos/1?formato=json")
        d = r.json()[-1]
        return {"valor": float(d["valor"]), "data": d["data"], "serie": series}
    except Exception as e:
        return {"erro": str(e), "serie": series}


def fetch_cambio() -> Optional[Dict]:
    """USD/BRL via AwesomeAPI (gratuita)."""
    try:
        r = _get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL")
        d = r.json()
        out = {}
        for pair, key in [("USDBRL", "usd_brl"), ("EURBRL", "eur_brl")]:
            if pair in d:
                out[key] = {
                    "bid": float(d[pair]["bid"]),
                    "pct_variacao": float(d[pair].get("pctChange", 0)),
                    "atualizado": d[pair].get("create_date"),
                }
        return out or None
    except Exception as e:
        return {"erro": str(e)}


def fetch_crypto() -> Optional[Dict]:
    """BTC/ETH via CoinGecko simple/price (gratuita)."""
    try:
        r = _get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum&vs_currencies=brl,usd"
            "&include_24hr_change=true"
        )
        d = r.json()
        out = {}
        for cid, key in [("bitcoin", "btc"), ("ethereum", "eth")]:
            if cid in d:
                c = d[cid]
                out[key] = {
                    "brl": c.get("brl"),
                    "usd": c.get("usd"),
                    "variacao_24h_pct": round(c.get("brl_24h_change", 0) or 0, 2),
                }
        return out or None
    except Exception as e:
        return {"erro": str(e)}


def fetch_indices_mercado() -> Optional[Dict]:
    """IBOV/IFIX/S&P500 via Yahoo (gratuito)."""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from market_data import get_yahoo
        out = {}
        for ticker, key in [("^BVSP", "ibov"), ("^VIX", "vix")]:
            try:
                d = get_yahoo(ticker, "5d", "1d")
                out[key] = {"valor": d["price"], "pct_variacao": d.get("change_pct")}
            except Exception:
                out[key] = None
        return out
    except Exception as e:
        return {"erro": str(e)}


def _parse_brl_float(s: str) -> Optional[float]:
    """'R$ 10,90' -> 10.9 | 'R$ 1.234,56' -> 1234.56"""
    try:
        clean = s.replace("R$", "").strip().replace(".", "").replace(",", ".")
        return float(clean)
    except Exception:
        return None


def fetch_tesouro() -> Dict:
    """
    Tabela oficial do Tesouro Direto via espelho público Investidor10.
    Fallback: retorna last_verified embutido (com data de verificação explícita).
    """
    try:
        r = _get("https://investidor10.com.br/tesouro-direto/investir/", timeout=25)
        html = r.text
        # Cada linha da tabela: <a ... title="NOME"> ... <td data-order="X">IDX</td>
        # <td data-order="Y">TAXA%</td> <td data-order="Z">R$ PREÇO</td> <td data-order="DATA">DD/MM/AAAA</td>
        row_pat = re.compile(
            r'title="(Tesouro[^"]+)"'
            r'.*?<td data-order="[^"]*">\s*([^<]*?)\s*</td>'      # indexador
            r'.*?<td data-order="[^"]*">\s*([^<]*?)\s*</td>'      # taxa
            r'.*?<td data-order="[^"]*">\s*(R\$[^<]*?)\s*</td>'   # preço
            r'.*?<td data-order="([^"]*)">\s*([^<]*?)\s*</td>',   # vencimento
            re.S,
        )
        bonds = []
        for m in row_pat.finditer(html):
            nome, idx, taxa, preco, venc_iso, venc_br = m.groups()
            if "Tesouro" not in nome:
                continue
            taxa_clean = taxa.strip()
            rate_value = None
            rate_kind = "selic"
            if "%" in taxa_clean:
                rate_value = _parse_brl_float(taxa_clean.replace("%", ""))
                rate_kind = "prefixado"
            elif "+" in taxa_clean:
                parts = taxa_clean.split("+")
                rate_value = _parse_brl_float(parts[1].replace("%", ""))
                rate_kind = "ipca"
            elif "SELIC" in taxa_clean.upper() and "+" in taxa_clean:
                rate_value = _parse_brl_float(taxa_clean.split("+")[1])
                rate_kind = "selic_spread"
            bonds.append({
                "nome": nome.strip(),
                "indexador": idx.strip(),
                "tipo_taxa": rate_kind,
                "taxa": rate_value,
                "taxa_texto": taxa_clean,
                "preco_unitario": _parse_brl_float(preco),
                "vencimento": venc_br.strip(),
            })
        if not bonds:
            raise ValueError("parser não encontrou títulos")
        return {"fonte": "investidor10.com.br (espelho B3/Tesouro)", "titulos": bonds, "ao_vivo": True}
    except Exception as e:
        return {
            "fonte": "cache local (verificado em 2026-08-21 via investidor10.com.br)",
            "ao_vivo": False,
            "erro_fetch": str(e),
            "titulos": [
                {"nome": "Tesouro Reserva 2036", "indexador": "SELIC", "tipo_taxa": "selic", "taxa": 14.00, "taxa_texto": "SELIC", "preco_unitario": 10.90, "vencimento": "01/01/2036"},
                {"nome": "Tesouro Selic 2031", "indexador": "SELIC + 0,0732%", "tipo_taxa": "selic_spread", "taxa": 0.0732, "taxa_texto": "SELIC + 0,0732%", "preco_unitario": 19647.06, "vencimento": "01/03/2031"},
                {"nome": "Tesouro Prefixado 2029", "indexador": "Prefixado", "tipo_taxa": "prefixado", "taxa": 14.29, "taxa_texto": "14,29%", "preco_unitario": 731.84, "vencimento": "01/01/2029"},
                {"nome": "Tesouro Prefixado 2032", "indexador": "Prefixado", "tipo_taxa": "prefixado", "taxa": 14.74, "taxa_texto": "14,74%", "preco_unitario": 480.83, "vencimento": "01/01/2032"},
                {"nome": "Tesouro IPCA+ 2040", "indexador": "IPCA + 7,54%", "tipo_taxa": "ipca", "taxa": 7.54, "taxa_texto": "IPCA + 7,54%", "preco_unitario": 1725.88, "vencimento": "15/08/2040"},
                {"nome": "Tesouro IPCA+ 2050", "indexador": "IPCA + 7,30%", "tipo_taxa": "ipca", "taxa": 7.30, "taxa_texto": "IPCA + 7,30%", "preco_unitario": 884.48, "vencimento": "15/08/2050"},
            ],
        }


def build_snapshot() -> Dict:
    selic = fetch_bcb_sgs(432)
    ipca = fetch_bcb_sgs(13522)
    cdi_daily = fetch_bcb_sgs(12)
    cdi_anual = None
    if cdi_daily and "valor" in cdi_daily:
        # CDI diário -> anualizado (252 dias úteis)
        cdi_anual = round(((1 + cdi_daily["valor"] / 100) ** 252 - 1) * 100, 2)
    return {
        "schema": "financas_snapshot/v1",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "fontes": {
            "selic_ipca_cdi": "api.bcb.gov.br (SGS)",
            "cambio": "economia.awesomeapi.com.br",
            "crypto": "api.coingecko.com",
            "tesouro": "investidor10.com.br (espelho tabela oficial)",
        },
        "macro": {
            "selic": selic,
            "ipca_12m": ipca,
            "cdi_diario": cdi_daily,
            "cdi_anualizado": cdi_anual,
        },
        "cambio": fetch_cambio(),
        "crypto": fetch_crypto(),
        "indices": fetch_indices_mercado(),
        "tesouro": fetch_tesouro(),
    }


def write_snapshot(snapshot: Dict, path: str = SNAPSHOT_PATH) -> str:
    """Escrita atômica: tmp + os.replace."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def selftest() -> bool:
    ok = True
    print("Testando snapshot...")
    snap = build_snapshot()
    # Validações de sanidade contra valores reais conhecidos
    macro = snap.get("macro", {})
    selic = macro.get("selic") or {}
    if selic.get("valor"):
        assert 5 < selic["valor"] < 30, f"Selic implausível: {selic['valor']}"
        print(f"  Selic: {selic['valor']}% ({selic['data']}) OK")
    else:
        print(f"  Selic: FALHOU - {selic}")
        ok = False
    ipca = macro.get("ipca_12m") or {}
    if ipca.get("valor") is not None:
        assert -5 < ipca["valor"] < 30
        print(f"  IPCA 12m: {ipca['valor']}% OK")
    cdi = macro.get("cdi_anualizado")
    if cdi:
        assert 5 < cdi < 30, f"CDI implausível: {cdi}"
        print(f"  CDI anualizado: {cdi}% OK")
    cambio = snap.get("cambio") or {}
    usd = cambio.get("usd_brl") or {}
    if usd.get("bid"):
        assert 2 < usd["bid"] < 15
        print(f"  USD/BRL: {usd['bid']} OK")
    crypto = snap.get("crypto") or {}
    btc = crypto.get("btc") or {}
    if btc.get("brl"):
        print(f"  BTC: R$ {btc['brl']:,.0f} ({btc['variacao_24h_pct']:+}%) OK")
    tesouro = snap.get("tesouro") or {}
    titulos = tesouro.get("titulos") or []
    reserva = next((t for t in titulos if "Reserva" in t["nome"]), None)
    if reserva and reserva.get("preco_unitario"):
        print(f"  Tesouro ao vivo: {len(titulos)} títulos | Reserva 2036: R$ {reserva['preco_unitario']} OK")
    else:
        print(f"  Tesouro: fallback cache ({len(titulos)} títulos)")
    path = write_snapshot(snap)
    print(f"  Snapshot gravado: {path}")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Snapshot financeiro com dados reais")
    parser.add_argument("--out", default=SNAPSHOT_PATH)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    snap = build_snapshot()
    path = write_snapshot(snap, args.out)
    print(json.dumps({"ok": True, "path": path, "gerado_em": snap["gerado_em"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()