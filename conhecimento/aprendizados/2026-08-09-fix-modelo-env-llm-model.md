---
tipo: erro
tags: [opencode, config, llm, placeholder, model_not_found, eco-system, sync]
data: 2026-08-09
contexto: Ao trocar de LLM, contextos, tarefas e projetos deixaram de ser reconhecidos em sessoes novas. Investigacao revelou que o placeholder {{LLM_MODEL}} no config de opencode NAO e substituido pelo opencode, gerando model_not_found que quebrava o boot das sessoes novas (sem fallback em vigor).
decisao: Substituir o placeholder nao-resolvivel por {env:LLM_MODEL} (mecanismo nativo de env do opencode, o mesmo ja usado na apiKey) tanto no template config/opencode.jsonc quanto no deployed ~/.config/opencode/opencode.jsonc, mantendo-os identicos para o @sync (que copia o template) nao regredir o fix. Modelo persistido via setx LLM_MODEL=opencode/big-pickle. Chave NVIDIA unificada: config usa {env:NVIDIA_API_KEY} e a chave hardcoded foi removida do projeto.
impacto: Modelo primario sempre resolve; sessoes novas carregam AGENTS.md/estado/memoria de forma estavel; troca futura de LLM = editar env LLM_MODEL (restart), sem editar config. Preflight agora exige LLM_MODEL definida.
validacao: check_jsonc OK (template e deployed), template == deployed, opencode debug config resolveu model para opencode/big-pickle e apiKey unica, preflight_check.py TODOS TESTES PASSARAM.
detalhes: LICAO: no opencode, placeholders suportados sao {env:VAR} (e {{USERPROFILE}} que o proprio opencode expande) — NUNCA inventar placeholder proprio como {{LLM_MODEL}}. Ao adicionar/mudar modelo, manter template e deployed sincronizados (mesmo conteudo) e garantir a env definida antes do preflight.

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]