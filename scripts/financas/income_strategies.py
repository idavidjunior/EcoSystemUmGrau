#!/usr/bin/env python3
"""
Income Strategies — Covered calls, staking, yield farming, dividendos, arbitragem.
Cálculos de renda passiva com risco explícito.
"""
import sys
import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import numpy as np
except ImportError:
    np = None

sys.path.insert(0, os.path.dirname(__file__))


def covered_call_return(spot: float, strike: float, premium: float,
                        days: int = 30) -> Dict:
    """Retorno de covered call: prêmio + upside limitado."""
    if spot <= 0 or days <= 0:
        raise ValueError("spot e days devem ser positivos")
    premium_yield = premium / spot
    annualized = premium_yield * (365 / days)
    # Cenários
    assigned = strike > spot
    max_profit = (strike - spot) + premium if assigned else None
    upside_capped = strike - spot
    return {
        "strategy": "covered_call",
        "spot": spot,
        "strike": strike,
        "premium": premium,
        "days": days,
        "premium_yield_pct": round(premium_yield * 100, 2),
        "annualized_yield_pct": round(annualized * 100, 2),
        "assigned": assigned,
        "max_profit": round(max_profit, 2) if max_profit else None,
        "upside_left_pct": round((upside_capped / spot) * 100, 2) if not assigned else 0,
        "risk": "downside total do ativo menos prêmio recebido",
    }


def cash_secured_put_return(strike: float, premium: float, days: int = 30) -> Dict:
    """Cash-secured put: recebe prêmio, obrigação de comprar no strike."""
    if strike <= 0 or days <= 0:
        raise ValueError("strike e days devem ser positivos")
    collateral = strike
    premium_yield = premium / collateral
    annualized = premium_yield * (365 / days)
    breakeven = strike - premium
    return {
        "strategy": "cash_secured_put",
        "strike": strike,
        "premium": premium,
        "collateral": collateral,
        "days": days,
        "premium_yield_pct": round(premium_yield * 100, 2),
        "annualized_yield_pct": round(annualized * 100, 2),
        "breakeven": round(breakeven, 2),
        "risk": "compra do ativo no strike se exercido; perda até strike-prêmio",
    }


def staking_apy(annual_reward_rate: float, lock_days: int = 0,
                token_inflation: float = 0.0) -> Dict:
    """Staking APY com ajuste por inflação e liquidez."""
    real_apy = annual_reward_rate - token_inflation
    liquidity_penalty = 0.02 if lock_days >= 28 else 0.0  # penalidade conservadora
    net_apy = real_apy - liquidity_penalty
    return {
        "strategy": "staking",
        "nominal_apy_pct": round(annual_reward_rate * 100, 2),
        "token_inflation_pct": round(token_inflation * 100, 2),
        "real_apy_pct": round(real_apy * 100, 2),
        "lock_days": lock_days,
        "liquidity_penalty_pct": round(liquidity_penalty * 100, 2),
        "net_apy_pct": round(net_apy * 100, 2),
        "risks": ["slashing", "desbloqueio forçado", "queda do token", "custódia"],
    }


def yield_farming_net(apr: float, gas_cost_usd_per_tx: float, txs_per_day: float,
                      capital_usd: float, impermanent_loss_risk: str = "medium") -> Dict:
    """Yield farming líquido após custos de gás e IL estimada."""
    gross_daily = capital_usd * apr / 365
    daily_gas = gas_cost_usd_per_tx * txs_per_day
    net_daily = gross_daily - daily_gas
    il_estimates = {"low": 0.005, "medium": 0.03, "high": 0.10}
    il_annual = capital_usd * il_estimates.get(impermanent_loss_risk, 0.03)
    net_annual = net_daily * 365 - il_annual
    net_apr = net_annual / capital_usd if capital_usd > 0 else 0
    return {
        "strategy": "yield_farming",
        "capital_usd": capital_usd,
        "apr_gross_pct": round(apr * 100, 2),
        "daily_gas_usd": round(daily_gas, 2),
        "net_daily_usd": round(net_daily, 2),
        "il_estimate_pct": round(il_estimates.get(impermanent_loss_risk, 0.03) * 100, 1),
        "net_apr_pct": round(net_apr * 100, 2),
        "viable": net_apr > 0.05,
        "risks": ["impermanent loss", "rug pull", "exploit do contrato", "mudança de APR"],
    }


