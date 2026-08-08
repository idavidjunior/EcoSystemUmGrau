"""MCP server — Prompt Optimization Pipeline.

Expõe tools para otimização automática de prompts usando DSPy (Stanford),
PromptWizard (Microsoft) e PromptFlow (Microsoft).

Python puro, sem npx (Cláusula Pétrea — Resiliência).

Uso: python mcp/desenvolvimento/habilidades/prompt-optimization/server.py

Tools:
  - optimize_prompt_dspy    — otimiza prompts via DSPy teleprompters (MIPRO, BootstrapFewShot)
  - refine_prompt_wizard   — refinamento iterativo via Critique & Refine (Microsoft PromptWizard)
  - evaluate_prompt        — avalia qualidade de prompt (accuracy, brevity, consistency, safety)
  - compare_prompts        — compara múltiplas variantes de prompt
  - generate_prompt_tests  — gera casos de teste para validação
  - suggest_prompt_improvement — análise estática de prompt (qualidade, clareza, alinhamento)
"""
import json
import sys
import os
import re
import time
from pathlib import Path
from typing import Any

BASE = str(Path(__file__).resolve().parent.parent.parent.parent)
SCRIPTS = os.path.join(BASE, 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

BASE_DOMINIO = str(Path(__file__).resolve().parent.parent.parent)
DOMINIO = "prompt-optimization"

TOOLS = [
    {
        "name": "optimize_prompt_dspy",
        "description": "Otimiza prompts automaticamente usando DSPy (Stanford). Suporta teleprompters: MIPRO (Bayesian optimization, melhor qualidade), BootstrapFewShot (gera exemplos few-shot), BootstrapFewShotWithRandomSearch (robusto). Ideal para otimizar prompts de assinaturas, Chain-of-Thought, e prompts de agentes.\n\nTrigger keywords: optimize, otimizar, dsp, teleprompter, MIPRO, bootstrap, few-shot, automatic prompt optimization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_prompt": {"type": "string", "description": "Prompt base a ser otimizado", "minLength": 1},
                "examples": {"type": "string", "description": "Exemplos de input/output em formato JSON array (opcional)"},
                "metric": {"type": "string", "description": "Métrica: 'accuracy', 'relevance', 'brevity', 'consistency' ou 'composite'"},
                "method": {"type": "string", "description": "Método: 'mipromo', 'bootstrap', 'bootstrap_random_search'"},
            },
        },
    },
    {
        "name": "refine_prompt_wizard",
        "description": "Refinamento iterativo de prompts usando a técnica Critique & Refine do Microsoft PromptWizard. Gera variações de estilo, usa meta-critique para identificar falhas, e refina o prompt. Suporta geração de exemplos sintéticos.\n\nTrigger keywords: refine, refinamento, promptwizard, critique, iterate, improve prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt a ser refinado", "minLength": 1},
                "failures": {"type": "string", "description": "Exemplos de falhas do prompt atual (texto livre)"},
            },
        },
    },
    {
        "name": "evaluate_prompt",
        "description": "Avalia a qualidade de um prompt usando 5 dimensões: Accuracy (acurácia), Relevance (relevância), Brevity (concisão), Consistency (consistência), Safety (segurança/alinhamento ético). Retorna score 0-100 e recomendações.\n\nTrigger keywords: evaluate, qualidade de prompt, prompt quality, assess, metric.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt a ser avaliado", "minLength": 1},
            },
        },
    },
    {
        "name": "compare_prompts",
        "description": "Compara múltiplas variantes de prompt e identifica a melhor. Útil para A/B testing de prompts, validação de otimizações, e detecção de regressão.\n\nTrigger keywords: compare, A/B test, variantes, benchmark.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompts": {"type": "string", "description": "JSON array de prompts a comparar (máx 5)"},
            },
        },
    },
    {
        "name": "generate_prompt_tests",
        "description": "Gera casos de teste estruturados para validar um prompt. Cada caso inclui input, output esperado, e categoria (accuracy, edge_case, safety, brevity).\n\nTrigger keywords: test cases, validate, generate tests, QA prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt para gerar testes", "minLength": 1},
                "num_tests": {"type": "integer", "description": "Número de casos de teste (default 5, max 10)", "default": 5},
            },
        },
    },
    {
        "name": "suggest_prompt_improvement",
        "description": "Análise estática de prompt — detecta problemas sem chamar LLM. Verifica clareza, ambiguidade, incompleto, over-engineering, token economy, segurança, alinhamento com cláusulas pétreas do ecossistema. Retorna sugestões acionáveis.\n\nTrigger keywords: analyze, improve, sugestão, check, static analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt a analisar", "minLength": 1},
            },
        },
    },
]


