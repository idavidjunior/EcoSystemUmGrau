"""Conversão de números para extenso em pt-BR.

Função pura, determinística e sem rede.
Regras padronizadas (num2words pt_BR):
- 100 → "cem"; 101–199 → "cento e ..."; 200 → "duzentos"
- Milhar + "e" quando resto < 100 OU resto é centena cheia:
  1001 → "mil e um"; 1100 → "mil e cem"; 1101 → "mil cento e um"
"""
from __future__ import annotations

_UNIDADES = [
    "zero", "um", "dois", "três", "quatro", "cinco", "seis",
    "sete", "oito", "nove",
]
_DEZ_ATE_19 = [
    "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
    "dezessete", "dezoito", "dezenove",
]
_DEZENAS = [
    "", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta",
    "setenta", "oitenta", "noventa",
]
_CENTENAS = [
    "", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
    "seiscentos", "setecentos", "oitocentos", "novecentos",
]
_ESCALAS = [
    (10**9, ("bilhão", "bilhões")),
    (10**6, ("milhão", "milhões")),
    (10**3, ("mil", "mil")),
]


def _ate_99(n: int) -> str:
    if n < 10:
        return _UNIDADES[n]
    if n < 20:
        return _DEZ_ATE_19[n - 10]
    dez = n // 10
    uni = n % 10
    if uni == 0:
        return _DEZENAS[dez]
    return f"{_DEZENAS[dez]} e {_UNIDADES[uni]}"


def _ate_999(n: int) -> str:
    if n < 100:
        return _ate_99(n)
    cen = n // 100
    resto = n % 100
    if resto == 0:
        return _CENTENAS[cen] if cen > 1 else "cem"
    return f"{_CENTENAS[cen]} e {_ate_99(resto)}"


def numero_por_extenso(n: int) -> str:
    """Converte inteiro para extenso em pt-BR (|n| até 999.999.999)."""
    if n < 0:
        return f"menos {numero_por_extenso(-n)}"
    if n == 0:
        return "zero"
    for valor, singular_plural in _ESCALAS:
        if n >= valor:
            q, resto = divmod(n, valor)
            base = f"{_ate_999(q)} {singular_plural[1]}" if q > 1 else singular_plural[0]
            if q == 1 and valor >= 10**6:
                base = f"um {singular_plural[0]}"
            if resto == 0:
                return base
            if resto < 100 or resto % 100 == 0:
                return f"{base} e {numero_por_extenso(resto)}"
            return f"{base} {numero_por_extenso(resto)}"
    return _ate_999(n)


def numero_feminino(n: int) -> str:
    """Versão feminina para 1 → "uma", 2 → "duas" (e finais 1/2)."""
    if n == 1:
        return "uma"
    if n == 2:
        return "duas"
    if n >= 20:
        dezena = (n // 10) * 10
        uni = n % 10
        if uni in (1, 2):
            return f"{numero_por_extenso(dezena)} e {numero_feminino(uni)}"
    return numero_por_extenso(n)