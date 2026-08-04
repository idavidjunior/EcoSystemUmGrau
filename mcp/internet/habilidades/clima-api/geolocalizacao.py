import json, sys, os
from pathlib import Path
try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests


def get_localizacao():
    try:
        resp = requests.get("http://ip-api.com/json/?fields=status,city,region,country,lat,lon,query,timezone", timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("status") == "success":
                return {
                    "cidade": d["city"],
                    "regiao": d["region"],
                    "pais": d["country"],
                    "latitude": d["lat"],
                    "longitude": d["lon"],
                    "ip": d["query"],
                    "timezone": d["timezone"]
                }
        return {"erro": "falha na consulta"}
    except Exception as e:
        return {"erro": str(e)}


def get_clima_local():
    from clima_api import get_weather
    local = get_localizacao()
    if "erro" in local:
        return f"Não foi possível obter localização: {local['erro']}"
    clima = get_weather(local["cidade"])
    return f"{local['cidade']}, {local['regiao']}. {clima}"


def formatar_saudacao():
    local = get_localizacao()
    if "erro" in local:
        return "sistemas online"
    try:
        from clima_api import get_weather
        clima = get_weather(local["cidade"])
    except Exception:
        clima = ""
    return f"em {local['cidade']}, {local['regiao']}"


if __name__ == "__main__":
    if "--clima" in sys.argv:
        print(get_clima_local())
    elif "--saudacao" in sys.argv:
        print(formatar_saudacao())
    else:
        print(json.dumps(get_localizacao(), indent=2, ensure_ascii=False))
