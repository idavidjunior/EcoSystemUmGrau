# Mapa de Conteúdo — Projetos

## Android

### Mp3Player
- **Repo:** `Android/Mp3Player/`
- **Stack:** Kotlin, ExoPlayer, Equalizer
- **Features:** Metadata search (AcoustID → iTunes → MusicBrainz), equalizer 20 bandas, soft-clipping, peak limiter, play count tracking
- **Bug fixes:** EQ distorção, preset locale pt_BR, preamp cumulativo, AudioProcessor pipeline
- [[MOC - Bugs#Mp3Player|Bugs do Mp3Player]]

### CellCleaner
- **Repo:** `Android/CellCleaner/`
- **Stack:** Java, Android SDK
- **Features:** Limpeza de arquivos temporários, gerenciamento de permissões

### SupermarketCalculator
- **Repo:** `Android/SupermarketCalculator/`
- **Stack:** Java, Android SDK
- **Features:** Cálculo de compras, comparação de preços

### Biblia
- **Repo:** `Android/Biblia/`
- **Stack:** Java, Android SDK
- **Features:** Estudo bíblico completo

## Ecossistema

### EcoSystemUmGrau
- **Repo:** `EcoSystemUmGrau/` (este vault)
- **Stack:** PowerShell, Python, OpenCode, LER
- **Features:** Vigilante automático, knowledge graph, 15 agentes OpenCode, LER runtime, setup.bat plug & play
- [[estado_atual.md|Snapshot completo]]

---
\`\`\`dataview
TABLE file.cday as "Criado", file.etags as "Tags"
FROM "conhecimento/aprendizados"
WHERE contains(file.name, "scan")
SORT file.cday DESC
\`\`\`
