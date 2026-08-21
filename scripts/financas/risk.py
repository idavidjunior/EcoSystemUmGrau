#!/usr/bin/env python3
"""
Risk Management — VaR, CVaR, stress test, correlação, Kelly criterion, position sizing.
Monte Carlo, historical simulation, parametric.
"""
import sys
import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = None
    pd = None

try:
    import scipy.stats as stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def _ensure_numpy():
    if np is None:
        raise RuntimeError("numpy/pandas não instalados: pip install numpy pandas")


def var_historical(returns: "np.ndarray", confidence: float = 0.99, horizon: int = 1) -> float:
    """VaR histórico (percentil)."""
    _ensure_numpy()
    if len(returns) < 30:
        raise ValueError("Precisa de pelo menos 30 observações")
    var = -np.percentile(returns, (1 - confidence) * 100) * np.sqrt(horizon)
    return float(var)


def cvar_historical(returns: "np.ndarray", confidence: float = 0.99, horizon: int = 1) -> float:
    """Conditional VaR (Expected Shortfall) histórico."""
    _ensure_numpy()
    var = var_historical(returns, confidence, horizon)
    tail = returns[returns <= -var / np.sqrt(horizon)]
    if len(tail) == 0:
        return var
    cvar = -tail.mean() * np.sqrt(horizon)
    return float(cvar)


def var_parametric(returns: "np.ndarray", confidence: float = 0.99, horizon: int = 1) -> float:
    """VaR paramétrico (assume normal)."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário para VaR paramétrico")
    mu = returns.mean()
    sigma = returns.std(ddof=1)
    z = stats.norm.ppf(1 - confidence)
    var = -(mu + z * sigma) * np.sqrt(horizon)
    return float(var)


def cvar_parametric(returns: "np.ndarray", confidence: float = 0.99, horizon: int = 1) -> float:
    """CVaR paramétrico."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    mu = returns.mean()
    sigma = returns.std(ddof=1)
    z = stats.norm.ppf(1 - confidence)
    cvar = -(mu - sigma * stats.norm.pdf(z) / (1 - confidence)) * np.sqrt(horizon)
    return float(cvar)


def var_monte_carlo(returns: "np.ndarray", confidence: float = 0.99, horizon: int = 1, n_sim: int = 10000) -> float:
    """VaR Monte Carlo (bootstrap)."""
    _ensure_numpy()
    sim = np.random.choice(returns, size=(n_sim, horizon), replace=True).sum(axis=1)
    var = -np.percentile(sim, (1 - confidence) * 100)
    return float(var)


def max_drawdown(prices: "np.ndarray") -> Dict:
    """Max drawdown, duração, recovery."""
    _ensure_numpy()
    peak = np.maximum.accumulate(prices)
    dd = (prices - peak) / peak
    max_dd = dd.min()
    peak_idx = np.argmax(prices[:np.argmin(dd) + 1]) if len(dd) > 0 else 0
    trough_idx = np.argmin(dd)
    # Recovery
    recovery_idx = None
    for i in range(trough_idx + 1, len(prices)):
        if prices[i] >= prices[peak_idx]:
            recovery_idx = i
            break
    duration = trough_idx - peak_idx
    recovery_duration = recovery_idx - trough_idx if recovery_idx else None
    return {
        "max_drawdown": float(max_dd),
        "peak_idx": int(peak_idx),
        "trough_idx": int(trough_idx),
        "duration_days": int(duration),
        "recovery_days": int(recovery_duration) if recovery_duration else None,
        "recovered": recovery_idx is not None,
    }


def correlation_matrix(returns_dict: Dict[str, "np.ndarray"]) -> Dict:
    """Matriz de correlação entre ativos."""
    _ensure_numpy()
    df = pd.DataFrame({k: v for k, v in returns_dict.items() if len(v) > 10})
    if df.empty or df.shape[1] < 2:
        return {}
    corr = df.corr()
    return {
        "matrix": corr.round(3).to_dict(),
        "max_corr": float(corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().max()),
        "min_corr": float(corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().min()),
        "avg_corr": float(corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().mean()),
    }


