# 2026-08-01: Cláusula Pétrea — Comunicação contínua em áudio

**Categoria:** decisao
**Contexto:** Usuário apontou que o Jarvis executou tarefas (verificação de sync, commits, pronúncia) sem narrar em áudio o que estava fazendo, desrespeitando a regra de comunicação por voz. A regra existia no contexto da sessão, mas não estava registrada em lugar nenhum — por isso foi esquecida.

## Decisão
**Todo passo que o Jarvis executa DEVE ser narrado em áudio**, sempre, sem exceção, em qualquer tarefa.

## Regras permanentes (registradas em scripts/JARVIS_SYSTEM.md)
1. Antes de agir, fale o que vai fazer ("Vou verificar o git...", "Vou commitar...", "Vou testar a pronúncia...").
2. Durante a execução, acompanhe em voz ("Encontrei...", "Estou ajustando...", "Agora vou sincronizar...").
3. Ao terminar, resuma em áudio o que foi feito e o resultado ("Pronto, tudo sincronizado.").
4. Usar o TTS da bridge (`gerar_audio` / `vox_audio.py falar`) para falar.
5. Vale para TODA sessão e TODA tarefa — é cláusula pétrea, não pode ser esquecida.

## Implementação
- `scripts/JARVIS_SYSTEM.md`: seção "Cláusula Pétrea — Comunicação em Áudio" adicionada logo após a Identidade.
- O `JARVIS_SYSTEM.md` é injetado pela bridge no prompt de todo agente — a regra vale para qualquer sessão.

## Validação
- Regra adicionada ao system prompt (lido a cada conexão) ✓
- Áudio de confirmação gerado e tocado ✓
