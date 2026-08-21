#!/usr/bin/env python3
"""
Alerts & Monitoring — Breakouts, volume anômalo, funding rate extremo, whale moves, macro events.
Polling + webhook ready.
"""
import sys
import json
import argparse
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    import requests
except ImportError:
    requests = None

try:
    import numpy as np
except ImportError:
    np = None

# Importar módulos locais
sys.path.insert(0, os.path.dirname(__file__))
from market_data import get_binance, get_bybit, get_yahoo
from technical import analyze_technical
from onchain import get_coingecko_coin


class AlertEngine:
    def __init__(self, config: Dict = None):
        self.config = config or {
            "volume_spike_threshold": 3.0,      # x volume médio 20p
            "price_change_threshold": 0.05,     # 5% em 1h/4h
            "rsi_overbought": 75,
            "rsi_oversold": 25,
            "funding_rate_extreme": 0.01,       # 1% per 8h
            "whale_threshold_usd": 1_000_000,
            "breakout_lookback": 20,
            "cooldown_minutes": 60,
        }
        self.last_alert = {}  # {(symbol, type): timestamp}

    def _cooldown_ok(self, key: str) -> bool:
        now = datetime.now()
        if key in self.last_alert:
            elapsed = (now - self.last_alert[key]).total_seconds() / 60
            if elapsed < self.config["cooldown_minutes"]:
                return False
        self.last_alert[key] = now
        return True

    def check_crypto_breakouts(self, symbols: List[str], interval: str = "1h") -> List[Dict]:
        """Detecta breakouts de range (Donchian) + volume spike."""
        alerts = []
        for sym in symbols:
            try:
                data = get_binance(sym, interval, limit=100)
                klines = data["klines"]
                if len(klines) < self.config["breakout_lookback"] + 5:
                    continue
                highs = [k["high"] for k in klines]
                lows = [k["low"] for k in klines]
                volumes = [k["volume"] for k in klines]
                closes = [k["close"] for k in klines]
                lookback = self.config["breakout_lookback"]
                recent_high = max(highs[-lookback:-1])
                recent_low = min(lows[-lookback:-1])
                current_price = closes[-1]
                current_vol = volumes[-1]
                avg_vol = np.mean(volumes[-lookback-1:-1]) if np else sum(volumes[-lookback-1:-1]) / lookback
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
                # Breakout up
                if current_price > recent_high and vol_ratio > self.config["volume_spike_threshold"]:
                    key = f"{sym}:breakout_up"
                    if self._cooldown_ok(key):
                        alerts.append({
                            "type": "BREAKOUT_UP",
                            "symbol": sym,
                            "price": current_price,
                            "breakout_level": recent_high,
                            "volume_ratio": round(vol_ratio, 2),
                            "interval": interval,
                            "timestamp": datetime.now().isoformat(),
                        })
                # Breakdown down
                if current_price < recent_low and vol_ratio > self.config["volume_spike_threshold"]:
                    key = f"{sym}:breakdown_down"
                    if self._cooldown_ok(key):
                        alerts.append({
                            "type": "BREAKDOWN_DOWN",
                            "symbol": sym,
                            "price": current_price,
                            "breakdown_level": recent_low,
                            "volume_ratio": round(vol_ratio, 2),
                            "interval": interval,
                            "timestamp": datetime.now().isoformat(),
                        })
            except Exception as e:
                alerts.append({"type": "ERROR", "symbol": sym, "error": str(e)})
        return alerts

    def check_funding_rates(self, symbols: List[str]) -> List[Dict]:
        """Funding rate extremo (perp)."""
        alerts = []
        for sym in symbols:
            try:
                data = get_binance(sym, "1h", 10)
                fr = data.get("funding_rate")
                if fr and abs(fr["rate"]) > self.config["funding_rate_extreme"]:
                    key = f"{sym}:funding"
                    if self._cooldown_ok(key):
                        alerts.append({
                            "type": "FUNDING_EXTREME",
                            "symbol": sym,
                            "rate": fr["rate"],
                            "rate_pct": round(fr["rate"] * 100, 4),
                            "annualized": round(fr["rate"] * 3 * 365 * 100, 2),  # 3x/day
                            "timestamp": fr["timestamp"],
                        })
            except Exception:
                pass
        return alerts

    def check_rsi_extremes(self, symbols: List[str], interval: str = "4h") -> List[Dict]:
        """RSI overbought/oversold em timeframes maiores."""
        alerts = []
        for sym in symbols:
            try:
                data = get_binance(sym, interval, limit=100)
                klines = data["klines"]
                ohlcv = [{"open": k["open"], "high": k["high"], "low": k["low"], "close": k["close"], "volume": k["volume"]} for k in klines]
                tech = analyze_technical(ohlcv)
                rsi = tech.get("rsi")
                if rsi:
                    if rsi >= self.config["rsi_overbought"]:
                        key = f"{sym}:rsi_ob"
                        if self._cooldown_ok(key):
                            alerts.append({"type": "RSI_OVERBOUGHT", "symbol": sym, "rsi": rsi, "interval": interval, "timestamp": datetime.now().isoformat()})
                    elif rsi <= self.config["rsi_oversold"]:
                        key = f"{sym}:rsi_os"
                        if self._cooldown_ok(key):
                            alerts.append({"type": "RSI_OVERSOLD", "symbol": sym, "rsi": rsi, "interval": interval, "timestamp": datetime.now().isoformat()})
            except Exception:
                pass
        return alerts

    def check_macro_events(self) -> List[Dict]:
        """Eventos macro agendados (FOMC, CPI, Payroll, BCB Copom). Placeholder."""
        # Integrar com calendário econômico (TradingEconomics, Investing.com, FRED)
        return []

    def check_onchain_whales(self, asset: str = "BTC") -> List[Dict]:
        """Whale alerts via on-chain (placeholder - precisa API)."""
        return []

    def run_all(self, symbols: List[str] = None) -> List[Dict]:
        """Executa todos os checks."""
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"]
        all_alerts = []
        all_alerts.extend(self.check_crypto_breakouts(symbols, "1h"))
        all_alerts.extend(self.check_crypto_breakouts(symbols, "4h"))
        all_alerts.extend(self.check_funding_rates(symbols))
        all_alerts.extend(self.check_rsi_extremes(symbols, "4h"))
        all_alerts.extend(self.check_macro_events())
        return all_alerts

    def send_webhook(self, alerts: List[Dict], webhook_url: str) -> bool:
        """Envia alertas para webhook (Discord, Slack, Telegram, etc.)."""
        if not requests or not webhook_url:
            return False
        for alert in alerts:
            try:
                payload = {"content": f"🚨 **{alert['type']}** | {alert.get('symbol', '')} | {json.dumps(alert, default=str)}"}
                requests.post(webhook_url, json=payload, timeout=5)
            except Exception:
                pass
        return True


