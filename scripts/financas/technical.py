#!/usr/bin/env python3
"""
Technical Analysis — RSI, MACD, Bollinger, VWAP, OBV, Wyckoff, order flow.
Implementação própria (sem TA-Lib dependency) + pandas-ta opcional.
"""
import sys
import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import math

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False


def _ensure_pandas():
    if pd is None:
        raise RuntimeError("pandas/numpy não instalados: pip install pandas numpy")


def _to_dataframe(ohlcv: List[Dict]) -> "pd.DataFrame":
    """Converte lista de dicts OHLCV para DataFrame com colunas padrão."""
    df = pd.DataFrame(ohlcv)
    # Normalizar nomes de colunas
    col_map = {
        "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume",
        "o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume",
    }
    df.columns = [col_map.get(c.lower(), c) for c in df.columns]
    # Garantir tipos
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    return df


def rsi(series: "pd.Series", period: int = 14) -> "pd.Series":
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: "pd.Series", fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, "pd.Series"]:
    """MACD line, signal line, histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bollinger_bands(series: "pd.Series", period: int = 20, std_dev: float = 2.0) -> Dict[str, "pd.Series"]:
    """Bollinger Bands: upper, middle (SMA), lower."""
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    return {
        "upper": sma + std_dev * std,
        "middle": sma,
        "lower": sma - std_dev * std,
        "width": (2 * std_dev * std) / sma,  # Bandwidth
        "percent_b": (series - (sma - std_dev * std)) / (2 * std_dev * std),  # %B
    }


def vwap(high: "pd.Series", low: "pd.Series", close: "pd.Series", volume: "pd.Series") -> "pd.Series":
    """Volume Weighted Average Price."""
    typical = (high + low + close) / 3
    return (typical * volume).cumsum() / volume.cumsum()


def obv(close: "pd.Series", volume: "pd.Series") -> "pd.Series":
    """On-Balance Volume."""
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def atr(high: "pd.Series", low: "pd.Series", close: "pd.Series", period: int = 14) -> "pd.Series":
    """Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def adx(high: "pd.Series", low: "pd.Series", close: "pd.Series", period: int = 14) -> Dict[str, "pd.Series"]:
    """Average Directional Index."""
    plus_dm = high.diff()
    minus_dm = low.diff().mul(-1)
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = atr(high, low, close, period=1).rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_val = dx.rolling(period).mean()
    return {"adx": adx_val, "plus_di": plus_di, "minus_di": minus_di}


def wyckoff_phase(df: "pd.DataFrame") -> Dict:
    """Classificação simplificada de fase Wyckoff baseada em estrutura de preço/volume."""
    if len(df) < 50:
        return {"phase": "INSUFFICIENT_DATA", "confidence": 0}
    close = df["Close"]
    volume = df["Volume"]
    # Tendência de 20 períodos
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    trend = "UP" if sma20.iloc[-1] > sma50.iloc[-1] else "DOWN"
    # Volume médio
    vol_avg = volume.rolling(20).mean().iloc[-1]
    vol_recent = volume.tail(5).mean()
    vol_trend = "INCREASING" if vol_recent > vol_avg * 1.2 else "DECREASING" if vol_recent < vol_avg * 0.8 else "NEUTRAL"
    # Range
    high_20 = df["High"].rolling(20).max().iloc[-1]
    low_20 = df["Low"].rolling(20).min().iloc[-1]
    range_pct = (high_20 - low_20) / close.iloc[-1]
    # Heurística simples
    if trend == "UP" and vol_trend == "INCREASING" and range_pct < 0.15:
        phase = "MARKUP (C)"
    elif trend == "UP" and vol_trend == "DECREASING" and range_pct > 0.15:
        phase = "DISTRIBUTION (E)"
    elif trend == "DOWN" and vol_trend == "INCREASING" and range_pct < 0.15:
        phase = "MARKDOWN (C)"
    elif trend == "DOWN" and vol_trend == "DECREASING" and range_pct > 0.15:
        phase = "ACCUMULATION (A)"
    else:
        phase = "REACCUMULATION/REDISTRIBUTION (B/D)"
    return {"phase": phase, "trend": trend, "volume_trend": vol_trend, "range_pct": round(range_pct * 100, 2), "confidence": 60}