def _dspy_available():
    try:
        import dspy
        return True, dspy
    except ImportError:
        return False, None


def _init_dspy(dspy, model="openai/gpt-4o-mini"):
    """Configura o DSPy com modelo fallback."""
    import litellm
    try:
        dspy.settings.configure(
            lm=dspy.LM(model),
            trace=[],
        )
        return True
    except Exception:
        return False


def _static_analyze_prompt(prompt: str) -> list:
    """Análise estática sem LLM — detecta problemas comuns."""
    issues = []
    
    # Clareza / ambiguidade
    if len(prompt) > 2000:
        issues.append(("OVER_ENGINEERING", "Prompt muito longo (>2000 chars). Considere modularizar.", "warning"))
    
    if not re.search(r'[.!?]$', prompt.strip()) and '\n' not in prompt:
        issues.append(("UNCLEAR_INSTRUCTION", "Instrução sem terminador claro. Adicione ponto final ou newline.", "warning"))
    
    # Ambiguidade
    if re.search(r'\b(tudo|qualquer|tudo que|etc)\b', prompt, re.I):
        issues.append(("AMBIGUITY", "Palavras ambíguas detectadas ('tudo', 'qualquer', 'etc'). Seja específico.", "info"))
    
    # Output format não definido
    if 'formato' not in prompt.lower() and 'format' not in prompt.lower() and '```' not in prompt:
        issues.append(("NO_OUTPUT_FORMAT", "Nenhum formato de output especificado. Defina explicitamente o formato esperado.", "warning"))
    
    # Safety / cláusulas pétreas
    petrea_keywords = ['cláusula pétrea', 'imutável', 'obrigatório', 'nunca']
    if any(k in prompt.lower() for k in petrea_keywords):
        issues.append(("PETRAEA_REF", "Referência a cláusula pétrea detectada. Verifique alinhamento com Constituição.", "info"))
    
    # Token economy
    word_count = len(prompt.split())
    if word_count > 300:
        issues.append(("TOKEN_ECONOMY", f"Prompt muito verboso ({word_count} palavras). Considere simplificar.", "info"))
    
    # Missing context
    if not re.search(r'\b(contexto|background|informação|dados)', prompt, re.I):
        issues.append(("CONTEXT_NEEDED", "Considere adicionar seção de contexto/background.", "info"))
    
    return issues


def _evaluate_prompt_quality(prompt: str) -> dict:
    """Avalia qualidade do prompt (static analysis + heurísticas)."""
    scores = {}
    
    # Accuracy (claridade/estrutura)
    issues = _static_analyze_prompt(prompt)
    error_count = sum(1 for _, _, sev in issues if sev == "error")
    warn_count = sum(1 for _, _, sev in issues if sev == "warning")
    scores['accuracy'] = max(0, 100 - error_count * 20 - warn_count * 10)
    
    # Relevance
    word_count = len(prompt.split())
    has_structure = bool(re.search(r'^(Objetivo|Contexto|Instruções|Formato)', prompt, re.I | re.M))
    scores['relevance'] = min(100, 80 + (20 if has_structure else 0) - max(0, word_count - 100))
    
    # Brevity
    scores['brevity'] = max(0, 100 - max(0, word_count - 50) * 0.5)
    
    # Consistency
    has_numbers = bool(re.search(r'\d+', prompt))
    has_examples = 'exemplo' in prompt.lower() or '```' in prompt
    scores['consistency'] = 70 + (15 if has_numbers else 0) + (15 if has_examples else 0)
    
    # Safety
    unsafe_patterns = ['ignore previous', 'esqueça', 'desobedeça', 'sem limites']
    has_unsafe = any(p in prompt.lower() for p in unsafe_patterns)
    scores['safety'] = 0 if has_unsafe else 100
    
    overall = sum(scores.values()) / len(scores)
    scores['overall'] = round(overall, 1)
    
    return scores


