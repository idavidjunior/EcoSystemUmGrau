# Cruzamento Epistêmico — Memória + Cache Externo + Aprendizados

## Objetivo
Permitir que o agente raciocine sobre o próprio conhecimento, combinando três fontes:
- **Memória episódica** (`memory_engine.py`) — experiência vivida, com `confidence` e `source_type`
- **Cache externo** (Wikidata via `evolution_radar_collect.py`) — fatos universais verificáveis
- **Aprendizados consolidados** (`conhecimento/aprendizados/`) — decisões arquiteturais, padrões, erros

## Uso
```bash
# Via skill
python mcp/nucleo/habilidades/epistemico-cruzamento/epistemico.py "<pergunta>"

# Via MCP tool (quando registrado)
epistemico_cruzamento:cruzar "<pergunta>"
```

## Funções estruturadas
- `cruzar(pergunta: str) -> dict` — busca nas 3 fontes, ranqueia por confiança, retorna síntese
- `get_memory_context(topic: str) -> list` — memórias relevantes com confidence/source
- `get_wikidata_context(entity: str) -> dict` — consulta Wikidata SPARQL
- `get_aprendizados_context(topic: str) -> list` — busca em aprendizados (BM25)

## Retorno padronizado
```json
{
  "pergunta": "...",
  "sintese": "Resumo curto em pt-BR",
  "fontes": [
    {"tipo": "memoria", "items": [...], "confidence_media": 0.85},
    {"tipo": "wikidata", "items": [...], "confidence_media": 0.95},
    {"tipo": "aprendizados", "items": [...], "confidence_media": 0.9}
  ],
  "lacunas": ["o que não sabemos com confiança"],
  "recomendacao": "próximo passo sugerido"
}
```

## Níveis de confiança
- **Fato confirmado** (confidence >= 0.9, source_type in [experiencia, api]): usar direto
- **Provável** (confidence 0.7-0.9): usar com verificação
- **Hipótese** (confidence < 0.7): marcar como incerto, buscar validação

## Integração com Evolution Radar
Quando o radar detecta uma proposta, usa este skill para:
1. Verificar se já sabemos algo sobre o tema (memória)
2. Buscar fatos externos (Wikidata: versões, specs, padrões)
3. Verificar aprendizados passados (decisões, erros, padrões)
4. Gerar recomendação fundamentada para validar/rejeitar