def dividend_yield_analysis(price: float, annual_dividend: float,
                            payout_ratio: float = None, growth_rate: float = 0.0) -> Dict:
    """Análise de dividendo: yield, payout, sustentabilidade."""
    if price <= 0:
        raise ValueError("price deve ser positivo")
    yield_pct = annual_dividend / price
    sustainable = True
    warnings = []
    if payout_ratio is not None:
        if payout_ratio > 0.8:
            sustainable = False
            warnings.append("payout ratio alto (>80%) — dividendo em risco")
        elif payout_ratio > 0.6:
            warnings.append("payout ratio moderado (60-80%)")
    if yield_pct > 0.12:
        warnings.append("yield muito alto (>12%) — possível value trap ou corte iminente")
    return {
        "strategy": "dividendos",
        "price": price,
        "annual_dividend": annual_dividend,
        "yield_pct": round(yield_pct * 100, 2),
        "payout_ratio": payout_ratio,
        "growth_rate_pct": round(growth_rate * 100, 2),
        "sustainable": sustainable,
        "warnings": warnings,
    }


def arbitrage_spread(buy_price: float, sell_price: float, buy_fee: float = 0.001,
                     sell_fee: float = 0.001, transfer_fee: float = 0.0,
                     transfer_time_min: int = 10) -> Dict:
    """Arbitragem entre exchanges — spread líquido após taxas."""
    gross_spread = (sell_price - buy_price) / buy_price
    total_fees = buy_fee + sell_fee + transfer_fee
    net_spread = gross_spread - total_fees
    return {
        "strategy": "arbitragem",
        "buy_price": buy_price,
        "sell_price": sell_price,
        "gross_spread_pct": round(gross_spread * 100, 4),
        "total_fees_pct": round(total_fees * 100, 4),
        "net_spread_pct": round(net_spread * 100, 4),
        "transfer_time_min": transfer_time_min,
        "viable": net_spread > 0.002,
        "risks": ["movimento de preço durante transferência", "liquidez insuficiente", "retirada bloqueada"],
    }


def income_portfolio_projection(capital: float, allocations: Dict[str, float],
                                yields: Dict[str, float], months: int = 12) -> Dict:
    """Projeção de renda mensal de portfólio de renda."""
    monthly_income = {}
    total_monthly = 0
    for asset, alloc_pct in allocations.items():
        amount = capital * alloc_pct
        y = yields.get(asset, 0)
        monthly = amount * y / 12
        monthly_income[asset] = round(monthly, 2)
        total_monthly += monthly
    total_annual = total_monthly * months
    blended_yield = total_annual / capital if capital > 0 else 0
    return {
        "capital": capital,
        "allocations": allocations,
        "yields_apr": yields,
        "monthly_income_by_asset": monthly_income,
        "total_monthly_income": round(total_monthly, 2),
        "total_annual_income": round(total_annual, 2),
        "blended_yield_pct": round(blended_yield * 100, 2),
        "months_projected": months,
    }


