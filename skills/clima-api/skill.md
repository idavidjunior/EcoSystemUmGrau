# Clima API — Integração com OpenWeatherMap

## Como usar
Para obter o clima de uma cidade, use `python EcoSystemUmGrau/scripts/clima_api.py "<cidade>"`.

## Exemplo
```python
python clima_api.py "São Paulo"
# → "céu limpo, 22°C"
```

## Requisitos
- A chave da API OpenWeatherMap está em `scripts/.env` como `OPENWEATHER_API_KEY`
- O script usa `requests` (já instalado)
- Idioma: `lang=pt_br`, unidade: `°C`

## Cidades comuns
São Paulo, Rio de Janeiro, Belo Horizonte, Brasília, Salvador, Fortaleza, Curitiba, Porto Alegre, Recife, Manaus
