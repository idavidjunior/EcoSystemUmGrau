---
tipo: padrao
tags: [saudacao, jarvis, llm, nvidia, api, auto-evolucao, secundario]
data: 2026-08-18
contexto: >
  Sistema de saudacao auto-evolutiva precisava de contribuicao LLM
  como fonte secundaria de variedade. Templates sao primarios, LLM
  complementa com frases mais espontaneas e naturais.
decisao: >
  Integrar NVIDIA API (meta/llama-3.1-8b-instruct) como canal LLM
  secundario. Serve local retorna 500 para novas sessoes (ocupado
  servindo sessao atual), entao usar NVIDIA API direta via urllib.
  Chave lida do .env. LLM gera 5 frases por chamada, salva em
  audacoes_aprendidas.json. Fallback para templates se LLM falhar.
impacto: >
  Jarvis agora combina templates (confiaveis) + LLM (criativo).
  Total de 40+ frases por periodo, mix de origens.
  Sem depender do serve local para geracao de saudacoes.
---
