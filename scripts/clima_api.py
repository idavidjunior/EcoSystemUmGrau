import os, json, sys
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass
import requests

def get_weather(city="São Paulo"):
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "Chave da API não configurada. Defina OPENWEATHER_API_KEY no .env"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pt_br"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            desc = d["weather"][0]["description"]
            temp = d["main"]["temp"]
            feel = d["main"]["feels_like"]
            hum = d["main"]["humidity"]
            city_name = d["name"]
            return f"{city_name}: {desc}, {temp:.0f}°C (sensação {feel:.0f}°C), umidade {hum}%"
        elif resp.status_code == 401:
            return "Chave da API inválida. Verifique OPENWEATHER_API_KEY."
        elif resp.status_code == 404:
            return f"Cidade '{city}' não encontrada."
        else:
            return f"Erro na API: {resp.status_code}"
    except requests.exceptions.Timeout:
        return "API do clima não respondeu a tempo."
    except requests.exceptions.ConnectionError:
        return "Sem conexão com a API do clima."
    except Exception as e:
        return f"Erro ao consultar clima: {e}"

def get_forecast(city="São Paulo"):
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "Chave da API não configurada."
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br&cnt=8"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            lista = resp.json().get("list", [])
            if not lista:
                return ""
            amanha = lista[:4]
            temps = [it["main"]["temp"] for it in amanha if it.get("main")]
            descs = [it["weather"][0]["description"] for it in amanha if it.get("weather")]
            chuva = any(any(d.get("icon", "").endswith("d") and "rain" in (d.get("description", "") or "") for d in it.get("weather", [])) for it in amanha)
            desc = descs[0] if descs else ""
            if temps:
                tmin, tmax = min(temps), max(temps)
                previsao = f"Previsão para hoje: {desc}, entre {tmin:.0f} e {tmax:.0f} graus"
                if chuva:
                    previsao += ", com chance de chuva"
                return previsao + "."
            return f"Previsão para hoje: {desc}." if desc else ""
        return ""
    except Exception:
        return ""

if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else "São Paulo"
    print(get_weather(city))
    f = get_forecast(city)
    if f:
        print(f)