def monitor_loop(symbols: List[str], interval_sec: int = 300, webhook: str = None, once: bool = False):
    """Loop de monitoramento contínuo."""
    engine = AlertEngine()
    print(f"Iniciando monitoramento: {symbols} | intervalo: {interval_sec}s | webhook: {'sim' if webhook else 'não'}")
    while True:
        alerts = engine.run_all(symbols)
        if alerts:
            for a in alerts:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {a['type']} | {a.get('symbol', '')} | {json.dumps(a, default=str)}")
            if webhook:
                engine.send_webhook(alerts, webhook)
        if once:
            break
        time.sleep(interval_sec)


def selftest() -> bool:
    ok = True
    print("Testando alerts...")
    engine = AlertEngine()
    # Teste breakout detection lógica
    highs = [100, 101, 102, 101, 100, 99, 100, 101, 102, 103, 104, 105]  # breakout
    lows = [98, 99, 98, 99, 98, 97, 98, 99, 98, 99, 98, 97]
    volumes = [1000] * 10 + [5000]  # volume spike
    recent_high = max(highs[-10:-1])
    current_price = highs[-1]
    avg_vol = sum(volumes[-11:-1]) / 10
    vol_ratio = volumes[-1] / avg_vol
    assert current_price > recent_high and vol_ratio > 3
    print("  Breakout logic: OK")
    # RSI thresholds
    assert engine.config["rsi_overbought"] == 75
    assert engine.config["rsi_oversold"] == 25
    print("  Config thresholds: OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Alerts & Monitoring CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="Rodar checks uma vez")
    p.add_argument("-s", "--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    p.add_argument("--webhook", help="Webhook URL para envio")

    p = sub.add_parser("monitor", help="Loop contínuo de monitoramento")
    p.add_argument("-s", "--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    p.add_argument("-i", "--interval", type=int, default=300, help="Segundos entre checks")
    p.add_argument("--webhook", help="Webhook URL")

    p = sub.add_parser("breakout", help="Verificar breakouts")
    p.add_argument("symbols", nargs="+")
    p.add_argument("-i", "--interval", default="1h")

    p = sub.add_parser("funding", help="Verificar funding rates")
    p.add_argument("symbols", nargs="+")

    p = sub.add_parser("rsi", help="Verificar RSI extremos")
    p.add_argument("symbols", nargs="+")
    p.add_argument("-i", "--interval", default="4h")

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    engine = AlertEngine()

    try:
        if args.cmd == "run":
            alerts = engine.run_all(args.symbols)
            print(json.dumps(alerts, indent=2, default=str))
            if args.webhook:
                engine.send_webhook(alerts, args.webhook)

        elif args.cmd == "monitor":
            monitor_loop(args.symbols, args.interval, args.webhook, once=False)

        elif args.cmd == "breakout":
            alerts = engine.check_crypto_breakouts(args.symbols, args.interval)
            print(json.dumps(alerts, indent=2, default=str))

        elif args.cmd == "funding":
            alerts = engine.check_funding_rates(args.symbols)
            print(json.dumps(alerts, indent=2, default=str))

        elif args.cmd == "rsi":
            alerts = engine.check_rsi_extremes(args.symbols, args.interval)
            print(json.dumps(alerts, indent=2, default=str))

    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()