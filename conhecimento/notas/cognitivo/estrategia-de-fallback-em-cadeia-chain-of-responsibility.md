---
tags: [automatico, cognitivo, precisa, preferencia, proxima, systemdesign]
aliases: [Estrategia de fallback em cadeia (Chain of Responsibility)]
date: 2026-08-02
---

# Estrategia de fallback em cadeia (Chain of Responsibility)

**Dominio:** system_design

Quando uma operacao tem multiplas fontes de dados possiveis, organize-as em ordem de preferencia (mais precisa primeiro) com fallback automatico para a proxima. Cada fonte deve reportar claramente se conseguiu ou nao. Nao pare no primeiro resultado — avalie todos e escolha o melhor. Exemplo: MetadataSearch usa AcoustID (fingerprint) -> iTunes BR (scoring) -> MusicBrainz (detalhado) -> iTunes US (fallback).
## Conexoes

- [[cache-de-decisoes-caras]]
- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[estrategia-de-loop-autonomo-planejar-executar-verificar-corr]]
- [[padrao-de-escrita-atomica-para-persistencia]]
- [[sempre-esperar-o-inesperado-em-es]]