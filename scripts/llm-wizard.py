#!/usr/bin/env python3
"""llm-wizard.py — Assistente interativo para escolha do modelo LLM.

Detecta provedores disponíveis (baseado em API keys no ambiente) e permite
ao usuário escolher seu modelo primário. O valor escolhido pode ser usado
pelo setup-auto.ps1 para renderizar {{LLM_MODEL}} no opencode.jsonc.

Uso:
  python scripts/llm-wizard.py                    # modo interativo
  python scripts/llm-wizard.py --detect-only      # lista provedores sem prompt
  python scripts/llm-wizard.py --json             # output JSON (para automação)
"""
import json
import os
import sys
import io


# Modelos nativos do OpenCode (não precisam de API key)
NATIVE_MODELS = [
    {
        "model": "opencode/deepseek-v4-flash-free",
        "provider": "opencode",
        "name": "DeepSeek v4 Flash (Free)",
        "description": "Rápido, gratuito via OpenCode",
        "requires_key": False,
        "recommended": True,
    },
    {
        "model": "opencode/laguna-s-2.1-free",
        "provider": "opencode",
        "name": "Laguna S 2.1 (Free)",
        "description": "Modelo atualmente em uso pelo ecossistema",
        "requires_key": False,
        "recommended": False,
    },
    {
        "model": "opencode/nemotron-3-ultra-free",
        "provider": "opencode",
        "name": "Nemotron-3 Ultra (Free)",
        "description": "Alta performance via OpenCode",
        "requires_key": False,
        "recommended": False,
    },
    {
        "model": "opencode/ling-3.0-flash-free",
        "provider": "opencode",
        "name": "Ling 3.0 Flash (Free)",
        "description": "Leve e rápido via OpenCode",
        "requires_key": False,
        "recommended": False,
    },
    {
        "model": "opencode/mimo-v2.5-free",
        "provider": "opencode",
        "name": "Mimo v2.5 (Free)",
        "description": "Eficiente via OpenCode",
        "requires_key": False,
        "recommended": False,
    },
    {
        "model": "opencode/north-mini-code-free",
        "provider": "opencode",
        "name": "North Mini Code (Free)",
        "description": "Focado em código via OpenCode",
        "requires_key": False,
        "recommended": False,
    },
    {
        "model": "opencode/big-pickle",
        "provider": "opencode",
        "name": "Big Pickle",
        "description": "Experimental via OpenCode",
        "requires_key": False,
        "recommended": False,
    },
]

# Modelos via providers (necessitam de API key)
PROVIDER_MODELS = {
    "NVIDIA_API_KEY": {
        "provider_name": "NVIDIA",
        "models": [
            {
                "model": "nvidia/nemotron-4-340b-reward",
                "provider": "nvidia",
                "name": "Nemotron-4 340B Reward",
                "description": "Reward model da NVIDIA",
                "requires_key": True,
                "recommended": False,
            },
            {
                "model": "nvidia/llama-3-70b",
                "provider": "nvidia",
                "name": "Llama 3 70B (NVIDIA)",
                "description": "Llama 3 via NVIDIA API",
                "requires_key": True,
                "recommended": False,
            },
        ],
    },
    "OPENAI_API_KEY": {
        "provider_name": "OpenAI",
        "models": [
            {
                "model": "openai/gpt-4o",
                "provider": "openai",
                "name": "GPT-4o",
                "description": "Modelo mais avançado da OpenAI",
                "requires_key": True,
                "recommended": False,
            },
            {
                "model": "openai/gpt-4o-mini",
                "provider": "openai",
                "name": "GPT-4o Mini",
                "description": "Versão mais rápida e econômica",
                "requires_key": True,
                "recommended": False,
            },
        ],
    },
    "ANTHROPIC_API_KEY": {
        "provider_name": "Anthropic",
        "models": [
            {
                "model": "anthropic/claude-3-5-sonnet-latest",
                "provider": "anthropic",
                "name": "Claude 3.5 Sonnet",
                "description": "Modelo mais avançado da Anthropic",
                "requires_key": True,
                "recommended": True,
            },
        ],
    },
}


