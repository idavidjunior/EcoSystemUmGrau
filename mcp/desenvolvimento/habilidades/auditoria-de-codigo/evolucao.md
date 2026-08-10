# Evolução da skill auditoria-de-codigo

Registro cronológico de aprendizados e refinamentos da própria skill.

## 2026-08-09 — Criação (técnica aprendida em auditoria do painel StreamUmGrau)
- **Tarefa**: auditar barra lateral / controle `#mastodon-login` que não aparecia
  e painel com crashes aleatórios.
- **O que funcionou**: escanear por fluxo (matriz `chave → grava → lê → status`
  de localStorage; matriz de eventos `gatilho → handler → efeito`) em vez de ler
  arquivos linearmente. Verificar com `node --check` por bloco isolado e `py_compile`
  em vez de confiar no display (que corrompeu/duplicou saídas).
- **O que falhou**: confiar inicialmente em display truncado; perder tempo
  editando o artefato gerado em vez do fonte.
- **Padrão novo**: pipeline de 5 fases (fluxo → ferramentas autoritativas →
  corrigir no fonte → rastrear dado vs código → efeitos colaterais).
