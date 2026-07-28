# Mapa de Conteúdo — Conhecimento Técnico

> Base completa no [[ler-runtime/CONHECIMENTO.md]] — carregada no contexto de todo agente.

## Categorias

### Decisões Arquiteturais
- LER usa Python puro (stdlib only)
- Estado persiste em JSON (human-readable)
- Checkpoints salvos antes de cada iteração
- Pontuação ponderada com 6 categorias
- Metadata busca multi-fontes (AcoustID → iTunes → MusicBrainz)
- Single Activity com FrameLayout (sem Fragments)
- Form Starts Empty
- Salvar cria novo arquivo timestampado

### Padrões Técnicos (71 registrados)
- Build Pipeline Intelligence (aapt + javac + d8 + apksigner)
- Metadata Search Pipeline (scoring thresholds)
- Strategy Engine v2.0
- Custom Numpad Pattern
- JSON Persistence Pattern
- E mais...

### Skills (34)
Disponíveis em [[skills/]]:
- android-pure-sdk, mobile-specific-patterns, mp3player-metadata-rescue
- python-patterns, golang-patterns, backend-patterns, frontend-patterns
- security-review, data-privacy-by-design, observability-stack
- tdd-workflow, e2e-testing, autonomous-loops
- E mais...

---
\`\`\`dataview
TABLE file.cday as "Criado"
FROM "conhecimento/aprendizados"
WHERE contains(file.name, "scan") = false
SORT file.cday DESC
\`\`\`
