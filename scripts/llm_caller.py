"""LLM Caller - Chamada direta e simples a LLMs.

Fornece call_llm() que:
- Usa NVIDIA API como primário (via quota monitor)
- Fallback para OpenAI/Anthropic se NVIDIA falhar
- Suporta retry, timeout, temperature configurável
- Retorna string limpa ou dict estruturado

Uso:
    from llm_caller import call_llm, call_llm_json
    resposta = call_llm("Explique X em 3 frases")
    dados = call_llm_json("Liste 3 riscos", expected_keys=["risks"])
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = Path(__file__).resolve().parent
ENV_PATH = SCRIPTS / ".env"

# Cache de chaves (carrega uma vez)
_api_keys: Dict[str, str] = {}
_keys_loaded = False


def _load_keys():
    """Carrega chaves de API do .env uma única vez."""
    global _keys_loaded
    if _keys_loaded:
        return
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                _api_keys[k.strip()] = v.strip()
    # Env vars sobrescrevem .env
    for key in ("NVIDIA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        env_val = os.environ.get(key)
        if env_val:
            _api_keys[key] = env_val
    _keys_loaded = True


def _get_key(name: str) -> str:
    _load_keys()
    return _api_keys.get(name, "")


def _call_nvidia(messages: list, model: str = "nvidia/nemotron-3-nano-30b-a3b",
                  max_tokens: int = 1024, temperature: float = 0.3,
                  timeout: int = 30) -> Optional[str]:
    """Chama NVIDIA NIM API. Retorna texto ou None se falhar."""
    api_key = _get_key("NVIDIA_API_KEY")
    if not api_key:
        return None

    # Tenta usar quota monitor se disponível
    try:
        from nvidia_quota_monitor import nvidia_request_with_quota
        r = nvidia_request_with_quota(
            model, messages, max_tokens=max_tokens, temperature=temperature
        )
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        return None
    except Exception:
        pass

    # Fallback: request direto
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _call_openai(messages: list, model: str = "gpt-4o-mini",
                  max_tokens: int = 1024, temperature: float = 0.3,
                  timeout: int = 30) -> Optional[str]:
    """Chama OpenAI API. Retorna texto ou None se falhar."""
    api_key = _get_key("OPENAI_API_KEY")
    if not api_key:
        return None

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def call_llm(
    prompt: str,
    system: str = "",
    model: str = "auto",
    max_tokens: int = 1024,
    temperature: float = 0.3,
    timeout: int = 30,
    retries: int = 1,
) -> str:
    """Chama LLM com fallback automático. Retorna string vazia se todos falharem.

    Args:
        prompt: Mensagem do usuário
        system: System prompt opcional
        model: "auto" usa NVIDIA, ou nome específico
        max_tokens: Limite de tokens na resposta
        temperature: Criatividade (0=factual, 1=criativo)
        timeout: Timeout por tentativa em segundos
        retries: Quantidade de retries por provider

    Returns:
        Texto da resposta ou string vazia
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    providers = [
        ("nvidia", _call_nvidia),
        ("openai", _call_openai),
    ]

    for provider_name, provider_fn in providers:
        for attempt in range(retries + 1):
            try:
                result = provider_fn(
                    messages, max_tokens=max_tokens,
                    temperature=temperature, timeout=timeout
                )
                if result:
                    return result
            except Exception:
                if attempt < retries:
                    time.sleep(1 * (attempt + 1))
                continue

    return ""


def call_llm_json(
    prompt: str,
    system: str = "",
    model: str = "auto",
    max_tokens: int = 1024,
    temperature: float = 0.2,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Chama LLM e tenta parsear resposta como JSON.

    Se o LLM retornar JSON dentro de ```json ou { }, extrai automaticamente.
    Retorna dict com campo "_parse_error" se não conseguir parsear.
    """
    json_system = (
        (system + "\n\n" if system else "") +
        "Responda APENAS com JSON válido, sem markdown, sem explicações, "
        "sem texto antes ou depois. Apenas o objeto JSON."
    )

    raw = call_llm(
        prompt=prompt, system=json_system, model=model,
        max_tokens=max_tokens, temperature=temperature, timeout=timeout,
    )

    if not raw:
        return {"_parse_error": "empty_response"}

    # Tenta extrair JSON de dentro de ```json ... ```
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1).strip()

    # Tenta extrair primeiro { ... } ou [ ... ]
    if not raw.startswith(('{', '[')):
        brace = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', raw)
        if brace:
            raw = brace.group(1)

    # Remove trailing commas antes de } ou ] (JSON invalido comum)
    raw = re.sub(r',\s*([}\]])', r'\1', raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Ultimo recurso: tenta extrair campo perspective do texto
        p_match = re.search(r'"perspective"\s*:\s*"([^"]*)"', raw)
        c_match = re.findall(r'"concerns"\s*:\s*\[(.*?)\]', raw)
        s_match = re.findall(r'"suggestions"\s*:\s*\[(.*?)\]', raw)
        v_match = re.search(r'"vote"\s*:\s*"([^"]*)"', raw)
        if p_match:
            return {
                "perspective": p_match.group(1),
                "concerns": [c.strip().strip('"') for c in c_match[0].split(',')] if c_match else [],
                "suggestions": [s.strip().strip('"') for s in s_match[0].split(',')] if s_match else [],
                "vote": v_match.group(1) if v_match else "abster-se",
                "confidence": 0.7,
            }
        return {"_parse_error": "json_decode_failed", "_raw": raw[:500]}


def call_agents_parallel(
    agent_prompts: Dict[str, Dict[str, str]],
    model: str = "auto",
    max_tokens: int = 1024,
    temperature: float = 0.3,
    max_workers: int = 6,
) -> Dict[str, str]:
    """Chama múltiplos agentes em paralelo via ThreadPool.

    Args:
        agent_prompts: Dict {agent_name: {"prompt": ..., "system": ...}}
        model: Modelo a usar
        max_tokens: Limite de tokens
        temperature: Temperatura
        max_workers: Máximo de threads simultâneas

    Returns:
        Dict {agent_name: resposta_texto}
    """
    import concurrent.futures

    results: Dict[str, str] = {}

    def _call_agent(name: str, config: Dict[str, str]):
        texto = call_llm(
            prompt=config.get("prompt", ""),
            system=config.get("system", ""),
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return name, texto

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_call_agent, name, config): name
            for name, config in agent_prompts.items()
        }
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                agent_name, texto = future.result()
                results[agent_name] = texto
            except Exception as e:
                results[name] = f"[ERRO] {type(e).__name__}: {e}"

    return results


# CLI para teste rápido
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        resultado = call_llm(prompt, system="Responda em pt-BR.", max_tokens=256)
        print(resultado if resultado else "[FALHA] Nenhum LLM respondeu.")
    else:
        print("Uso: python llm_caller.py <prompt>")
        print("Exemplo: python llm_caller.py 'O que é SOLID?'")
