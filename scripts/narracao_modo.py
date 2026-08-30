"""narracao_modo.py — modos de escuta da narração (padrão heardlabs/heard).

Três modos que modulam o que o narrador fala, escolhidos pelo usuário:

  copilot   (default) — na tela, codando: sinais curtos e marcos. O filtro de
                        relevância atual (narra só eventos relevantes).
  companion            — olhos fora da tela (dirigindo, cozinhando, andando):
                        mais permissivo, vira um briefing contínuo.
  focus                — só alertas: conclusões, erros, decisões e bloqueios.
                        Conteúdo comum de rotina fica em silêncio.

Estado persistido em runtime/narracao_modo.json (escrita atômica). Qualquer
script/agente consulta via get_modo() e altera via set_modo().

Uso CLI:
  python scripts/narracao_modo.py            # mostra o modo atual
  python scripts/narracao_modo.py copilot    # troca para copilot
  python scripts/narracao_modo.py companion
  python scripts/narracao_modo.py focus
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODO_FILE = ROOT / "runtime" / "narracao_modo.json"

MODOS = ("copilot", "companion", "focus")
DEFAULT = "copilot"

# Motivos de relevância (retornados por widget_edge._deve_narrar) permitidos
# em cada modo. Um motivo ausente = silenciado naquele modo.
RELEVANCIA_POR_MODO = {
    "copilot": {
        "conclusao", "erro", "decisao", "alerta", "sucesso", "bloqueio",
        "resumo", "comando",
    },
    "companion": {
        "conclusao", "erro", "decisao", "alerta", "sucesso", "bloqueio",
        "resumo", "comando", "progresso", "conversa", "sem relevancia",
    },
    "focus": {
        "conclusao", "erro", "decisao", "alerta", "bloqueio",
    },
}


def _ler() -> dict:
    try:
        if MODO_FILE.exists():
            data = json.loads(MODO_FILE.read_text(encoding="utf-8"))
            if data.get("modo") in MODOS:
                return data
    except Exception:
        pass
    return {"modo": DEFAULT}


def _salvar(data: dict):
    try:
        MODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = MODO_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(MODO_FILE)
    except Exception:
        pass


def get_modo() -> str:
    """Devolve o modo de escuta atual (sempre um dos três válidos)."""
    return _ler().get("modo", DEFAULT)


def set_modo(modo: str) -> bool:
    """Define o modo de escuta. Devolve True se aceito."""
    modo = (modo or "").strip().lower()
    if modo not in MODOS:
        return False
    _salvar({"modo": modo})
    return True


def permite_relevancia(motivo: str) -> bool:
    """True se o motivo de relevância deve ser narrado no modo atual."""
    modo = get_modo()
    permitidos = RELEVANCIA_POR_MODO.get(modo, RELEVANCIA_POR_MODO[DEFAULT])
    return (motivo or "") in permitidos


def descricao_modo(modo: str) -> str:
    desc = {
        "copilot": "na tela, codando: sinais curtos e marcos, só eventos relevantes",
        "companion": "olhos fora da tela: briefings completos do que está acontecendo",
        "focus": "só alertas: conclusões, erros, decisões e bloqueios; o resto silencia",
    }
    return desc.get(modo, "")


def main():
    if len(sys.argv) < 2:
        modo = get_modo()
        print(f"Modo de escuta: {modo}")
        print(descricao_modo(modo))
        return 0
    alvo = sys.argv[1]
    if set_modo(alvo):
        print(f"Modo de escuta alterado para: {alvo}")
        print(descricao_modo(alvo))
        return 0
    print(f"Modo inválido: {alvo}. Use um de: {', '.join(MODOS)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())