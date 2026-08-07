---
tipo: decisao
tags: [memoria-semantica, embeddings, dense, sinonimos, significado, busca]
data: 2026-08-07
contexto: Análise do ecossistema revelou que a semântica era mecânica (TF-IDF puro, matching de palavras). A camada densa de embeddings existia mas era opcional e subutilizada (peso 50/50, só carregava se já construída). Usuário pediu evolução escolhendo o que aprender.
decisao: A camada densa de embeddings (paraphrase-multilingual-MiniLM-L12-v2) passa a LIDERAR a busca com peso 0.65, TF-IDF com expansão complementa com 0.35. Adicionado léxico SINONIMOS (pt-br, domínio do ecossistema) em expandir_query() para capturar intenção. A matriz densa é construída automaticamente (best-effort) no cold-cache se ausente.
impacto: Busca 'a conexao quebrou e precisa voltar' retorna nota de persistência de conexão. Busca 'recuperar conexao apos queda do android' retorna top-3 os aprendizados de Recuperação Rápida de Conexão. Busca 'como fazer o celular voltar a se conectar' recupera memória #77 (watchdog/bridge) por significado, sem palavras idênticas. Py_compile OK, preflight_check TODOS TESTES PASSARAM.
status: operacional
