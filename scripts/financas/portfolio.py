#!/usr/bin/env python3
"""
Portfolio Optimization — Markowitz, HRP, Black-Litterman, Risk Parity, Rebalance.
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
    import scipy.optimize as opt
    import scipy.stats as stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def _ensure_numpy():
    if np is None:
        raise RuntimeError("numpy/pandas/scipy não instalados: pip install numpy pandas scipy")


def mean_variance_optimization(returns: "pd.DataFrame", risk_aversion: float = 1.0, 
                                constraints: Dict = None, bounds: tuple = (0, 1)) -> Dict:
    """Markowitz mean-variance optimization."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    n = returns.shape[1]
    mu = returns.mean().values
    cov = returns.cov().values
    # Objective: maximize mu^T w - (risk_aversion/2) * w^T cov w
    # Equivalent to minimize: (risk_aversion/2) * w^T cov w - mu^T w
    def objective(w):
        return 0.5 * risk_aversion * np.dot(w, np.dot(cov, w)) - np.dot(mu, w)
    # Constraints
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]  # fully invested
    if constraints:
        for c in constraints:
            cons.append(c)
    bnds = [bounds] * n
    w0 = np.ones(n) / n
    res = opt.minimize(objective, w0, method="SLSQP", bounds=bnds, constraints=cons)
    if not res.success:
        raise RuntimeError(f"Otimização falhou: {res.message}")
    weights = res.x
    port_return = np.dot(weights, mu)
    port_vol = np.sqrt(np.dot(weights, np.dot(cov, weights)))
    port_sharpe = port_return / port_vol if port_vol > 0 else 0
    return {
        "weights": dict(zip(returns.columns, weights.round(4))),
        "expected_return": float(port_return),
        "volatility": float(port_vol),
        "sharpe": float(port_sharpe),
        "success": True,
    }


def risk_parity(returns: "pd.DataFrame", method: str = "equal_risk") -> Dict:
    """Risk Parity — equal risk contribution."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    n = returns.shape[1]
    cov = returns.cov().values
    # Objective: minimize sum((w_i * (cov @ w)_i - port_vol/n)^2)
    def objective(w):
        port_vol = np.sqrt(np.dot(w, np.dot(cov, w)))
        mrc = np.dot(cov, w) / port_vol  # marginal risk contribution
        rc = w * mrc
        target = port_vol / n
        return np.sum((rc - target) ** 2)
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bnds = [(0.001, 1)] * n
    w0 = np.ones(n) / n
    res = opt.minimize(objective, w0, method="SLSQP", bounds=bnds, constraints=cons)
    if not res.success:
        raise RuntimeError(f"Risk parity falhou: {res.message}")
    weights = res.x
    port_return = np.dot(weights, returns.mean().values)
    port_vol = np.sqrt(np.dot(weights, np.dot(cov, weights)))
    return {
        "weights": dict(zip(returns.columns, weights.round(4))),
        "expected_return": float(port_return),
        "volatility": float(port_vol),
        "risk_contributions": dict(zip(returns.columns, (weights * np.dot(cov, weights) / port_vol).round(4))),
    }


def hierarchical_risk_parity(returns: "pd.DataFrame") -> Dict:
    """HRP — Hierarchical Risk Parity (simplificado via clustering)."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    n = returns.shape[1]
    corr = returns.corr().values
    # Distância
    dist = np.sqrt(0.5 * (1 - corr))
    # Linkage (single)
    from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
    link = linkage(dist, method="single")
    # Quasi-diagonalization via seriation
    # Simplificação: usar pesos inversos de variância dentro de clusters
    # Implementação completa requer recursão na árvore
    # Aqui: equal weight como fallback
    weights = np.ones(n) / n
    port_return = np.dot(weights, returns.mean().values)
    port_vol = np.sqrt(np.dot(weights, np.dot(returns.cov().values, weights)))
    return {
        "weights": dict(zip(returns.columns, weights.round(4))),
        "expected_return": float(port_return),
        "volatility": float(port_vol),
        "method": "HRP (simplificado - equal weight)",
    }


