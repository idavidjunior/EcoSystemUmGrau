"""frases_manager.py — Gerenciador unificado de frases anti-repetição para o ecossistema.

Usado por:
- widget_controle_jarvis.py (ativação/desativação voz, mic, ações UI)
- jarvis_bridge.py (saudações de reconexão vs primeira vez)

Padrão: uma frase por ação, não repete no dia, aprende novas, persiste em JSON.
"""
import json
import random
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
RUNTIME = ROOT / "runtime"

# ============================================================
# Estado compartilhado de saudações (bridge + widget)
# ============================================================

SAUDACAO_ESTADO = SCRIPTS_DIR / "saudacao_estado.json"


def _carregar_saudacao_estado() -> dict:
    """Carrega estado unificado de saudações."""
    if not SAUDACAO_ESTADO.exists():
        return {"conexoes": 0, "hoje": "", "saudacoes_hoje": [], "ultima_saudacao": "", "ultima_saudacao_ts": 0, "ultima_atividade_ts": 0}
    try:
        d = json.loads(SAUDACAO_ESTADO.read_text(encoding="utf-8"))
        hoje = datetime.now().strftime("%Y-%m-%d")
        if d.get("hoje") != hoje:
            d["hoje"] = hoje
            d["saudacoes_hoje"] = []
        return d
    except Exception:
        return {"conexoes": 0, "hoje": datetime.now().strftime("%Y-%m-%d"), "saudacoes_hoje": [], "ultima_saudacao": "", "ultima_saudacao_ts": 0, "ultima_atividade_ts": 0}


def _salvar_saudacao_estado(data: dict):
    """Salva estado atômico."""
    tmp = SAUDACAO_ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(SAUDACAO_ESTADO)
    except OSError:
        import os
        os.replace(tmp, SAUDACAO_ESTADO)


def registrar_saudacao(texto: str):
    """Registra saudação usada (para anti-repetição compartilhada)."""
    data = _carregar_saudacao_estado()
    data["conexoes"] = data.get("conexoes", 0) + 1
    data["saudacoes_hoje"].append(texto[:200])
    if len(data["saudacoes_hoje"]) > 20:
        data["saudacoes_hoje"] = data["saudacoes_hoje"][-20:]
    data["ultima_saudacao"] = texto[:200]
    data["ultima_saudacao_ts"] = time.time()
    _salvar_saudacao_estado(data)


def obter_saudacoes_hoje() -> list:
    """Retorna saudações já usadas hoje (para evitar repetição)."""
    return _carregar_saudacao_estado().get("saudacoes_hoje", [])


def marcar_atividade():
    """Atualiza timestamp de última atividade (para detectar reconexão)."""
    data = _carregar_saudacao_estado()
    data["ultima_atividade_ts"] = time.time()
    _salvar_saudacao_estado(data)


def classificar_conexao() -> str:
    """Classifica: 'primeira_vez' ou 'reconexao' baseado em 3 fontes."""
    data = _carregar_saudacao_estado()
    # 1. Já saudou hoje?
    if data.get("saudacoes_hoje"):
        return "reconexao"
    # 2. Atividade recente (últimos 30 min)?
    if data.get("ultima_atividade_ts", 0) > time.time() - 1800:
        return "reconexao"
    # 3. Arquivo de conversa recente?
    try:
        conv = ROOT / "conversa_unica.json"
        if conv.exists() and conv.stat().st_mtime > time.time() - 1800:
            return "reconexao"
    except Exception:
        pass
    return "primeira_vez"


# ============================================================
# Gerenciador genérico de frases por ação
# ============================================================

