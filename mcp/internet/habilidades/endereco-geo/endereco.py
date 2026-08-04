import json, sys
try:
    import requests
except ImportError:
    import os
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests


def get_localizacao():
    resp = requests.get("http://ip-api.com/json/?fields=status,city,region,country,lat,lon,query,timezone", timeout=10)
    if resp.status_code == 200:
        d = resp.json()
        if d.get("status") == "success":
            return d
    return {"erro": "falha na consulta"}


def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,
        "accept-language": "pt-BR"
    }
    headers = {"User-Agent": "EcoSystemUmGrau-Jarvis/1.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return {"erro": f"HTTP {resp.status_code}"}


def formatar_endereco(dados):
    if "erro" in dados:
        return f"Não foi possível obter o endereço: {dados['erro']}"
    end = dados.get("address", {})
    rua = end.get("road") or end.get("pedestrian") or end.get("footway") or ""
    numero = end.get("house_number") or ""
    bairro = end.get("neighbourhood") or end.get("suburb") or end.get("residential") or ""
    cidade = end.get("city") or end.get("town") or end.get("village") or ""
    estado = end.get("state") or end.get("region") or ""
    cep = end.get("postcode") or ""

    partes = []
    if numero:
        partes.append(f"{rua}, {numero}" if rua else numero)
    elif rua:
        partes.append(rua)
    if bairro:
        partes.append(bairro)
    if cidade and estado:
        partes.append(f"{cidade}, {estado}")
    elif cidade:
        partes.append(cidade)
    if cep:
        partes.append(f"CEP {cep}")
    return ", ".join(partes) if partes else dados.get("display_name", "endereço não encontrado")


def get_endereco(lat=None, lon=None):
    if lat is None or lon is None:
        local = get_localizacao()
        if "erro" in local:
            return {"erro": local["erro"]}
        lat, lon = local["lat"], local["lon"]
    dados = reverse_geocode(lat, lon)
    return {
        "latitude": lat,
        "longitude": lon,
        "endereco": dados.get("address", {}),
        "texto": formatar_endereco(dados),
        "display_name": dados.get("display_name", "")
    }


if __name__ == "__main__":
    if "--lat" in sys.argv and "--lon" in sys.argv:
        i = sys.argv.index("--lat")
        la = float(sys.argv[i + 1])
        i = sys.argv.index("--lon")
        lo = float(sys.argv[i + 1])
    else:
        la = lo = None
    resultado = get_endereco(la, lo)
    if "--texto" in sys.argv:
        print(resultado.get("texto", resultado.get("erro", "erro")))
    else:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
