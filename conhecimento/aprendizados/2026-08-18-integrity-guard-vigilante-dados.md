---
tipo: padrao
tags: [integracao, vigilancia, mojibake, integridade, dados]
data: 2026-08-18
contexto: O ecossistema sofreu corrupção de dados por mojibake (texto UTF-8 lido como CP1252) em vários JSONs de conhecimento. A correção do knowledge_graph foi manual e não se repetia. Decidiu-se criar um vigilante permanente de integridade de dados.
decisao: Criar scripts/integrity_guard.py, um detector/corretor de mojibake e truncamento em 13 JSONs de conhecimento, com backup, escrita atômica e proteção contra falsos positivos. Integrado aos gatilhos naturais: runtime_boot --check, preflight_check seção [10] e vigilante.ps1 (timer 1h com --fix + comunicação via Write-Log e memory_engine log).
implementacao:
  - Modo --check (scan + exit 0/1), --fix (corrige + backup em runtime/backups/integrity_guard/), --json, --targets
  - Modo --audit (prevenção): escaneia scripts por escritas sem encoding UTF-8 / sem ensure_ascii e corrige com backup + validação py_compile
  - Auditoria também reporta .py que não compilam (risco de runtime) — sem correção automática segura, apenas reporta
  - Alvos padrão incluem as fontes de reindex semântico (conhecimento/notas, conhecimento/aprendizados, docs, documentos): mojibake nelas se propaga para tfidf_meta.json
  - Auto-resiliência: pós-validação após correção (re-leitura + re-scan) com rollback automático para backup se falhar
  - SUBST_PAIRS com pares inequívocos pt-BR (inclui sequências 3-bytes para em-dash, apóstrofo, aspas, reticências)
  - fix_mojibake: round-trip cp1252 completo + substituição direcionada para strings mistas
  - atomic_write_json: tmp + os.replace (anti-corrupção)
  - Falsos positivos protegidos: "NÃO"/"ATIVAÇÃO" legítimos e em-dash "—" legítimo NÃO são alterados
  - Strings não reversíveis com segurança (ex.: dupla corrupção) são deixadas intactas (confiança alta primeiro)
  - Detecção por reversibilidade real (não só presença de gatilho); documentação que cita padrões deve usar notação de escape (\u00e1) para não ser confundida com corrupção real
validacao:
  - Detectou e corrigiu 55 strings reais em memories.json (17) e tfidf_meta.json (38)
  - Re-check estabilizou em 0 corrupções; JSONs continuam válidos
  - Teste de falso positivo: NÃO, ATIVAÇÃO, CONSTITUIÇÃO, em-dash legítimo inalterados
  - Teste de fluxo completo com arquivo injetado: detecta, corrige, backup, escrita atômica, estável
  - Auditoria de scripts: corrigiu escritas perigosas em 12 arquivos (sem encoding UTF-8 ou sem ensure_ascii), com backup e py_compile OK
  - Rollback verificado: correção que quebraria sintaxe em memory_semantic.py foi descartada automaticamente
  - Causa raiz da recorrência eliminada: 39 .md antigos com mojibake real corrigidos (fonte do reindex do memory_engine); tfidf_meta.json regenerado limpo e reindex de 1133 docs não reintroduziu corrupção
  - clean_sessions.py (stub markdown tratado como .py, não compilava) convertido em stub Python válido
  - runtime_boot --check: INTEGRIDADE OK com nova seção
  - preflight_check: TODOS TESTES PASSARAM (13 MCP online, seção [10] nova)
  - vigilante.ps1: SYNTAX OK, parsing do relatório validado em PowerShell
  - Boot completo sem regressão
impacto: Corrupção de dados por mojibake agora é detectada e corrigida automaticamente em todo boot, preflight e a cada hora via vigilante, com backup sempre disponível para rollback. A fonte do problema (escritas de código sem UTF-8 e .md corrompidos que alimentam o índice semântico) é auditada e corrigida preventivamente.
