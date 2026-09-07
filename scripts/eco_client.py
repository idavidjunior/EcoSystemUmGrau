"""Cliente Python embutido do EcoSystemUmGrau.

Expõe o runtime via import direto, sem subprocesso e sem mudar a UI.

Uso:
    import sys
    sys.path.insert(0, "scripts")
    from eco_client import EcoClient

    eco = EcoClient()
    print(eco.status())
    eco.checkpoint("marco")

100% stdlib. Falha suave: consultas simples nunca lançam.
Reutiliza runtime_boot, runtime_state, memory_engine, runtime_context,
runtime_kernel, runtime_auditor e maestro_client sem duplicar lógica.
Nunca executa git direto.
"""

import os
import sys
from pathlib import Path


def _resolver_base(inicio=None):
    """Sobe pelos pais até achar a raiz do ecossistema."""
    atual = Path(inicio).resolve() if inicio else Path(__file__).resolve().parent
    for cand in [atual] + list(atual.parents):
        scripts = cand / "scripts" / "runtime_state.py"
        runtime = cand / "runtime"
        conhecimento = cand / "conhecimento"
        if scripts.exists() and (runtime.exists() or conhecimento.exists()):
            return str(cand)
        if (cand / "runtime_state.py").exists():
            return str(cand.parent)
    return str(Path(__file__).resolve().parent.parent)


BASE = _resolver_base()
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def _ok(**campos):
    out = {"ok": True}
    out.update(campos)
    return out


def _falha(motivo, **campos):
    out = {"ok": False, "motivo": str(motivo)}
    out.update(campos)
    return out


