# 2026-08-02 - Feedback contínuo em tarefas longas

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** baixa

## Contexto

O usuário pediu mais transparência durante tarefas demoradas: não queria ficar
esperando em silêncio sem saber o que o Jarvis está fazendo ou se há progresso.

## Decisão

Adicionada regra permanente de **feedback contínuo** em `JARVIS_SYSTEM.md`:
- Regra 16 em "Regras de Resposta".
- Nova seção "Regra de Feedback Contínuo (02/08/2026)".

O que mudou na prática:
- Antes de agir: avisar o plano.
- Durante: relatar descobertas, bloqueios e decisões em voz.
- Em esperas longas (LLM 20-30s, builds, testes): enviar status intermediário.
- Ao concluir: resumir resultado.

## Lição

O usuário prefere receber atualizações frequentes e curtas a um único relatório
final longo. Transparência durante a execução reduz a sensação de espera inútil.
