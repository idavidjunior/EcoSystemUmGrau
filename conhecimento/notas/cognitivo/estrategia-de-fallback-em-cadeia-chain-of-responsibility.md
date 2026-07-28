---
tags: [cognitivo, system_design]
aliases: [Estrategia de fallback em cadeia (Chain of Responsibility)]
date: 2026-07-27
---

# Estrategia de fallback em cadeia (Chain of Responsibility)

**Dominio:** system_design

Quando uma operacao tem multiplas fontes de dados possiveis, organize-as em ordem de preferencia (mais precisa primeiro) com fallback automatico para a proxima. Cada fonte deve reportar claramente se conseguiu ou nao. Nao pare no primeiro resultado — avalie todos e escolha o melhor. Exemplo: MetadataSearch usa AcoustID (fingerprint) -> iTunes BR (scoring) -> MusicBrainz (detalhado) -> iTunes US (fallback).
