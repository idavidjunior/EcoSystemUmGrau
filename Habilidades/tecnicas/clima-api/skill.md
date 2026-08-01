# Clima API — Open-Meteo (sem chave)

## Como usar
Clima atual e previsão diária via Open-Meteo (gratuito, sem API key).

```bash
python Habilidades/tecnicas/clima-api/clima_api.py "cidade"
# → "São Paulo: predominantemente limpo, 16°C (sensação 16°C), umidade 91%"
# → "Previsão para amanhã: mínima de 13 e máxima de 28 graus, nublado."
```

Usado pela bridge (`jarvis_bridge.py`) na saudação criativa — ver funções estruturadas:

- `get_weather_data()` → dict {cidade, temp, sensacao, umidade, descricao, codigo}
- `get_forecast_data(days)` → {cidade, previsoes: [{data, tmin, tmax, precip, descricao}]}

## Dependências
- `requests`
- `geolocalizacao.py` (localização por IP, mesmo diretório desta habilidade)

## Cidades comuns
São Paulo, Rio de Janeiro, Belo Horizonte, Brasília, Salvador, Fortaleza, Curitiba, Porto Alegre, Recife, Manaus
