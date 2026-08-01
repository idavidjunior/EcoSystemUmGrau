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


def get_weather(city=None):
    loc = _localizacao()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
        "&timezone=America/Sao_Paulo"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            cur = d.get("current", {})
            if not cur:
                return f"{loc['cidade']}: previsão indisponível."
            temp = cur.get("temperature_2m")
            feel = cur.get("apparent_temperature")
            hum = cur.get("relative_humidity_2m")
            code = cur.get("weather_code")
            desc = CODIGOS.get(code, "condição variável")
            texto = f"{loc['cidade']}: {desc}, {temp:.0f}°C"
            if feel is not None:
                texto += f" (sensação {feel:.0f}°C)"
            if hum is not None:
                texto += f", umidade {hum:.0f}%"
            return texto
        return f"Erro na API de clima: {resp.status_code}"
    except requests.exceptions.Timeout:
        return "API do clima não respondeu a tempo."
    except requests.exceptions.ConnectionError:
        return "Sem conexão com a API do clima."
    except Exception as e:
        return f"Erro ao consultar clima: {e}"


def get_forecast(city=None):
    loc = _localizacao()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={loc['lat']}&longitude={loc['lon']}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        "&timezone=America/Sao_Paulo&forecast_days=1"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            dia = d.get("daily", {})
            if not dia:
                return ""
            tmax = dia.get("temperature_2m_max", [None])[0]
            tmin = dia.get("temperature_2m_min", [None])[0]
            pchuv = dia.get("precipitation_probability_max", [None])[0]
            code = dia.get("weather_code", [None])[0]
            desc = CODIGOS.get(code, "")
            partes = []
            if tmax is not None and tmin is not None:
                partes.append(f"máxima de {tmax:.0f} e mínima de {tmin:.0f} graus")
            if desc:
                partes.append(desc)
            if pchuv is not None and pchuv > 0:
                partes.append(f"chance de chuva de {pchuv:.0f} por cento")
            if not partes:
                return ""
            return "Previsão para hoje: " + ", ".join(partes) + "."
        return ""
    except Exception:
        return ""


if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else None
    print(get_weather(city))
    f = get_forecast(city)
    if f:
        print(f)
