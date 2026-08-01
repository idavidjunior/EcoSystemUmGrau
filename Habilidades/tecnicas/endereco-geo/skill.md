# Endereço por Geolocalização — Nominatim/OpenStreetMap (sem chave)

## Como usar
Descobre o endereço (rua e, quando disponível, número) a partir das coordenadas obtidas por IP, com geolocalização reversa do OpenStreetMap (gratuito, sem API key).

```bash
python Habilidades/tecnicas/endereco-geo/endereco.py
# → JSON completo com latitude, longitude, endereço detalhado e texto formatado

python Habilidades/tecnicas/endereco-geo/endereco.py --texto
# → "Avenida Paulista, 1000, Bela Vista, São Paulo, SP, CEP 01310-100"

python Habilidades/tecnicas/endereco-geo/endereco.py --lat -23.5475 --lon -46.6361
# → Reverse geocode de coordenadas explícitas
```

Funções estruturadas:

- `get_endereco(lat, lon)` → dict {latitude, longitude, endereco (address details), texto, display_name}
- `get_localizacao()` → coordenadas por IP (ip-api.com)
- `reverse_geocode(lat, lon)` → resposta bruta do Nominatim (addressdetails)
- `formatar_endereco(dados)` → texto amigável em pt-BR

## Limitações (importante)
- Geolocalização por IP tem precisão de cidade/bairro — o número da casa é o do ponto mapeado mais próximo, não garantia do endereço exato do usuário.
- Para endereço exato com número real, o ideal é GPS do celular (enviar lat/lon via `--lat`/`--lon`).
- Nominatim tem uso gratuito com limite de 1 requisição por segundo — nunca chamar em loop rápido.

## Dependências
- `requests`

## Fontes
- ip-api.com (coordenadas por IP)
- nominatim.openstreetmap.org (geolocalização reversa)
