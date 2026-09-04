---
tipo: padrao
tags: [memoria, unificacao, adb, connection-manager, dedup]
data: 2026-09-04
contexto: Usuário pediu varredura para unificar aprendizados ADB semelhantes/redundantes do Cluster A (auto-conexão + monitor ADB), descartando lixo duplicado.
decisao: Cluster A (memórias 307, 309, 310, 311, 98234, 98235) consolidado em um único registro (memória 312), atualizado para refletir o estado atual do adb_connection_manager.py. Clusters B (Tailscale/endereço) e C (perito ADB) preservados como referência técnica distinta.
impacto: Reduziu 6 registros redundantes para 1; recuperação semântica mais limpa; registros duplicados como rascunho (98234/98235) eliminados da base.
notas: Escrita atômica no memories.json (tmp + os.replace) com backup .bak-cluster-unif e validação JSON. Reindex semântico TF-IDF reexecutado (1678 docs) + rebuild denso em background. Lock de memória órfão (memories.json.lock) removido com segurança (7min de idade, sem processo ativo segurando — provável reindex interrompido).