class EcoClient:
    """Ponto único de acesso programático ao runtime."""

    def __init__(self, base=None):
        self.base = _resolver_base(base) if base else BASE
        scripts = os.path.join(self.base, "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)

    # -- boot e estado -------------------------------------------------

    def check(self):
        """Verifica integridade sem restaurar estado pesado."""
        try:
            import runtime_boot
            ok, detalhes = runtime_boot.check_integrity()
            return _ok(integridade=ok, detalhes=detalhes)
        except Exception as e:
            return _falha(e)

    def boot(self, memorias_limite=5):
        """Restaura estado e carrega memórias da sessão."""
        try:
            import runtime_boot
            ok, detalhes = runtime_boot.check_integrity()
            estado = runtime_boot.load_runtime_state()
            memorias, prefs = runtime_boot.load_session_context(limit=memorias_limite)
            return _ok(integridade=ok, detalhes=detalhes,
                       estado=estado, memorias=memorias, preferencias=prefs)
        except Exception as e:
            return _falha(e)

    def status(self):
        """Retorna o estado persistente atual."""
        try:
            from runtime_state import load_state
            return _ok(estado=load_state())
        except Exception as e:
            return _falha(e)

    def set_campo(self, chave, valor):
        """Atualiza projeto, objetivo, tarefa ou contexto."""
        try:
            from runtime_state import set_field
            msg = set_field(chave, valor)
            if msg.startswith("[ERR]"):
                return _falha(msg)
            return _ok(mensagem=msg)
        except Exception as e:
            return _falha(e)

    def nota(self, texto):
        """Adiciona linha ao histórico resumido."""
        try:
            from runtime_state import add_note
            return _ok(mensagem=add_note(texto))
        except Exception as e:
            return _falha(e)

    def pendencia_add(self, texto):
        """Adiciona pendência ao runtime."""
        try:
            from runtime_state import add_pending
            return _ok(mensagem=add_pending(texto))
        except Exception as e:
            return _falha(e)

    def pendencia_done(self, pid):
        """Conclui pendência pelo id."""
        try:
            from runtime_state import done_pending
            return _ok(mensagem=done_pending(int(pid)))
        except Exception as e:
            return _falha(e)

    def agente_add(self, nome):
        """Registra agente ativo."""
        try:
            from runtime_state import add_agent
            return _ok(mensagem=add_agent(nome))
        except Exception as e:
            return _falha(e)

    def agente_drop(self, nome):
        """Remove agente ativo."""
        try:
            from runtime_state import drop_agent
            return _ok(mensagem=drop_agent(nome))
        except Exception as e:
            return _falha(e)

    def checkpoint(self, rotulo="manual"):
        """Salva checkpoint do estado atual."""
        try:
            from runtime_state import save_checkpoint
            return _ok(mensagem=save_checkpoint(rotulo))
        except Exception as e:
            return _falha(e)

    # -- memória --------------------------------------------------------

    def memoria_add(self, titulo, resumo, tipo="episodio", projeto="", tags=None):
        """Grava memória com redação automática de segredos."""
        try:
            import memory_engine
            if tipo not in ("decisao", "erro", "padrao", "episodio",
                            "contexto", "preferencia"):
                return _falha("tipo inválido: %s" % tipo)
            mid = memory_engine.add_memory(titulo, resumo, kind=tipo,
                                           project=projeto or None,
                                           tags=tags or [])
            return _ok(id=mid)
        except Exception as e:
            return _falha(e)

    def memoria_buscar(self, texto="", tipo="", projeto="", limite=5):
        """Busca memórias relevantes sem carregar tudo."""
        try:
            import memory_engine
            res = memory_engine.query(project=projeto or None,
                                      kind=tipo or None,
                                      text=texto or None,
                                      limit=limite)
            return _ok(memorias=res or [])
        except Exception:
            return _ok(memorias=[])

    def memoria_contexto(self, texto="", projeto="", limite=5):
        """Retorna contexto enxuto para injeção em prompt."""
        try:
            import memory_engine
            ctx = memory_engine.get_context(project=projeto or None,
                                            text=texto or None,
                                            limit=limite)
            return _ok(contexto=ctx or "")
        except Exception:
            return _ok(contexto="")

    def memoria_stats(self):
        """Retorna sanidade do arquivo de memórias."""
        try:
            import memory_engine
            return _ok(stats=memory_engine.stats())
        except Exception as e:
            return _falha(e)

    # -- contexto, kernel, auditoria ------------------------------------

    def contexto_carregar(self, assunto, projeto="", limite=10):
        """Carrega só o contexto relevante ao assunto."""
        try:
            from runtime_context import carregar_contexto
            if not (assunto or "").strip():
                return _ok(contexto={}, vazio=True)
            ctx = carregar_contexto(assunto, projeto=projeto or None,
                                    limite=limite)
            return _ok(contexto=ctx or {})
        except Exception:
            return _ok(contexto={})

    def validar_saida(self, texto, objetivo=""):
        """Valida texto contra as regras do kernel."""
        try:
            from runtime_kernel import Kernel
            kernel = Kernel()
            res = kernel.validate_output(texto, objetivo or texto[:80])
            if isinstance(res, dict):
                return _ok(valido=res.get("ok", True), detalhes=res)
            return _ok(valido=bool(res), detalhes=res)
        except Exception as e:
            return _falha(e)

    def auditar(self, resposta, objetivo="", criticidade=None):
        """Audita resposta contra Constituição e objetivo."""
        try:
            from runtime_auditor import auditar, classificar_criticidade
            crit = criticidade or classificar_criticidade(objetivo or resposta)
            res = auditar(resposta, objetivo=objetivo, criticidade=crit)
            return _ok(auditoria=res, criticidade=crit)
        except Exception as e:
            return _falha(e)

    # -- sandbox ---------------------------------------------------------

    def sandbox_executar(self, codigo, linguagem="python", timeout=60,
                         rede=False):
        """Delega execução de código ao sandbox (Docker ou degradado)."""
        try:
            from eco_sandbox import executar
            return executar(codigo, linguagem=linguagem,
                            timeout=timeout, rede=rede)
        except Exception as e:
            return {"ok": False, "motivo": str(e), "modo": "nenhum"}

    # -- maestro --------------------------------------------------------

    def maestro(self, cmd, **kwargs):
        """Consulta o maestro com fallback degradado."""
        try:
            from maestro_client import consultar_maestro, fallback_degraded
            res = consultar_maestro(cmd, **kwargs)
            if isinstance(res, dict) and res.get("status") == "offline":
                fallback_degraded("eco_client", motivo=str(cmd))
            return _ok(resposta=res)
        except Exception as e:
            return _falha(e)


_cliente_padrao = None


def get_client(base=None):
    """Retorna singleton do cliente para o processo atual."""
    global _cliente_padrao
    if _cliente_padrao is None or base:
        _cliente_padrao = EcoClient(base=base)
    return _cliente_padrao
