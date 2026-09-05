---
tipo: padrao
tags: [vox, edicao, edit-and-resubmit, app-android, bridge]
data: 2026-09-04
contexto: O usuário pediu para implementar no app Vox a edição de mensagem já enviada, seguindo o padrão das outras IAs (ChatGPT/Claude).
decisao: Implementado o padrão edit-and-resubmit em duas partes. Na bridge (scripts/jarvis_bridge.py): novo tipo de mensagem "editar" com texto_antigo/texto_novo; a função _aplicar_edicao trunca o histórico (conversa_unica.json) na última ocorrência do texto normalizado (caixa baixa, sem acento, sem prefixo Usuário:/Jarvis:, espaços colapsados) e o fluxo regenera a resposta para o texto novo; ACK é enviado também em caso de falha (não encontrou) para limpar a fila do app. No app (VoxUmGrau): VoxWebSocket.editarMensagem envia o comando; VoxViewModel.editarMensagem descarta localmente as mensagens a partir do índice editado e reenvia; JarvisChatScreen mostra lápis nos balões do usuário e um editor inline (EditMessageBubble em MessageBubble.kt) com salvar/cancelar; onMessage trata edicao_falhou restaurando a mensagem original. 
impacto: Padrão de UX alinhado às IAs modernas; editar uma mensagem antiga regenera todo o fluxo a partir dela, descartando o futuro. Histórico fica consistente entre app e bridge (formato "Usuário: ..." / "Jarvis: ..." unificado).
