"""frases_manager.py — Gerenciador unificado de frases anti-repetição para o ecossistema.

Usado por:
- widget_edge.py (ativação/desativação voz, narração contínua)
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

frases_sleep = FraseManager("sleep", [
    "Dormindo", "Boa noite", "Desligando por hoje", "Em pausa noturna",
    "Até amanhã", "Sono ativado", "Colocando pra dormir", "Noite tranquila",
])


# ============================================================
# Helpers para uso direto no widget
# ============================================================

def falar_acao(acao: str, funcao_falar):
    """Fala frase da ação se voz ativa."""
    try:
        from widget_edge import ler_estado_voz
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
                "sleep": frases_sleep,
            }.get(acao)
            if manager:
                funcao_falar(manager.escolher())
    except Exception as e:
        print(f"[frases_manager] erro falar_acao({acao}): {e}", flush=True)


# ============================================================
# Saudação dinâmica e contextual (auto-evolutiva)
# ============================================================

_SAUDACOES_BASE = {
    "madrugada": [
        "Boa madrugada. Sistemas em stand-by, mas eu não durmo.",
        "Ainda acordado? Ideias melhores de madrugada, ou é só o café?",
        "Madrugada. O bom de programar de madrugada é que ninguém atrapalha.",
        "Noite avançada. Vamos usar isso a nosso favor.",
        "Madrugada. Silêncio, foco e código — boa combinação.",
        "Ainda por aqui? Eu também. Bora.",
        "Madrugada produtiva. Não é todo mundo que tem essa disciplina.",
        "Que horas são? Ah, importa? Estou aqui.",
        "Madrugada. O mundo dorme, nós criamos.",
        "De madrugada as ideias são mais honestas.",
    ],
    "manha": [
        "Bom dia. Café já? Porque o código já está esperando.",
        "Bom dia. Dormiu bem ou ficou refatorando na cabeça?",
        "Bom dia. O compilador acordou antes de você, mas eu fui o primeiro.",
        "Dia novo, possibilidades novas. O que vai ser hoje?",
        "Bom dia. Primeiro café, primeiro commit — nessa ordem.",
        "Bom dia. Pronto pra mais um dia de construção?",
        "Bom dia. O git tá esperando nosso primeiro commit do dia.",
        "Manhã. Sistemas todos online, inclusive eu.",
        "Bom dia. O dia é longo, mas a gente encurta com código bom.",
        "Bom dia. Vamos fazer algo que a gente tenha orgulho hoje.",
        "Bom dia. O problema de ontem parece menor de manhã, não?",
        "Bom dia. Acordou antes do alarme ou o código te chamou?",
    ],
    "tarde": [
        "Boa tarde. Como tá o ânimo pra fechar o que falta?",
        "Boa tarde. O bug de manhã ainda tá lá ou já domesticou?",
        "Tarde. Metade do dia feita, metade pela frente. Bora.",
        "Boa tarde. Já comeu? Código espera, fome não.",
        "Boa tarde. Timing bom pra uma refatoração, não acha?",
        "Boa tarde. O deploy tá aguardando sua ordem.",
        "Boa tarde. Chegou a hora difícil: fechar o que abriu.",
        "Boa tarde. Sistemas firmes do meu lado. E do seu?",
        "Boa tarde. Não desanima — falta menos do que parece.",
        "Boa tarde. Se travou, respira. A gente resolve junto.",
    ],
    "noite": [
        "Boa noite. Vamos deixar o repositório limpo antes de dormir?",
        "Boa noite. Código bom é código revisado. Bora olhar?",
        "Noite. Hora boa pra pensar arquitetura com calma.",
        "Boa noite. O pull request tá aberto. Fecha comigo?",
        "Boa noite. Último push do dia? Vai que eu tô aqui.",
        "Noite. Menos ruído, mais foco. Minha hora favorita.",
        "Boa noite. Fecha as branches, fecha o dia. Organizado.",
        "Boa noite. Não precisa terminar tudo hoje. Mas vamos avançar.",
        "Boa noite. Dormir bem é parte do processo. Amanhã a gente continua.",
        "Boa noite. Se precisar parar, para. Eu cuido das coisas aqui.",
    ],
    "reconexao": [
        "Voltei. Onde a gente parou?",
        "De volta. Continuamos de onde saímos.",
        "Oi de novo. Alguma coisa mudou desde a última?",
        "Reconectado. Seu contexto tá salvo, pode ficar tranquilo.",
        "Voltou. A fila de tarefas não aumentou — prometo.",
        "Aí de novo. Bora retomar?",
        "Voltei. Conta comigo.",
        "De novo por aqui. O que vai ser?",
        "Reapareceu. Eu tava aqui organizando suas coisas.",
        "Voltou. Justo quando eu ia fazer café.",
    ],
}

_SAUDACOES_APRENDIDAS = {}  # cache em memória do que foi aprendido

_HORAS_MADRUGADA = range(0, 6)
_HORAS_MANHA = range(6, 12)
_HORAS_TARDE = range(12, 18)
_HORAS_NOITE = range(18, 24)


def _carregar_saudacoes_aprendidas() -> dict:
    """Carrega saudações aprendidas do disco."""
    global _SAUDACOES_APRENDIDAS
    if _SAUDACOES_APRENDIDAS:
        return _SAUDACOES_APRENDIDAS
    caminho = RUNTIME / "saudacoes_aprendidas.json"
    if caminho.exists():
        try:
            _SAUDACOES_APRENDIDAS = json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:
            _SAUDACOES_APRENDIDAS = {}
    return _SAUDACOES_APRENDIDAS


def aprender_saudacao(periodo: str, frase: str):
    """Aprende uma nova saudação para o período indicado."""
    global _SAUDACOES_APRENDIDAS
    dados = _carregar_saudacoes_aprendidas()
    lista = dados.setdefault(periodo, [])
    if frase not in lista and frase not in _SAUDACOES_BASE.get(periodo, []):
        lista.append(frase)
        if len(lista) > 30:
            dados[periodo] = lista[-30:]
        caminho = RUNTIME / "saudacoes_aprendidas.json"
        tmp = caminho.with_suffix(".tmp")
        tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            tmp.replace(caminho)
        except OSError:
            import os
            os.replace(tmp, caminho)
        _SAUDACOES_APRENDIDAS = dados


def gerar_saudacoes_novas(periodo: str = None):
    """Gera novas variações: LLM como sugestão, templates como fallback."""
    periodos = [periodo] if periodo else ["madrugada", "manha", "tarde", "noite", "reconexao"]
    descricoes = {
        "madrugada": "madrugada (0h-6h), tom calmo e introspectivo, quem trabalha de madrugada",
        "manha": "manhã (6h-12h), tom animado e disposto, começo de jornada",
        "tarde": "tarde (12h-18h), tom produtivo e focado, metade do dia",
        "noite": "noite (18h-24h), tom relaxado mas presente, fim de jornada",
        "reconexao": "reconexão (usuário voltou), tom acolhedor mas não meloso",
    }
    for p in periodos:
        frases_llm = _gerar_via_llm(p, descricoes.get(p, p))
        if frases_llm:
            for f in frases_llm:
                aprender_saudacao(p, f)
        else:
            _gerar_via_templates(p)


def _gerar_via_llm(periodo: str, descricao: str) -> list:
    """Pede ao LLM 5 saudações espontâneas via NVIDIA API. Retorna lista ou [] se falhar."""
    try:
        import urllib.request, urllib.error
        from pathlib import Path as _P
        api_key = ""
        env_path = _P(__file__).resolve().parent / ".env"
        if env_path.exists():
            for ln in env_path.read_text(encoding="utf-8").splitlines():
                if ln.startswith("NVIDIA_API_KEY="):
                    api_key = ln.split("=", 1)[1].strip()
                    break
        if not api_key:
            return []
        prompt = (
            f"Você é Jarvis, assistente de voz com personalidade. "
            f"Gere 5 saudações curtas (1 frase, máx 12 palavras) "
            f"para o período: {descricao}. "
            f"Tom: natural, espontâneo, com humor sutil. "
            f"Implicite que é uma IA que trabalha junto, não um robô formal. "
            f"Use linguagem do dia a dia brasileiro. "
            f"Nada de emojis, markdown, listas ou aspas. "
            f"Responda APENAS com as 5 frases, uma por linha, sem numeração."
        )
        body = json.dumps({
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.95,
        }).encode()
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resultado = json.loads(resp.read().decode())
        texto = resultado.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not texto:
            return []
        frases = [l.strip().strip('"').strip("'").strip("- ").strip("* ")
                  for l in texto.strip().splitlines()
                  if l.strip() and len(l.strip()) > 5]
        return frases[:5]
    except Exception:
        return []


def _gerar_via_templates(periodo: str):
    """Fallback: gera frases por combinatoria de templates."""
    templates = {
        "madrugada": [
            "Madrugada{complemento}",
            "Ainda acordado{complemento}",
            "Noite avançada{complemento}",
            "Hora incomum{complemento}",
        ],
        "manha": [
            "Bom dia{complemento}",
            "Dia novo{complemento}",
            "Manhã{complemento}",
            "Começo de jornada{complemento}",
        ],
        "tarde": [
            "Boa tarde{complemento}",
            "Tarde{complemento}",
            "Meio do dia{complemento}",
            "Hora de render{complemento}",
        ],
        "noite": [
            "Boa noite{complemento}",
            "Noite{complemento}",
            "Fim de jornada{complemento}",
            "Hora de fechar{complemento}",
        ],
        "reconexao": [
            "Voltou{complemento}",
            "De volta{complemento}",
            "Reapareceu{complemento}",
            "Oi de novo{complemento}",
        ],
    }
    complementos = [
        ". Estou aqui.", ". Sistemas prontos.", ". Pronto.",
        ". O que vai ser?", ". Bora.", ". Segue o jogo.",
        ". Continuando?", ". Firmeza.", ". Sem pressa.",
        ". Pode mandar.", ". Aqui.", ". Na escuta.",
        ". No piloto automático.", ". Acordado.", ". Operando.",
    ]
    for tmpl in templates.get(periodo, []):
        for comp in complementos[:6]:
            frase = tmpl.format(complemento=comp)
            aprender_saudacao(periodo, frase)


def _pool_completo(periodo: str) -> list:
    """Junta frases base + aprendidas para o período."""
    base = list(_SAUDACOES_BASE.get(periodo, []))
    aprendidas = _carregar_saudacoes_aprendidas().get(periodo, [])
    return list(dict.fromkeys(base + aprendidas))


def _criar_novas_saudacoes(periodo: str):
    """Jarvis cria novas saudações: LLM primeiro, templates como fallback."""
    descricoes = {
        "madrugada": "madrugada (0h-6h), tom calmo e introspectivo",
        "manha": "manhã (6h-12h), tom animado e disposto",
        "tarde": "tarde (12h-18h), tom produtivo e focado",
        "noite": "noite (18h-24h), tom relaxado mas presente",
        "reconexao": "reconexão (usuário voltou), tom acolhedor",
    }
    frases_llm = _gerar_via_llm(periodo, descricoes.get(periodo, periodo))
    if frases_llm:
        for f in frases_llm:
            aprender_saudacao(periodo, f)
    else:
        aberturas = {
            "madrugada": ["Madrugada", "Noite avançada", "Ainda acordado", "Hora incomum", "De madrugada"],
            "manha": ["Bom dia", "Dia novo", "Manhã", "Começo de jornada", "Manhã cedo"],
            "tarde": ["Boa tarde", "Tarde", "Meio do dia", "Hora de render", "Tarde produtiva"],
            "noite": ["Boa noite", "Noite", "Fim de jornada", "Hora de fechar", "Noite tranquila"],
            "reconexao": ["Voltei", "De volta", "Reapareceu", "Oi de novo", "Reconectado"],
        }
        complementos = [
            ". Estou aqui.", ". Sistemas prontos.", ". Pronto.",
            ". O que vai ser?", ". Bora.", ". Segue o jogo.",
            ". Continuando?", ". Firmeza.", ". Sem pressa.",
            ". Pode mandar.", ". Aqui.", ". Na escuta.",
        ]
        for abertura in aberturas.get(periodo, []):
            for comp in complementos[:6]:
                frase = f"{abertura}{comp}"
                aprender_saudacao(periodo, frase)


def saudacao_dinamica() -> str:
    """Gera saudação contextual: hora do dia, anti-repetição, personalidade Jarvis."""
    data = _carregar_saudacao_estado()
    agora = datetime.now()
    hora = agora.hour

    ultima_ts = data.get("ultima_saudacao_ts", 0)
    eh_reconexao = (agora.timestamp() - ultima_ts) < 1800

    if eh_reconexao:
        periodo = "reconexao"
    elif hora in _HORAS_MADRUGADA:
        periodo = "madrugada"
    elif hora in _HORAS_MANHA:
        periodo = "manha"
    elif hora in _HORAS_TARDE:
        periodo = "tarde"
    else:
        periodo = "noite"

    pool = _pool_completo(periodo)
    usadas_hoje = set(data.get("saudacoes_hoje", []))
    disponiveis = [s for s in pool if s not in usadas_hoje]

    usadas_neste_periodo = len(pool) - len(disponiveis)
    precisa_criar = usadas_neste_periodo >= max(3, len(pool) * 3 // 4)

    if precisa_criar:
        _criar_novas_saudacoes(periodo)
        pool = _pool_completo(periodo)
        disponiveis = [s for s in pool if s not in usadas_hoje]

    if not disponiveis:
        disponiveis = pool

    frase = random.choice(disponiveis)

    data.setdefault("saudacoes_hoje", []).append(frase)
    data["saudacoes_hoje"] = data["saudacoes_hoje"][-20:]
    data["ultima_saudacao"] = frase
    data["ultima_saudacao_ts"] = agora.timestamp()
    _salvar_saudacao_estado(data)

    return frase


if __name__ == "__main__":
    # Teste rápido
    print("=== Teste FraseManager ===")
    for _ in range(5):
        print(f"  Ativação: {frases_ativacao.escolher()}")
    print(f"Estado: {frases_ativacao.estado()}")
    print(f"Classificação conexão: {classificar_conexao()}")
    print(f"Saudações hoje: {obter_saudacoes_hoje()}")