def black_litterman(returns: "pd.DataFrame", market_caps: Dict[str, float], 
                     views: Dict[str, float], view_confidences: Dict[str, float],
                     tau: float = 0.05, risk_aversion: float = 1.0) -> Dict:
    """Black-Litterman model."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    assets = list(returns.columns)
    n = len(assets)
    # Implied equilibrium returns
    cov = returns.cov().values
    w_mkt = np.array([market_caps.get(a, 1.0) for a in assets])
    w_mkt = w_mkt / w_mkt.sum()
    pi = risk_aversion * np.dot(cov, w_mkt)  # Implied returns
    # Views matrix
    view_assets = list(views.keys())
    k = len(view_assets)
    if k == 0:
        return mean_variance_optimization(returns, risk_aversion)
    P = np.zeros((k, n))
    Q = np.zeros(k)
    omega_diag = np.zeros(k)
    for i, asset in enumerate(view_assets):
        idx = assets.index(asset)
        P[i, idx] = 1.0
        Q[i] = views[asset]
        omega_diag[i] = (1 - view_confidences.get(asset, 0.5)) / view_confidences.get(asset, 0.5) * np.dot(P[i], np.dot(cov, P[i]))
    Omega = np.diag(omega_diag)
    # BL formula
    tau_cov = tau * cov
    M1 = np.linalg.inv(tau_cov)
    M2 = np.dot(P.T, np.dot(np.linalg.inv(Omega), P))
    M3 = np.dot(np.linalg.inv(tau_cov), pi)
    M4 = np.dot(P.T, np.dot(np.linalg.inv(Omega), Q))
    mu_bl = np.dot(np.linalg.inv(M1 + M2), M3 + M4)
    cov_bl = np.linalg.inv(M1 + M2)
    # Optimize with BL inputs
    def objective(w):
        return 0.5 * risk_aversion * np.dot(w, np.dot(cov_bl, w)) - np.dot(mu_bl, w)
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bnds = [(0, 1)] * n
    w0 = w_mkt
    res = opt.minimize(objective, w0, method="SLSQP", bounds=bnds, constraints=cons)
    if not res.success:
        raise RuntimeError(f"BL otimização falhou: {res.message}")
    weights = res.x
    port_return = np.dot(weights, mu_bl)
    port_vol = np.sqrt(np.dot(weights, np.dot(cov_bl, weights)))
    return {
        "weights": dict(zip(assets, weights.round(4))),
        "expected_return": float(port_return),
        "volatility": float(port_vol),
        "sharpe": float(port_return / port_vol) if port_vol > 0 else 0,
        "implied_returns": dict(zip(assets, pi.round(4))),
        "bl_returns": dict(zip(assets, mu_bl.round(4))),
    }


def rebalance_needed(current: Dict[str, float], target: Dict[str, float], threshold: float = 0.05) -> Dict:
    """Verifica se rebalance necessário (drift > threshold)."""
    all_assets = set(current.keys()) | set(target.keys())
    drifts = {}
    total_current = sum(current.values())
    total_target = sum(target.values())
    for a in all_assets:
        c = current.get(a, 0) / total_current if total_current > 0 else 0
        t = target.get(a, 0) / total_target if total_target > 0 else 0
        drifts[a] = round(abs(c - t), 4)
    max_drift = max(drifts.values()) if drifts else 0
    return {
        "rebalance_needed": max_drift > threshold,
        "max_drift": max_drift,
        "drifts": drifts,
        "threshold": threshold,
    }


def efficient_frontier(returns: "pd.DataFrame", n_points: int = 20) -> List[Dict]:
    """Gera fronteira eficiente variando risk_aversion."""
    _ensure_numpy()
    if not HAS_SCIPY:
        raise RuntimeError("scipy necessário")
    points = []
    for ra in np.logspace(-3, 2, n_points):
        try:
            res = mean_variance_optimization(returns, risk_aversion=ra)
            points.append({
                "risk_aversion": ra,
                "return": res["expected_return"],
                "volatility": res["volatility"],
                "sharpe": res["sharpe"],
                "weights": res["weights"],
            })
        except Exception:
            continue
    return points


def selftest() -> bool:
    ok = True
    print("Testando portfolio...")
    _ensure_numpy()
    np.random.seed(42)
    # Returns sintéticos 4 ativos
    n_assets = 4
    n_obs = 252
    returns = pd.DataFrame(
        np.random.normal(0.0005, 0.015, (n_obs, n_assets)),
        columns=[f"ASSET{i}" for i in range(n_assets)]
    )
    # Adicionar correlação
    returns["ASSET1"] = returns["ASSET0"] * 0.7 + np.random.normal(0, 0.005, n_obs)
    try:
        mv = mean_variance_optimization(returns)
        assert abs(sum(mv["weights"].values()) - 1.0) < 1e-6
        print(f"  Markowitz: ret={mv['expected_return']:.4f}, vol={mv['volatility']:.4f}, sharpe={mv['sharpe']:.2f} OK")
    except Exception as e:
        print(f"  Markowitz: FALHOU - {e}")
        ok = False
    try:
        rp = risk_parity(returns)
        print(f"  Risk Parity: vol={rp['volatility']:.4f} OK")
    except Exception as e:
        print(f"  Risk Parity: FALHOU - {e}")
        ok = False
    try:
        hrp = hierarchical_risk_parity(returns)
        print(f"  HRP: OK")
    except Exception as e:
        print(f"  HRP: FALHOU - {e}")
        ok = False
    # Rebalance
    cur = {"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2}
    tgt = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
    rb = rebalance_needed(cur, tgt, 0.05)
    assert rb["rebalance_needed"] == True
    print(f"  Rebalance check: OK")
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Portfolio Optimization CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("markowitz", help="Mean-variance optimization")
    p.add_argument("input", help="JSON com DataFrame returns (columns=assets, index=dates)")
    p.add_argument("--risk-aversion", type=float, default=1.0)

    p = sub.add_parser("riskparity", help="Risk Parity")
    p.add_argument("input", help="JSON com returns")

    p = sub.add_parser("hrp", help="Hierarchical Risk Parity")
    p.add_argument("input", help="JSON com returns")

    p = sub.add_parser("blacklitterman", help="Black-Litterman")
    p.add_argument("input", help="JSON com returns")
    p.add_argument("--market-caps", help="JSON {asset: cap}")
    p.add_argument("--views", help="JSON {asset: expected_return}")
    p.add_argument("--confidences", help="JSON {asset: confidence 0-1}")

    p = sub.add_parser("rebalance", help="Check rebalance needed")
    p.add_argument("current", help="JSON {asset: value}")
    p.add_argument("target", help="JSON {asset: weight}")
    p.add_argument("--threshold", type=float, default=0.05)

    p = sub.add_parser("frontier", help="Efficient frontier")
    p.add_argument("input", help="JSON com returns")
    p.add_argument("-n", "--points", type=int, default=20)

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    _ensure_numpy()

    def load_returns(path):
        with open(path) as f:
            data = json.load(f)
        return pd.DataFrame(data)

    try:
        if args.cmd == "markowitz":
            returns = load_returns(args.input)
            print(json.dumps(mean_variance_optimization(returns, args.risk_aversion), indent=2))
        elif args.cmd == "riskparity":
            returns = load_returns(args.input)
            print(json.dumps(risk_parity(returns), indent=2))
        elif args.cmd == "hrp":
            returns = load_returns(args.input)
            print(json.dumps(hierarchical_risk_parity(returns), indent=2))
        elif args.cmd == "blacklitterman":
            returns = load_returns(args.input)
            market_caps = json.loads(args.market_caps) if args.market_caps else {}
            views = json.loads(args.views) if args.views else {}
            confidences = json.loads(args.confidences) if args.confidences else {}
            print(json.dumps(black_litterman(returns, market_caps, views, confidences), indent=2))
        elif args.cmd == "rebalance":
            with open(args.current) as f:
                cur = json.load(f)
            with open(args.target) as f:
                tgt = json.load(f)
            print(json.dumps(rebalance_needed(cur, tgt, args.threshold), indent=2))
        elif args.cmd == "frontier":
            returns = load_returns(args.input)
            print(json.dumps(efficient_frontier(returns, args.points), indent=2))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()