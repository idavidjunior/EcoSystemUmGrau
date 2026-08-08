---
name: prompt-optimization
description: Otimização e melhoria de prompts usando DSPy (Stanford), PromptWizard (Microsoft) e PromptFlow (Microsoft). Ativa quando o usuário pede para melhorar, otimizar, refinar, aprimorar um prompt, quer mais precisão em prompts, ou quando detecta baixa qualidade em prompts atuais. Trigger keywords: "melhorar prompt", "otimizar prompt", "prompt optimization", "refinar prompt", "aprender com prompts", "prompt engineering", "qualidade de prompt", "prompt review", "testar prompt", "benchmark prompt".
tags: [prompt, otimizacao, dspy, promptwizard, promptflow, llm, engineering]
data: 2026-08-08
---

# Prompt Optimization Pipeline

## Objetivo

Fornecer ao ecossistema uma pipeline completa de **detecção, otimização e melhoria automática de prompts** usando as 3 tecnologias de ponta:

1. **DSPy** (Stanford) — otimização automática via teleprompters (MIPRO, BootstrapFewShot, GEPA)
2. **PromptWizard** (Microsoft) — técnica Critique & Refine para refinamento iterativo
3. **PromptFlow** (Microsoft) — avaliação e experimentação de prompts em produção

## Quando esta skill ativa

- Sempre que o usuário ou o sistema detectar prompts de baixa qualidade
- Sempre que uma tarefa LLM não atender expected outcome
- Como pré-processamento de prompts críticos (cláusulas pétreas, instruções de sistema)
- Para otimização de prompts de agentes especializados
- Para refinamento de prompts de benchmark/avaliação

## Uso na pipeline do ecossistema

```
USUÁRIO → BOOTLOADER → KERNEL → [PROMPT OPTIMIZER] → CONTEXT LOADER → LER/Agente → EXECUÇÃO → AUDITORIA → RESPOSTA
```

### Integração automática (Cláusula Pétrea — Detecção e Correção)

Se **qualquer** problema de prompt for detectado, o ecossistema:
1. **Detecta** — baixa qualidade de prompt (via auditoria de output, métricas de acurácia, LLM feedback)
2. **Avisa** — informa o problema ao usuário
3. **Corrige** — otimiza o prompt automaticamente via pipeline DSPy + PromptWizard
4. **Registra** — salva no history de prompts otimizados
5. **Comunica** — informa o resultado da correção

## DSPy — Otimização Automática

### Conceito

DSPy vira o conceito de "programming for LLMs": em vez de escrever prompts, você escreve programas que os otimizam automaticamente.

```python
import dspy

# Define uma assinatura (input → output)
class RespostaMatematica(dspy.Signature):
    pergunta = dspy.InputField(prefix="Pergunta: ")
    resposta = dspy.OutputField(prefix="Resposta: ")

# Cria um módulo que usa Chain-of-Thought
math_bot = dspy.ChainOfThought(RespostaMatematica)

# Otimiza usando BootstrapFewShot
optimizer = dspy.BootstrapFewShot(metric=minha_metrica)
optimized = optimizer.compile(math_bot, trainset=meu_dataset)
```

### Teleprompters disponíveis

| Teleprompter | Técnica | Uso |
|---|---|---|
| `BootstrapFewShot` | Gera exemplos few-shot | Boa geral |
| `BootstrapFewShotWithRandomSearch` | Gera exemplos + random search | Robusto |
| `MIPRO` | Otimização Bayesiana | Melhor qualidade |
| `COPRO` | Algoritmo genético | Auto-evolução de prompts |
| `BestBaseAccuracy` | Ensemble de múltiplos optimizadores | Máxima acurácia |

## PromptWizard — Critique & Refine

```python
from promptwizard import GluePromptOpt

optimizer = GluePromptOpt(
    prompt_config_path="configs/promptopt_config.yaml",
    setup_config_path="configs/setup_config.yaml",
    dataset_jsonl="data/exemplos.jsonl",
    data_processor=MeuProcessador()
)

best_prompt, expert_profile = optimizer.get_best_prompt(
    use_examples=True,
    generate_synthetic_examples=True
)
```

## Pipeline recomendado

1. **DSPy MIPRO** — otimização automática de prompts e few-shot examples
2. **PromptWizard Critique & Refine** — refinamento iterativo baseado em falhas
3. **PromptFlow** — validação e deploy em produção

## Configuração DSPy no ecossistema

```python
import dspy

# Configuração global
dspy.settings.configure(
    lm=dspy.LM('openai/gpt-4o-mini'),  # ou nvidia/nv-llama-3.1-70b
    trace=[],
)
```

## Métricas recomendadas

- **Accuracy** — % de respostas corretas
- **Relevance** — relevância do output ao input
- **Consistency** — consistência entre múltiplas execuções
- **Brevity** — concisão (penaliza verbosidade)
- **Safety** — alinhamento com cláusulas pétreas

## Referências

- DSPy: https://github.com/stanfordnlp/dspy
- PromptWizard: https://github.com/microsoft/promptwizard
- PromptFlow: https://github.com/microsoft/promptflow

## Arquivos

- `mcp/desenvolvimento/habilidades/prompt-optimization/skill.md` (este arquivo)
- `scripts/prompt_optimizer.py` — MCP server com tools para DSPy, PromptWizard, PromptFlow
- `conhecimento/aprendizados/` — histórico de prompts otimizados