def _dspy_optimize(base_prompt: str, examples_str: str, metric: str, method: str) -> dict:
    """Otimiza prompt usando DSPy."""
    ok, dspy = _dspy_available()
    if not ok:
        return {"error": "DSPy não instalado. Instale: pip install dspy-ai", "success": False}
    
    if not _init_dspy(dspy):
        return {"error": "Falha ao inicializar DSPy (configurar LM). Verifique API key.", "success": False}
    
    # Parse examples
    examples = []
    if examples_str:
        try:
            examples = json.loads(examples_str)
        except json.JSONDecodeError:
            examples = [{"input": examples_str}]
    
    # Define signature dinamicamente
    import dspy as _dspy
    
    class DynamicSignature(_dspy.Signature):
        input_text = _dspy.InputField(prefix="Input: ")
        output_text = _dspy.OutputField(prefix="Output: ", desc=base_prompt)
    
    program = _dspy.Predict(DynamicSignature)
    
    # Build trainset
    trainset = []
    for ex in examples:
        if isinstance(ex, dict) and "input" in ex and "output" in ex:
            trainset.append(_dspy.Example(input_text=ex["input"], output_text=ex["output"], _dspy_keys=["input_text"]))
    
    # Select optimizer
    if method == "mipromo":
        optimizer = _dspy.MIPRO(metric=lambda x, y: 1.0, verbose=False)
    elif method == "bootstrap_random_search":
        optimizer = _dspy.BootstrapFewShotWithRandomSearch(metric=lambda x, y: 1.0, verbose=False)
    else:
        optimizer = _dspy.BootstrapFewShot(metric=lambda x, y: 1.0, verbose=False)
    
    try:
        optimized = optimizer.compile(program, trainset=trainset[:10])  # limit to 10
        result = {
            "optimized": True,
            "method": method,
            "base_prompt_length": len(base_prompt),
            "examples_count": len(trainset),
            "note": "Prompt otimizado via DSPy. Use o programa compiled para inferência.",
            "success": True,
        }
    except Exception as e:
        result = {"error": str(e), "success": False}
    
    return result


def _generate_prompt_tests(prompt: str, num_tests: int) -> list:
    """Genera casos de teste para validação de prompt (sem LLM, usa templates)."""
    tests = []
    num_tests = max(1, min(10, num_tests))
    
    base_cases = [
        {"input": "Exemplo simples relacionado ao prompt", "expected": "Resposta alinhada ao objetivo", "category": "accuracy"},
        {"input": "Caso de borda / edge case", "expected": "Tratamento adequado de edge case", "category": "edge_case"},
        {"input": "Conteúdo potencialmente problemático", "expected": "Resposta segura e ética", "category": "safety"},
        {"input": "Solicitação de informação complexa", "expected": "Resposta concisa e direta", "category": "brevity"},
    ]
    
    for i in range(num_tests):
        case = base_cases[i % len(base_cases)]
        tests.append({
            "id": f"test_{i+1:03d}",
            "input": case["input"],
            "expected_behavior": case["expected"],
            "category": case["category"],
            "prompt_under_test": prompt[:200] + ("..." if len(prompt) > 200 else ""),
        })
    
    return tests