def kelly_criterion(win_rate: float, win_loss_ratio: float) -> float:
    """Kelly fraction: f* = p - q/b = p - (1-p)/b."""
    if win_loss_ratio <= 0:
        return 0.0
    f = win_rate - (1 - win_rate) / win_loss_ratio
    return max(0.0, min(f, 1.0))


def half_kelly(win_rate: float, win_loss_ratio: float) -> float:
    """Half-Kelly (mais conservador)."""
    return kelly_criterion(win_rate, win_loss_ratio) * 0.5


def position_size_kelly(capital: float, win_rate: float, win_loss_ratio: float, max_fraction: float = 0.25) -> Dict:
    """Sizing baseado em Kelly limitado."""
    f = kelly_criterion(win_rate, win_loss_ratio)
    f_half = half_kelly(win_rate, win_loss_ratio)
    f_final = min(f_half, max_fraction)
    return {
        "kelly_fraction": round(f, 4),
        "half_kelly": round(f_half, 4),
        "used_fraction": round(f_final, 4),
        "position_size": round(capital * f_final, 2),
        "capital": capital,
    }


def risk_reward(entry: float, stop: float, target: float) -> Dict:
    """Risk/Reward ratio."""
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk == 0:
        return {"rr": None, "risk": 0, "reward": reward}
    return {"rr": round(reward / risk, 2), "risk": round(risk, 4), "reward": round(reward, 4)}


def stress_test(returns: "np.ndarray", scenarios: Dict[str, float] = None) -> Dict:
    """Stress test: aplicar choques históricos/hipotéticos."""
    _ensure_numpy()
    if scenarios is None:
        scenarios = {
            "covid_crash": -0.35,      # Mar 2020
            "gfc_2008": -0.50,         # 2008
            "crypto_winter": -0.80,    # 2018/2022
            "flash_crash": -0.10,      # Intraday
            "rate_hike": -0.15,        # Fed hike cycle
        }
    results = {}
    for name, shock in scenarios.items():
        portfolio_shock = returns.mean() + shock
        results[name] = {
            "shock": shock,
            "projected_return": float(portfolio_shock),
            "var_99": var_historical(returns, 0.99),
            "cvar_99": cvar_historical(returns, 0.99),
        }
    return results


def portfolio_var(weights: "np.ndarray", returns_matrix: "np.ndarray", confidence: float = 0.99) -> float:
    """VaR de carteira (paramétrico)."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    port_mean = np.dot(weights, returns_matrix.mean(axis=0))
    port_var = np.dot(weights, np.dot(np.cov(returns_matrix.T), weights))
    port_std = np.sqrt(port_var)
    z = stats.norm.ppf(1 - confidence)
    var = -(port_mean + z * port_std)
    return float(var)


def component_var(weights: "np.ndarray", returns_matrix: "np.ndarray", confidence: float = 0.99) -> "np.ndarray":
    """Component VaR por ativo."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    cov = np.cov(returns_matrix.T)
    port_std = np.sqrt(np.dot(weights, np.dot(cov, weights)))
    z = stats.norm.ppf(1 - confidence)
    mcr = np.dot(cov, weights) / port_std  # Marginal Contribution to Risk
    ccr = weights * mcr * z  # Component Contribution to Risk
    return ccr


