---
tipo: decisao
tags: [etica, niveis, preflight, governance]
data: 2026-08-07
contexto: Requisito do usuário para que a ética tenha três padrões: mínimo (padrão, permite tecnicamente viável com avisos mínimos), médio e máximo.
decisao: Implementado sistema de níveis éticos com configuração em conhecimento/etica/niveis_etica.json e gerenciador scripts/niveis_etica.py. O preflight_etica.py lê o nível atual e promove avisos a bloqueios conforme o rigor configurado. Padrão do ecossistema: minimo.
impacto: Preflight ético APROVADO (exit 0) no nível mínimo com 6 avisos não bloqueantes. Nível médio bloqueia segredos crus e dados sensíveis sem consentimento. Nível máximo bloqueia qualquer risco. Regras imutáveis mínimas (crianças, credenciais em texto plano, exclusão de dados) valem em todos os níveis. Falso positivo de "criança" corrigido (keyword 'crian' -> 'crianc', excluiu 80 arquivos de scan de inventário).
status: operacional