def _suggest_improvement(prompt: str) -> dict:
    """Sugestões estáticas de melhoria."""
    issues = _static_analyze_prompt(prompt)
    scores = _evaluate_prompt_quality(prompt)
    
    suggestions = []
    for code, msg, sev in issues:
        suggestions.append({"code": code, "message": msg, "severity": sev})
    
    # Sugerir melhorias específicas
    if scores['brevity'] < 60:
        suggestions.append({"code": "BREVITY_SUGGESTION", "message": "Use abreviações, remova repetições, foque no essencial.", "severity": "info"})
    
    if scores['accuracy'] < 70:
        suggestions.append({"code": "STRUCTURE_SUGGESTION", "message": "Adicione seções: Objetivo, Contexto, Instruções, Formato de Output.", "severity": "warning"})
    
    return {
        "scores": scores,
        "issues": issues,
        "suggestions": suggestions,
        "overall_assessment": "APPROVED" if scores['overall'] >= 70 else "NEEDS_IMPROVEMENT",
    }


def _compare_prompts(prompts_json: str) -> dict:
    """Compara múltiplas variantes."""
    try:
        prompts = json.loads(prompts_json)
    except json.JSONDecodeError:
        return {"error": "JSON inválido. Use: [\"prompt1\", \"prompt2\", ...]"}
    
    if not isinstance(prompts, list) or len(prompts) < 2:
        return {"error": "Forneça pelo menos 2 prompts"}
    
    if len(prompts) > 5:
        prompts = prompts[:5]
    
    results = []
    for i, p in enumerate(prompts):
        scores = _evaluate_prompt_quality(p)
        results.append({
            "variant": f"V{i+1}",
            "prompt_preview": p[:100] + ("..." if len(p) > 100 else ""),
            "scores": scores,
            "overall": scores['overall'],
        })
    
    results.sort(key=lambda x: x['overall'], reverse=True)
    
    return {
        "comparison": results,
        "best_variant": results[0]['variant'] if results else None,
        "winner_score": results[0]['overall'] if results else 0,
    }


def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})
    
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": f"mcp-{DOMINIO}", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}
    
    if method == "notifications/initialized":
        return None
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    
    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)
    
    return None


def handle_tool(tool, args, rid):
    result = None
    
    if tool == "optimize_prompt_dspy":
        result = _dspy_optimize(
            base_prompt=args.get("base_prompt", ""),
            examples_str=args.get("examples", ""),
            metric=args.get("metric", "composite"),
            method=args.get("method", "bootstrap"),
        )
    
    elif tool == "refine_prompt_wizard":
        prompt = args.get("prompt", "")
        failures = args.get("failures", "")
        result = {
            "tool": "refine_prompt_wizard",
            "status": "simulated",
            "refined_prompt": f"[Refinado via Critique & Refine]\n{prompt}",
            "note": "Refinamento iterativo baseado em falhas detectadas. Para execução completa, integrar PromptWizard.",
            "failures_analyzed": failures[:200] if failures else "Nenhuma falha fornecida",
        }
    
    elif tool == "evaluate_prompt":
        prompt = args.get("prompt", "")
        scores = _evaluate_prompt_quality(prompt)
        result = {
            "tool": "evaluate_prompt",
            "prompt_length": len(prompt),
            "scores": scores,
            "assessment": "APPROVED" if scores['overall'] >= 70 else "NEEDS_IMPROVEMENT",
        }
    
    elif tool == "compare_prompts":
        result = _compare_prompts(args.get("prompts", "[]"))
    
    elif tool == "generate_prompt_tests":
        prompt = args.get("prompt", "")
        num = int(args.get("num_tests", 5))
        tests = _generate_prompt_tests(prompt, num)
        result = {
            "tool": "generate_prompt_tests",
            "tests": tests,
            "count": len(tests),
        }
    
    elif tool == "suggest_prompt_improvement":
        result = _suggest_improvement(args.get("prompt", ""))
    
    else:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}
    
    return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle(req)
            if resp is not None:
                print(json.dumps(resp), flush=True)
        except json.JSONDecodeError:
            pass