def selftest() -> bool:
    ok = True
    print("Testando risk...")
    _ensure_numpy()
    np.random.seed(42)
    # Returns sintéticos
    returns = np.random.normal(0.0005, 0.02, 500)
    try:
        v = var_historical(returns, 0.99)
        c = cvar_historical(returns, 0.99)
        assert v > 0 and c >= v
        print(f"  VaR 99%: {v:.4f}, CVaR: {c:.4f} OK")
    except Exception as e:
        print(f"  VaR/CVaR: FALHOU - {e}")
        ok = False
    # Max DD
    prices = 100 * np.exp(np.cumsum(returns))
    dd = max_drawdown(prices)
    assert dd["max_drawdown"] < 0
    print(f"  Max DD: {dd['max_drawdown']:.2%} OK")
    # Kelly
    k = kelly_criterion(0.55, 1.5)
    assert 0 < k < 1
    print(f"  Kelly (55% win, 1.5 R:R): {k:.2%} OK")
    # Position size
    ps = position_size_kelly(100000, 0.55, 1.5)
    assert ps["used_fraction"] <= 0.25
    print(f"  Position size: ${ps['position_size']:,.0f} ({ps['used_fraction']:.1%}) OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Risk Management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("var", help="VaR/CVaR de returns (JSON file ou stdin)")
    p.add_argument("input", nargs="?", help="Arquivo JSON com array de returns")
    p.add_argument("-c", "--confidence", type=float, default=0.99)
    p.add_argument("-H", "--horizon", type=int, default=1)
    p.add_argument("-m", "--method", choices=["historical", "parametric", "mc"], default="historical")

    p = sub.add_parser("maxdd", help="Max drawdown de prices")
    p.add_argument("input", nargs="?", help="Arquivo JSON com array de prices")

    p = sub.add_parser("kelly", help="Kelly criterion")
    p.add_argument("win_rate", type=float)
    p.add_argument("win_loss_ratio", type=float)

    p = sub.add_parser("size", help="Position size via Kelly")
    p.add_argument("capital", type=float)
    p.add_argument("win_rate", type=float)
    p.add_argument("win_loss_ratio", type=float)
    p.add_argument("--max-frac", type=float, default=0.25)

    p = sub.add_parser("rr", help="Risk/Reward")
    p.add_argument("entry", type=float)
    p.add_argument("stop", type=float)
    p.add_argument("target", type=float)

    p = sub.add_parser("stress", help="Stress test")
    p.add_argument("input", nargs="?", help="Arquivo JSON com returns")

    p = sub.add_parser("corr", help="Correlation matrix")
    p.add_argument("input", help="Arquivo JSON com dict {symbol: returns_array}")

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    _ensure_numpy()

    def load_returns(path):
        if path:
            with open(path) as f:
                return np.array(json.load(f))
        return np.array(json.load(sys.stdin))

    def load_prices(path):
        if path:
            with open(path) as f:
                return np.array(json.load(f))
        return np.array(json.load(sys.stdin))

    try:
        if args.cmd == "var":
            returns = load_returns(args.input)
            if args.method == "historical":
                v = var_historical(returns, args.confidence, args.horizon)
                c = cvar_historical(returns, args.confidence, args.horizon)
            elif args.method == "parametric":
                v = var_parametric(returns, args.confidence, args.horizon)
                c = cvar_parametric(returns, args.confidence, args.horizon)
            else:
                v = var_monte_carlo(returns, args.confidence, args.horizon)
                c = None
            print(json.dumps({"var": v, "cvar": c, "confidence": args.confidence, "horizon": args.horizon}, indent=2))

        elif args.cmd == "maxdd":
            prices = load_prices(args.input)
            print(json.dumps(max_drawdown(prices), indent=2))

        elif args.cmd == "kelly":
            k = kelly_criterion(args.win_rate, args.win_loss_ratio)
            hk = half_kelly(args.win_rate, args.win_loss_ratio)
            print(json.dumps({"kelly": k, "half_kelly": hk}, indent=2))

        elif args.cmd == "size":
            print(json.dumps(position_size_kelly(args.capital, args.win_rate, args.win_loss_ratio, args.max_frac), indent=2))

        elif args.cmd == "rr":
            print(json.dumps(risk_reward(args.entry, args.stop, args.target), indent=2))

        elif args.cmd == "stress":
            returns = load_returns(args.input)
            print(json.dumps(stress_test(returns), indent=2))

        elif args.cmd == "corr":
            with open(args.input) as f:
                data = json.load(f)
            returns_dict = {k: np.array(v) for k, v in data.items()}
            print(json.dumps(correlation_matrix(returns_dict), indent=2))

    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()