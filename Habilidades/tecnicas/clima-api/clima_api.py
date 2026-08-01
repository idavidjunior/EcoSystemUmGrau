import sys
from pathlib import Path
try:
    import requests
except ImportError:
    import os
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

CIDADE_PADRAO = "São Paulo"
LAT_PADRAO, LON_PADRAO = -23.5505, -46.6333

CODIGOS = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "nevoeiro",
    48: "nevoeiro com geada",
    51: "garoa leve",
    53: "garoa",
    55: "garoa forte",
    56: "garoa congelante",
    57: "garoa congelante forte",
    61: "chuva leve",
    63: "chuva moderada",
    65: "chuva forte",
    66: "chuva congelante",
    67: "chuva congelante forte",
    71: "neve leve",
    73: "neve moderada",
    75: "neve forte",
    77: "granizo",
    80: "pancada de chuva",
    81: "pancada de chuva forte",
    82: "pancada de chuva violenta",
    85: "pancada de neve",
    86: "pancada de neve forte",
    95: "tempestade",
    96: "tempestade com granizo",
    99: "tempestade com granizo forte",
}

def _localizacao():
    try:
        from geolocalizacao import get_localizacao
        loc = get_localizacao()
        if "erro" not in loc and loc.get("latitude") and loc.get("longitude"):
            return {
                "cidade": loc.get("cidade", CIDADE_PADRAO),
                "lat": loc["latitude"],
                "lon": loc["longitude"],
            }
    except Exception:
        pass
    return {"cidade": CIDADE_PADRAO, "lat": LAT_PADRAO, "lon": LON_PADRAO}


def get_weather_data(city=None):
    """Dados estruturados do clima atual."""
    loc = _localizacao()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
        "&timezone=America/Sao_Paulo"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"erro": f"status {resp.status_code}"}
        cur = resp.json().get("current", {})
        if not cur:
            return {"erro": "sem dados atuais"}
        code = cur.get("weather_code")
        return {
            "cidade": loc["cidade"],
            "temp": cur.get("temperature_2m"),
            "sensacao": cur.get("apparent_temperature"),
            "umidade": cur.get("relative_humidity_2m"),
            "codigo": code,
            "descricao": CODIGOS.get(code, "condição variável"),
        }
    except requests.exceptions.Timeout:
        return {"erro": "tempo esgotado"}
    except requests.exceptions.ConnectionError:
        return {"erro": "sem conexão"}
    except Exception as e:
        return {"erro": str(e)}


def get_forecast_data(days=3, city=None):
    """Previsão diária estruturada (lista por dia, hoje em diante)."""
    loc = _localizacao()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        f"&timezone=America/Sao_Paulo&forecast_days={days}"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"erro": f"status {resp.status_code}"}
        dia = resp.json().get("daily", {})
        if not dia:
            return {"erro": "sem previsão"}
        tempos = dia.get("time", [])
        previsoes = []
        for i, data in enumerate(tempos):
            code = dia.get("weather_code", [None])[i] if i < len(dia.get("weather_code", [])) else None
            previsoes.append({
                "data": data,
                "tmax": dia.get("temperature_2m_max", [None])[i] if i < len(dia.get("temperature_2m_max", [])) else None,
                "tmin": dia.get("temperature_2m_min", [None])[i] if i < len(dia.get("temperature_2m_min", [])) else None,
                "precip": dia.get("precipitation_probability_max", [None])[i] if i < len(dia.get("precipitation_probability_max", [])) else None,
                "codigo": code,
                "descricao": CODIGOS.get(code, ""),
            })
        return {"cidade": loc["cidade"], "previsoes": previsoes}
    except Exception:
        return {"erro": "falha na previsão"}


def get_weather(city=None):
    d = get_weather_data(city)
    if "erro" in d:
        return f"Erro ao consultar clima: {d['erro']}"
    texto = f"{d['cidade']}: {d['descricao']}, {d['temp']:.0f}°C"
    if d.get("sensacao") is not None:
        texto += f" (sensação {d['sensacao']:.0f}°C)"
    if d.get("umidade") is not None:
        texto += f", umidade {d['umidade']:.0f}%"
    return texto


def get_forecast(city=None):
    dados = get_forecast_data(days=2, city=city)
    if "erro" in dados or len(dados["previsoes"]) < 2:
        return ""
    d = dados["previsoes"][1]
    partes = []
    if d.get("tmax") is not None and d.get("tmin") is not None:
        partes.append(f"mínima de {d['tmin']:.0f} e máxima de {d['tmax']:.0f} graus")
    if d.get("descricao"):
        partes.append(d["descricao"])
    if d.get("precip") and d["precip"] > 0:
        partes.append(f"chance de chuva de {d['precip']:.0f} por cento")
    if not partes:
        return ""
    return "Previsão para amanhã: " + ", ".join(partes) + "."


if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else None
    print(get_weather(city))
    f = get_forecast(city)
    if f:
        print(f)
