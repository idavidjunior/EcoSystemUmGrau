---
tipo: erro
tags: [vox, bridge, clima, previsao, hoje, amanha, caminho-rapido]
data: 2026-09-05
contexto: Usuário pediu no app Vox a previsão do tempo para HOJE e a bridge respondia a previsão de AMANHÃ, mesmo repetindo o pedido.
decisao: Causa: no caminho_rapido da bridge, o bloco de previsão capturava qualquer pergunta com 'previsao'/'tempo' e usava SEMPRE previsoes[1] (amanhã), ignorando o dia pedido. get_forecast_data(days=2) retorna índice 0 = hoje e 1 = amanhã. Correção: seleciona idx=1 somente se a pergunta contém a palavra 'amanha'; caso contrário idx=0 (hoje); se o dia não for citado, responde HOJE (comportamento natural). O briefing_espontaneo (saudação) segue usando amanhã de propósito, sem alteração.
impacto: Previsão para hoje responde hoje (mín 15/máx 24) e para amanhã responde amanhã (mín 11/máx 17). Testado via caminho_rapido direto; bridge reiniciada (pid novo 11928) e app reconectado. Casos testados: "previsão do tempo para hoje", "vai chover hoje?", "previsão para amanhã", "vai chover amanhã?", "como vai estar o tempo amanhã", "previsão do tempo" (sem dia -> hoje).