def support_resistance(df: "pd.DataFrame", window: int = 20, min_touches: int = 2) -> Dict:
    """Detecção simples de suporte/resistência por pivôs."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    # Pivôs altos/baixos
    high_pivots = high[(high.shift(1) < high) & (high.shift(-1) < high)]
    low_pivots = low[(low.shift(1) > low) & (low.shift(-1) > low)]
    # Agrupar níveis próximos (within 1%)
    levels = []
    for pivots, typ in [(high_pivots, "resistance"), (low_pivots, "support")]:
        for idx, val in pivots.items():
            merged = False
            for lvl in levels:
                if abs(lvl["price"] - val) / val < 0.01:
                    lvl["touches"] += 1
                    lvl["last_touch"] = idx
                    merged = True
                    break
            if not merged:
                levels.append({"price": val, "type": typ, "touches": 1, "first_touch": idx, "last_touch": idx})
    # Filtrar por mínimo de toques
    levels = [l for l in levels if l["touches"] >= min_touches]
    # Ordenar por proximidade do preço atual
    current = close.iloc[-1]
    levels.sort(key=lambda x: abs(x["price"] - current))
    return {"current_price": current, "levels": levels[:10]}


def analyze_technical(ohlcv: List[Dict]) -> Dict:
    """Pipeline completo de análise técnica."""
    _ensure_pandas()
    df = _to_dataframe(ohlcv)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    # Indicadores
    rsi_val = rsi(close).iloc[-1]
    macd_vals = macd(close)
    macd_line = macd_vals["macd"].iloc[-1]
    macd_signal = macd_vals["signal"].iloc[-1]
    macd_hist = macd_vals["histogram"].iloc[-1]
    bb = bollinger_bands(close)
    bb_upper = bb["upper"].iloc[-1]
    bb_middle = bb["middle"].iloc[-1]
    bb_lower = bb["lower"].iloc[-1]
    bb_pct_b = bb["percent_b"].iloc[-1]
    vwap_val = vwap(high, low, close, volume).iloc[-1]
    obv_val = obv(close, volume).iloc[-1]
    obv_prev = obv(close, volume).iloc[-2] if len(df) > 1 else obv_val
    atr_val = atr(high, low, close).iloc[-1]
    adx_vals = adx(high, low, close)
    adx_val = adx_vals["adx"].iloc[-1]
    # Wyckoff
    wyckoff = wyckoff_phase(df)
    # S/R
    sr = support_resistance(df)
    # Sinais
    signals = []
    if rsi_val > 70: signals.append({"type": "RSI_OVERBOUGHT", "value": round(rsi_val, 1)})
    elif rsi_val < 30: signals.append({"type": "RSI_OVERSOLD", "value": round(rsi_val, 1)})
    if macd_hist > 0 and macd_vals["histogram"].iloc[-2] <= 0: signals.append({"type": "MACD_BULLISH_CROSS"})
    if macd_hist < 0 and macd_vals["histogram"].iloc[-2] >= 0: signals.append({"type": "MACD_BEARISH_CROSS"})
    if close.iloc[-1] > bb_upper: signals.append({"type": "BB_UPPER_BREACH"})
    if close.iloc[-1] < bb_lower: signals.append({"type": "BB_LOWER_BREACH"})
    if obv_val > obv_prev and close.iloc[-1] > close.iloc[-2]: signals.append({"type": "OBV_CONFIRMS_UPTREND"})
    if obv_val < obv_prev and close.iloc[-1] < close.iloc[-2]: signals.append({"type": "OBV_CONFIRMS_DOWNTREND"})
    if adx_val > 25: signals.append({"type": "STRONG_TREND", "adx": round(adx_val, 1)})
    return {
        "timestamp": datetime.now().isoformat(),
        "price": round(float(close.iloc[-1]), 4),
        "rsi": round(float(rsi_val), 1) if not pd.isna(rsi_val) else None,
        "macd": {"line": round(float(macd_line), 4), "signal": round(float(macd_signal), 4), "histogram": round(float(macd_hist), 4)},
        "bollinger": {"upper": round(float(bb_upper), 4), "middle": round(float(bb_middle), 4), "lower": round(float(bb_lower), 4), "pct_b": round(float(bb_pct_b), 3)},
        "vwap": round(float(vwap_val), 4),
        "obv": round(float(obv_val), 0),
        "atr": round(float(atr_val), 4),
        "adx": round(float(adx_val), 1) if not pd.isna(adx_val) else None,
        "wyckoff": wyckoff,
        "support_resistance": sr,
        "signals": signals,
    }


def selftest() -> bool:
    ok = True
    print("Testando technical...")
    _ensure_pandas()
    # Gerar dados sintéticos
    np.random.seed(42)
    n = 100
    base = 100
    returns = np.random.normal(0.0005, 0.015, n)
    prices = base * np.exp(np.cumsum(returns))
    ohlcv = []
    for i, c in enumerate(prices):
        h = c * (1 + abs(np.random.normal(0, 0.005)))
        l = c * (1 - abs(np.random.normal(0, 0.005)))
        o = prices[i-1] if i > 0 else c
        v = int(np.random.lognormal(10, 0.5))
        ohlcv.append({"open": o, "high": h, "low": l, "close": c, "volume": v})
    try:
        result = analyze_technical(ohlcv)
        assert "rsi" in result and result["rsi"] is not None
        assert "macd" in result
        assert "wyckoff" in result
        print(f"  Análise técnica: RSI={result['rsi']}, MACD hist={result['macd']['histogram']:.4f}, Wyckoff={result['wyckoff']['phase']} OK")
    except Exception as e:
        print(f"  Análise: FALHOU - {e}")
        ok = False
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Technical Analysis CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("analyze", help="Análise técnica completa de OHLCV (JSON file ou stdin)")
    p.add_argument("input", nargs="?", help="Arquivo JSON com lista OHLCV (omitir para stdin)")
    p.add_argument("-o", "--output", help="Arquivo de saída JSON")

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    if args.cmd == "analyze":
        if args.input:
            with open(args.input) as f:
                ohlcv = json.load(f)
        else:
            ohlcv = json.load(sys.stdin)
        result = analyze_technical(ohlcv)
        out = json.dumps(result, indent=2, default=str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(out)
        else:
            print(out)


if __name__ == "__main__":
    main()