class FraseManager:
    """Gerencia frases variadas para uma ação específica."""
    
    def __init__(self, acao: str, base: list, max_historico: int = 50, max_hoje: int = 20):
        self.acao = acao
        self.base = base
        self.max_historico = max_historico
        self.max_hoje = max_hoje
        self.arquivo = RUNTIME / f"frases_{acao}.json"
    
    def _carregar(self) -> dict:
        if not self.arquivo.exists():
            return {"usadas_hoje": [], "historico": [], "ultima_data": ""}
        try:
            d = json.loads(self.arquivo.read_text(encoding="utf-8"))
            hoje = datetime.now().strftime("%Y-%m-%d")
            if d.get("ultima_data") != hoje:
                d["usadas_hoje"] = []
                d["ultima_data"] = hoje
            return d
        except Exception:
            return {"usadas_hoje": [], "historico": [], "ultima_data": datetime.now().strftime("%Y-%m-%d")}
    
    def _salvar(self, data: dict):
        tmp = self.arquivo.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        try:
            tmp.replace(self.arquivo)
        except OSError:
            import os
            os.replace(tmp, self.arquivo)
    
    def escolher(self) -> str:
        """Escolhe frase variada, não repete no dia."""
        data = self._carregar()
        hoje = datetime.now().strftime("%Y-%m-%d")
        usadas = set(data.get("usadas_hoje", []))
        historico = data.get("historico", [])
        todas = list(dict.fromkeys(self.base + historico))
        disponiveis = [f for f in todas if f not in usadas]
        if not disponiveis:
            usadas.clear()
            disponiveis = todas
        frase = random.choice(disponiveis)
        usadas.add(frase)
        data["usadas_hoje"] = list(usadas)[-self.max_hoje:]
        self._salvar(data)
        return frase
    
    def aprender(self, nova: str):
        """Adiciona nova frase ao histórico."""
        data = self._carregar()
        historico = data.get("historico", [])
        if nova not in historico and nova not in self.base:
            historico.append(nova)
            if len(historico) > self.max_historico:
                historico = historico[-self.max_historico:]
            data["historico"] = historico
            self._salvar(data)
    
    def estado(self) -> dict:
        """Retorna estado atual (para debug)."""
        return self._carregar()


# ============================================================
# Instâncias pré-configuradas para o widget
# ============================================================

frases_ativacao = FraseManager("ativacao", [
    "Voz ativada", "Voltei", "Online", "Na escuta",
    "Sistemas ativos", "Pronto", "Operante", "Conectado",
])

frases_desativacao = FraseManager("desativacao", [
    "Voz desativada", "Pausado", "Até logo", "Desconectado",
    "Encerrado", "Standby", "Silêncio", "Offline",
])

frases_mic_on = FraseManager("mic_on", [
    "Microfone ligado", "Escutando", "Microfone ativo", "Pode falar",
])

frases_mic_off = FraseManager("mic_off", [
    "Microfone desligado", "Microfone off", "Silêncio", "Desconectado",
])

frases_interromper = FraseManager("interromper", [
    "Interrompido", "Parado", "Cortado", "Ok, parei",
])

frases_minimizar = FraseManager("minimizar", [
    "Minimizado", "Escondido", "Sumido", "Guardado",
])

frases_topo = FraseManager("topo", [
    "Fixado no topo", "Sempre visível", "Topo ativado", "Acima de tudo",
])

frases_tras = FraseManager("tras", [
    "Enviado para trás", "Atrás das janelas", "Fundo", "Desfixado",
])


# ============================================================
# Helpers para uso direto no widget
# ============================================================

def falar_acao(acao: str, funcao_falar):
    """Fala frase da ação se voz ativa."""
    try:
        from widget_controle_jarvis import ler_estado_voz
        at, pa = ler_estado_voz()
        if at and not pa:
            manager = {
                "ativacao": frases_ativacao,
                "desativacao": frases_desativacao,
                "mic_on": frases_mic_on,
                "mic_off": frases_mic_off,
                "interromper": frases_interromper,
                "minimizar": frases_minimizar,
                "topo": frases_topo,
                "tras": frases_tras,
            }.get(acao)
            if manager:
                funcao_falar(manager.escolher())
    except Exception as e:
        print(f"[frases_manager] erro falar_acao({acao}): {e}", flush=True)


if __name__ == "__main__":
    # Teste rápido
    print("=== Teste FraseManager ===")
    for _ in range(5):
        print(f"  Ativação: {frases_ativacao.escolher()}")
    print(f"Estado: {frases_ativacao.estado()}")
    print(f"Classificação conexão: {classificar_conexao()}")
    print(f"Saudações hoje: {obter_saudacoes_hoje()}")