---
tipo: decisao
tags: [saudacao, continuidade, bridge, contexto, janela-conversa]
data: 2026-08-06
contexto: Usuario reclamou que Jarvis repetia saudacao inicial a cada nova conexao WebSocket, mesmo dentro da mesma sessao de conversa, ignorando o historico recente. Quebra a naturalidade e a sensacao de continuidade.
decisao: Adicionar janela de conversa ativa (JANELA_CONVERSA_MIN = 30 min) na bridge. Antes de chamar `saudar()`, checa o mtime do `conversa_unica.json` via `_ultima_atividade_minutos()`. Se a ultima fala foi ha menos de 30 minutos E ha historico, suprime a saudacao inicial — a conversa flui sem "recomeco". Fora da janela (ou sem historico), saudacao normal e gerada via LLM.
impacto: Jarvis agora respeita a continuidade contextual dentro da mesma sessao operacional. Reconexoes dentro de 30 min nao repetem "Bom dia"/"Boa tarde" — a conversa continua de onde estava. Isso atende explicitamente ao pedido do usuario de nao recomecar a cada interacao e manter o humor/personalidade/contexto fluindo.
arquivos: [scripts/jarvis_bridge.py]
funcoes: [_ultima_atividade_minutos, lidar]
referencias: [conversa_unica.json, clausula_petrea_continuidade_contexto_04_08_2026]
---