def detect_providers():
    """Detecta quais providers estão disponíveis baseado em API keys no ambiente."""
    available = []
    for env_var, provider_info in PROVIDER_MODELS.items():
        if os.environ.get(env_var):
            available.append({
                "env_var": env_var,
                "provider_name": provider_info["provider_name"],
                "models": provider_info["models"],
            })
    return available


def get_all_available_models():
    """Retorna todos os modelos disponíveis (nativos + providers detectados)."""
    models = list(NATIVE_MODELS)
    for provider in detect_providers():
        for m in provider["models"]:
            m_copy = dict(m)
            m_copy["provider_label"] = provider["provider_name"]
            models.append(m_copy)
    return models


def format_model_option(index, model):
    """Formata um modelo para exibição no menu."""
    provider_label = model.get("provider_label", "OpenCode")
    rec = " (recomendado)" if model.get("recommended") else ""
    return f"  [{index}] {model['name']}{rec} ({provider_label})"


def run_interactive():
    """Modo interativo: apresenta menu e permite escolha."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print()
    print("=" * 60)
    print("  🧠 EcoSystemUmGrau - LLM Selection Wizard")
    print("=" * 60)
    print()

    # Detecta provedores
    providers = detect_providers()
    print("Provedores detectados:")
    for p in providers:
        print(f"  ✓ {p['provider_name']} (via {p['env_var']})")
    if not providers:
        print("  — Apenas modelos nativos OpenCode (sem API key)")
    print()

    # Lista modelos disponíveis
    models = get_all_available_models()
    print("Modelos disponíveis:")
    for i, m in enumerate(models, 1):
        print(format_model_option(i, m))
    print()

    # Destaque modelo recomendado
    recommended = [m for m in models if m.get("recommended")]
    if recommended:
        print(f"→ Recomendado: {recommended[0]['name']}")
    print()

    # Prompt de escolha
    while True:
        try:
            choice = input(f"Escolha um modelo (1-{len(models)}) ou Enter para padrão: ").strip()
            if not choice:
                selected = models[0] if not recommended else recommended[0]
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    selected = models[idx]
                else:
                    print(f"  Digite um número entre 1 e {len(models)}")
                    continue
            break
        except (ValueError, KeyboardInterrupt):
            print()
            print("  Escolha cancelada. Usando modelo padrão.")
            selected = recommended[0] if recommended else models[0]
            break

    print()
    print(f"✓ Modelo selecionado: {selected['model']}")
    print(f"  Nome: {selected['name']}")
    print(f"  Provedor: {selected.get('provider_label', 'OpenCode')}")

    # Salva escolha
    choices_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", ".llm-choice.json"
    )
    with open(choices_file, "w", encoding="utf-8") as f:
        json.dump({"model": selected["model"], "name": selected["name"]}, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Salvo em: config/.llm-choice.json")
    print("  O setup usará este modelo ao renderizar config/opencode.jsonc")
    print()

    return selected["model"]


def run_detect_only():
    """Lista provedores sem prompt interativo."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    providers = detect_providers()
    print("Provedores detectados:")
    if providers:
        for p in providers:
            print(f"  ✓ {p['provider_name']}")
    else:
        print("  Nenhum provider com API key detectado")
        print("  Modelos nativos OpenCode disponíveis:")
        for m in NATIVE_MODELS:
            print(f"    - {m['model']}")
    return 0


def run_json():
    """Output JSON para automação."""
    result = {
        "providers_detected": [p["provider_name"] for p in detect_providers()],
        "native_models": [m["model"] for m in NATIVE_MODELS],
        "all_models": get_all_available_models(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--detect-only":
            return run_detect_only()
        elif cmd == "--json":
            return run_json()
        elif cmd == "--help":
            print("Uso: python scripts/llm-wizard.py [--detect-only|--json|--help]")
            print()
            print("  (sem args)  - modo interativo, escolhe modelo e salva em config/.llm-choice.json")
            print("  --detect-only  - lista provedores detectados")
            print("  --json  - output JSON para automação")
            return 0
        else:
            print(f"Argumento desconhecido: {cmd}")
            print("Use --help para ajuda")
            return 1

    return run_interactive() if sys.stdin.isatty() else 0


if __name__ == "__main__":
    sys.exit(main())