def selftest() -> bool:
    ok = True
    print("Testando income_strategies...")
    try:
        cc = covered_call_return(spot=100, strike=105, premium=2.5, days=30)
        assert cc["premium_yield_pct"] == 2.5
        assert cc["annualized_yield_pct"] == round(2.5 * (365/30), 2)
        print(f"  Covered call: yield={cc['premium_yield_pct']}%, anualizado={cc['annualized_yield_pct']}% OK")
    except Exception as e:
        print(f"  Covered call: FALHOU - {e}")
        ok = False
    try:
        csp = cash_secured_put_return(strike=95, premium=1.8, days=30)
        assert csp["breakeven"] == 93.2
        print(f"  Cash-secured put: breakeven={csp['breakeven']} OK")
    except Exception as e:
        print(f"  CSP: FALHOU - {e}")
        ok = False
    try:
        st = staking_apy(0.08, lock_days=28, token_inflation=0.04)
        assert st["net_apy_pct"] == round((0.08 - 0.04 - 0.02) * 100, 2)
        print(f"  Staking: net APY={st['net_apy_pct']}% OK")
    except Exception as e:
        print(f"  Staking: FALHOU - {e}")
        ok = False
    try:
        yf = yield_farming_net(apr=0.25, gas_cost_usd_per_tx=5, txs_per_day=2, capital_usd=5000)
        assert yf["net_daily_usd"] == round(5000*0.25/365 - 10, 2)
        print(f"  Yield farming: net APR={yf['net_apr_pct']}%, viável={yf['viable']} OK")
    except Exception as e:
        print(f"  Yield farming: FALHOU - {e}")
        ok = False
    try:
        dy = dividend_yield_analysis(price=50, annual_dividend=3.0, payout_ratio=0.7)
        assert dy["yield_pct"] == 6.0
        assert len(dy["warnings"]) == 1
        print(f"  Dividendos: yield={dy['yield_pct']}% OK")
    except Exception as e:
        print(f"  Dividendos: FALHOU - {e}")
        ok = False
    try:
        arb = arbitrage_spread(buy_price=100, sell_price=101, buy_fee=0.001, sell_fee=0.001)
        assert arb["net_spread_pct"] == round(((101-100)/100 - 0.002)*100, 4)
        assert arb["viable"]
        print(f"  Arbitragem: net={arb['net_spread_pct']}% OK")
    except Exception as e:
        print(f"  Arbitragem: FALHOU - {e}")
        ok = False
    try:
        proj = income_portfolio_projection(
            capital=100000,
            allocations={"tesouro": 0.5, "fiis": 0.3, "staking": 0.2},
            yields={"tesouro": 0.10, "fiis": 0.08, "staking": 0.06},
        )
        assert proj["blended_yield_pct"] == round((0.5*0.10 + 0.3*0.08 + 0.2*0.06)*100, 2)
        print(f"  Projeção: mensal=R${proj['total_monthly_income']}, yield={proj['blended_yield_pct']}% OK")
    except Exception as e:
        print(f"  Projeção: FALHOU - {e}")
        ok = False
    print(f"Selftest: {'PASSOU' if ok else 'FALHOU'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Income Strategies CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("coveredcall", help="Covered call")
    p.add_argument("--spot", type=float, required=True)
    p.add_argument("--strike", type=float, required=True)
    p.add_argument("--premium", type=float, required=True)
    p.add_argument("--days", type=int, default=30)

    p = sub.add_parser("csp", help="Cash-secured put")
    p.add_argument("--strike", type=float, required=True)
    p.add_argument("--premium", type=float, required=True)
    p.add_argument("--days", type=int, default=30)

    p = sub.add_parser("staking", help="Staking APY")
    p.add_argument("--rate", type=float, required=True, help="APR nominal (ex: 0.08)")
    p.add_argument("--lock-days", type=int, default=0)
    p.add_argument("--inflation", type=float, default=0.0)

    p = sub.add_parser("farming", help="Yield farming líquido")
    p.add_argument("--apr", type=float, required=True)
    p.add_argument("--gas", type=float, default=5.0)
    p.add_argument("--txs-day", type=float, default=2)
    p.add_argument("--capital", type=float, required=True)
    p.add_argument("--il", choices=["low", "medium", "high"], default="medium")

    p = sub.add_parser("dividend", help="Análise de dividendo")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--dividend", type=float, required=True)
    p.add_argument("--payout", type=float)
    p.add_argument("--growth", type=float, default=0.0)

    p = sub.add_parser("arbitrage", help="Spread de arbitragem")
    p.add_argument("--buy", type=float, required=True)
    p.add_argument("--sell", type=float, required=True)
    p.add_argument("--buy-fee", type=float, default=0.001)
    p.add_argument("--sell-fee", type=float, default=0.001)

    p = sub.add_parser("projection", help="Projeção de portfólio de renda")
    p.add_argument("--capital", type=float, required=True)
    p.add_argument("--allocations", required=True, help='JSON {"asset": pct}')
    p.add_argument("--yields", required=True, help='JSON {"asset": apr}')
    p.add_argument("--months", type=int, default=12)

    p = sub.add_parser("selftest", help="Auto-teste")

    args = parser.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)

    try:
        if args.cmd == "coveredcall":
            r = covered_call_return(args.spot, args.strike, args.premium, args.days)
        elif args.cmd == "csp":
            r = cash_secured_put_return(args.strike, args.premium, args.days)
        elif args.cmd == "staking":
            r = staking_apy(args.rate, args.lock_days, args.inflation)
        elif args.cmd == "farming":
            r = yield_farming_net(args.apr, args.gas, args.txs_day, args.capital, args.il)
        elif args.cmd == "dividend":
            r = dividend_yield_analysis(args.price, args.dividend, args.payout, args.growth)
        elif args.cmd == "arbitrage":
            r = arbitrage_spread(args.buy, args.sell, args.buy_fee, args.sell_fee)
        elif args.cmd == "projection":
            r = income_portfolio_projection(
                args.capital, json.loads(args.allocations), json.loads(args.yields), args.months
            )
        print(json.dumps(r, indent=2))
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()