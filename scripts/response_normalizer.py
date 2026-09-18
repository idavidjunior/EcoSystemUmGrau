#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""response_normalizer.py — Camada final de normalização de resposta (SPEC 1.0).

Orquestra as peças existentes (não duplica) e adiciona as etapas que faltam:

Reuso (import direto, nunca subprocess duplicado):
  - validar_idioma.calcular_score_pt          -> padrão linguístico pt-BR
  - validar_resposta.validar_e_corrigir       -> gate pt-BR + correção
  - validar_bajulacao.detectar_bajulacao      -> antibajulação

Etapas próprias:
  - INTENT DETECTION (detecção de intenção do usuário)
  - TASK CLASSIFICATION (classificação da tarefa)
  - tipo de interação (pergunta, implementação, erro, investigação, ...)
  - complexidade (tamanho + frases longas)
  - estrutura adaptativa (resumo -> entendimento -> técnico)
  - remoção de redundância (frases repetidas, espaços duplos)
  - estados de evidência (CONFIRMADO / PROVÁVEL / HIPÓTESE / NÃO VERIFICADO)
  - verificação de transparência (marcadores de incerteza)
  - FACT & STATE VALIDATION (validação de fatos e estados)
  - UNCERTAINTY DETECTION (detecção sistemática de incerteza)
  - LANGUAGE SIMPLIFICATION (simplificação de linguagem ativa)
  - TRUTHFULNESS CHECK (verificação de veracidade)
  - CHECKLIST FINAL (verificação sistemática antes da entrega)

Uso:
  python scripts/response_normalizer.py "texto"
  echo "texto" | python scripts/response_normalizer.py --stdin
  python scripts/response_normalizer.py --json '{"texto": "...", "tipo": "erro"}'

Saída JSON: {ok, texto, score_pt, tipo, complexidade, estrutura, acoes, checklist, ...}
Exit: 0 = normalizado/ok, 1 = houve correção aplicada, 2 = erro
"""
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validar_idioma import calcular_score_pt  # noqa: E402
from validar_resposta import validar_e_corrigir  # noqa: E402
from validar_bajulacao import detectar_bajulacao  # noqa: E402

# Marcadores de evidência reconhecidos (SPEC 3.1)
EVIDENCIA = ("CONFIRMADO", "PROVÁVEL", "HIPÓTESE", "NÃO VERIFICADO",
             "FALHOU", "INCOMPLETO", "IMPLEMENTADO", "TESTADO", "VALIDADO",
             "PRODUÇÃO", "PLANEJADO", "EM EXECUÇÃO", "CONCLUÍDO", "PARCIAL",
             "BLOQUEADO", "PENDENTE", "CANCELADO")

# Palavras de incerteza que indicam hipótese/pendência de verificação
INCERTEZA = re.compile(
    r'\b(?:provavelmente|possivelmente|talvez|aparentemente|possivelmente|'
    r'nao confirmad[oa]|ainda nao|hipotese|suspeito que|acho que|pode ser|'
    r'pode ter|nao verificad[oa]|precisamos testar|sem dados suficientes|'
    r'precisa (?:de )?validac|precisa (?:de )?teste|impera que)\b',
    re.IGNORECASE,
)

# Padrões de início que indicam o tipo da interação
TIPO_PADROES = [
    ("erro", re.compile(r'\b(erro|falhou|falha|crash|exception|quebrou|bug)\b', re.IGNORECASE)),
    ("implementacao", re.compile(r'\b(implement|criei|criado|alterei|alterado|escrevi|adicionei|refatorei|colei|construi)\b', re.IGNORECASE)),
    ("atualizacao", re.compile(r'\b(atualizei|atualizado|mudei|mudou|atualizacao|versao|upgrade)\b', re.IGNORECASE)),
    ("investigacao", re.compile(r'\b(investigu|investigando|diagnostic|analisei|estou analisando|evidencias|procurando causa)\b', re.IGNORECASE)),
    ("decisao", re.compile(r'\b(decidi|decisao|escolhi|optei|trade-off|arquitetura)\b', re.IGNORECASE)),
    ("pergunta", re.compile(r'\?$', re.MULTILINE)),
]

# Redundância estrutural (frases enchimento da IA, preâmbulos vazios)
PREAMBULOS = re.compile(
    r'^\s*(claro!|claro|com certeza!?|certo!?|vamos lá|ok!?|perfeito!?|'
    r'vou ajudar|deixa eu ver|deixa eu analisar|deixa eu pensar|'
    r'excelente conhecimento|ótima pergunta|boa pergunta|'
    r'entendi|entendido|anotado|sem problemas)\s*[.!]?\s*$',
    re.IGNORECASE,
)

# Preâmbulo artificial no início da frase (só enchimentos pontuados, em cadeia)
INICIO_ARTIFICIAL = re.compile(
    r'^\s*(?:claro!|claro\.|claro que sim!?|com certeza!?|certo!|certo\.|'
    r'perfeito!|vou te ajudar!|vou ajudar!|deixa eu ver!|deixa eu analisar!|'
    r'deixa eu pensar!|ok!|ok\.|sem problemas!|vamos lá!|vamos logo!)\s*',
    re.IGNORECASE,
)

# Padrões de intenção do usuário (INTENT DETECTION)
INTENT_PADROES = [
    ("informacao", re.compile(r'\b(como|o que|onde|quando|por que|qual|quem|explique|descreva|mostre)\b', re.IGNORECASE)),
    ("acao", re.compile(r'\b(faca|crie|execute|rode|instale|configure|altere|modifique|delete|remova)\b', re.IGNORECASE)),
    ("diagnostico", re.compile(r'\b(diagnosticar|investigar|debug|erro|problema|falha|quebrou|nao funciona)\b', re.IGNORECASE)),
    ("decisao", re.compile(r'\b(decidir|escolher|optar|recomendar|melhor|comparar)\b', re.IGNORECASE)),
    ("validacao", re.compile(r'\b(testar|validar|verificar|confirmar|checar|revisar)\b', re.IGNORECASE)),
]

# Classificação de tarefa (TASK CLASSIFICATION)
TAREFA_PADROES = [
    ("micro", re.compile(r'\b(corrigir|ajustar|pequeno|simples|rapido)\b', re.IGNORECASE)),
    ("pequena", re.compile(r'\b(funcao|metodo|classe|arquivo|integracao)\b', re.IGNORECASE)),
    ("media", re.compile(r'\b(recurso|modulo|feature|alteracao|refatoracao)\b', re.IGNORECASE)),
    ("grande", re.compile(r'\b(subsistema|arquitetura|banco de dados|autenticacao|comunicacao|migracao)\b', re.IGNORECASE)),
    ("critica", re.compile(r'\b(seguranca|dados sensíveis|pagamento|autenticacao|autorizacao|infraestrutura|irreversivel|destrutivo)\b', re.IGNORECASE)),
]

# Marcadores de afirmação vs hipótese (FACT & STATE VALIDATION)
FATO_INDICADORES = re.compile(
    r'\b(confirmei|verifiquei|testei|executei|funciona|esta funcionando|foi criado|foi alterado|'
    r'implementado|validado|concluido|finalizado|pronto|sucesso)\b',
    re.IGNORECASE,
)

HIPOSE_INDICADORES = re.compile(
    r'\b(provavelmente|talvez|possivelmente|deve ser|deveria|parece|aparenta|'
    r'acho que|suspeito|hipotese|teoria|especulacao)\b',
    re.IGNORECASE,
)

# Termos técnicos que precisam de explicação (LANGUAGE SIMPLIFICATION)
TERMOS_TECNICOS = {
    "api": "interface de programação",
    "endpoint": "ponto de acesso",
    "deployment": "implantação",
    "commit": "versão salva",
    "merge": "junção de código",
    "pull request": "solicitação de alteração",
    "branch": "ramo de trabalho",
    "docker": "ambiente virtual",
    "container": "recipiente virtual",
    "pipeline": "fluxo automático",
    "build": "construção",
    "runtime": "tempo de execução",
    "framework": "estrutura de trabalho",
    "middleware": "camada intermediária",
    "cache": "armazenamento temporário",
    "callback": "função de retorno",
    "async": "assíncrono",
    "sync": "síncrono",
}

# Marcadores de falsidade potencial (TRUTHFULNESS CHECK)
FALSIDADE_INDICADORES = re.compile(
    r'\b(sempre|nunca|todos|ninguem|jamais|absolutamente|garantidamente|'
    r'sem falhas|perfeito|impossivel falhar)\b',
    re.IGNORECASE,
)


def detectar_intencao(texto: str) -> str:
    """Detecta a intenção do usuário (INTENT DETECTION)."""
    if not texto or not texto.strip():
        return "desconhecido"
    for intent, padrao in INTENT_PADROES:
        if padrao.search(texto):
            return intent
    return "geral"


def classificar_tarefa(texto: str) -> str:
    """Classifica a complexidade/risco da tarefa (TASK CLASSIFICATION)."""
    if not texto or not texto.strip():
        return "desconhecido"
    for classe, padrao in TAREFA_PADROES:
        if padrao.search(texto):
            return classe
    return "media"


def detectar_tipo(texto: str) -> str:
    """Infere o tipo da interação por heurísticas simples."""
    if not texto or not texto.strip():
        return "desconhecido"
    for tipo, padrao in TIPO_PADROES:
        if padrao.search(texto):
            return tipo
    return "comunicacao"


def medir_complexidade(texto: str) -> dict:
    """Mede tamanho e proporção de frases longas (SPEC 6)."""
    if not texto or not texto.strip():
        return {"nivel": "simples", "palavras": 0, "frases": 0, "frases_longas": 0, "frase_media": 0}
    palavras = re.findall(r"\S+", texto)
    frases = [f for f in re.split(r"[.!?]+", texto) if f.strip()]
    longas = sum(1 for f in frases if len(f.split()) > 30)
    media = round(len(palavras) / len(frases), 1) if frases else 0
    if len(palavras) < 40 and media <= 15:
        nivel = "simples"
    elif len(palavras) < 150 and media <= 20:
        nivel = "media"
    else:
        nivel = "complexa"
    return {"nivel": nivel, "palavras": len(palavras), "frases": len(frases),
            "frases_longas": longas, "frase_media": media}


def remover_redundancia(texto: str) -> tuple:
    """Remove repetições mecânicas e preâmbulos vazios (SPEC 10.1 passo 8)."""
    if not texto:
        return texto, []
    acoes = []
    # Remove linhas úteis de preâmbulo ('Claro!', 'Vou ajudar.', etc.)
    linhas = [PREAMBULOS.sub("", ln).rstrip() for ln in texto.splitlines()]
    # Remove preâmbulos artificiais isolados no início da primeira linha (em cadeia)
    if linhas:
        primeira = linhas[0]
        while INICIO_ARTIFICIAL.match(primeira):
            nova = INICIO_ARTIFICIAL.sub("", primeira, count=1).strip()
            if nova == primeira or not nova:
                break
            primeira = nova
        if primeira != linhas[0]:
            linhas[0] = primeira
            acoes.append("preambulo artificial removido")
            return re.sub(r"[ \t]{2,}", " ", "\n".join(linhas).strip()), acoes
    # Remove linhas vazias duplicadas (máx 1)
    limpo = []
    vazio_pre = False
    for ln in linhas:
        if not ln.strip():
            if vazio_pre:
                continue
            vazio_pre = True
        else:
            vazio_pre = False
        limpo.append(ln)
    novo = "\n".join(limpo).strip()
    if novo != texto.strip():
        acoes.append("preambulo/linhas vazias removidas")
    # Colapsa espaços duplos residuais
    final = re.sub(r"[ \t]{2,}", " ", novo)
    if final != novo:
        acoes.append("espacos duplos colapsados")
    return final, acoes


def detectar_evidencia(texto: str) -> dict:
    """Separa fatos de hipóteses presentes no texto (SPEC 3.1/4)."""
    marcadores = [e for e in EVIDENCIA if re.search(rf"\b{re.escape(e)}\b", texto, re.IGNORECASE)]
    incertezas = sorted(set(m.lower() for m in INCERTEZA.findall(texto)))
    return {"marcadores_estado": marcadores, "termos_incerteza": incertezas}


def selecionar_estrutura(tipo: str, complexidade: str) -> str:
    """Escolhe a estrutura adaptativa (SPEC 4/6): resumo, entendimento, técnico."""
    if complexidade == "simples":
        return "direta"
    if tipo == "erro":
        return "problema/causa/impacto/correcao/situacao"
    if tipo == "implementacao":
        return "status/alteracao/motivo/validacao/resultado/pendencias"
    if tipo == "decisao":
        return "problema/opcoes/tradeoffs/decisao/motivo/impacto/riscos"
    if tipo == "investigacao":
        return "pergunta/evidencias/conclusao/duvidas/proximo_passo"
    if tipo == "atualizacao":
        return "o_que_mudou/por_que/resultado/impacto"
    return "resumo/o_que_aconteceu/o_que_foi_feito/resultado/proximo_passo"


def validar_fatos_estados(texto: str) -> dict:
    """Separa fatos de hipóteses (FACT & STATE VALIDATION)."""
    if not texto or not texto.strip():
        return {"fatos": [], "hipoteses": [], "estado": "vazio"}
    
    fatos = []
    hipoteses = []
    
    # Detecta afirmações de fato
    if FATO_INDICADORES.search(texto):
        fatos.append("indicadores de fato presentes")
    
    # Detecta hipóteses
    if HIPOSE_INDICADORES.search(texto):
        hipoteses.append("indicadores de hipótese presentes")
    
    # Classifica o estado geral
    if fatos and not hipoteses:
        estado = "predominantemente_fato"
    elif hipoteses and not fatos:
        estado = "predominantemente_hipotese"
    elif fatos and hipoteses:
        estado = "misto"
    else:
        estado = "neutro"
    
    return {"fatos": fatos, "hipoteses": hipoteses, "estado": estado}


def detectar_incerteza_sistemica(texto: str) -> dict:
    """Detecção sistemática de incerteza (UNCERTAINTY DETECTION)."""
    if not texto or not texto.strip():
        return {"nivel": "nenhuma", "marcadores": [], "alertas": []}
    
    marcadores = INCERTEZA.findall(texto)
    alertas = []
    
    # Classifica nível de incerteza
    if len(marcadores) == 0:
        nivel = "nenhuma"
    elif len(marcadores) <= 2:
        nivel = "baixa"
    elif len(marcadores) <= 5:
        nivel = "media"
    else:
        nivel = "alta"
        alertas.append("alto nível de incerteza detectado")
    
    return {"nivel": nivel, "marcadores": sorted(set(m.lower() for m in marcadores)), "alertas": alertas}


def simplificar_linguagem(texto: str) -> tuple:
    """Simplifica termos técnicos complexos (LANGUAGE SIMPLIFICATION)."""
    if not texto or not texto.strip():
        return texto, []
    
    acoes = []
    novo_texto = texto
    
    # Explica termos técnicos conhecidos
    for termo, explicacao in TERMOS_TECNICOS.items():
        padrao = re.compile(rf'\b{re.escape(termo)}\b', re.IGNORECASE)
        # Verifica se o termo aparece e não está explicado logo em seguida
        if padrao.search(novo_texto):
            # Adiciona explicação apenas se não houver parênteses explicativo
            if not re.search(rf'{re.escape(termo)}\s*\([^)]*\)', novo_texto, re.IGNORECASE):
                novo_texto = padrao.sub(f'{termo} ({explicacao})', novo_texto, count=1)
                acoes.append(f"termo técnico explicado: {termo}")
    
    return novo_texto, acoes


def verificar_veracidade(texto: str) -> dict:
    """Verifica indicadores de falsidade potencial (TRUTHFULNESS CHECK)."""
    if not texto or not texto.strip():
        return {"ok": True, "alertas": []}
    
    alertas = []
    
    # Detecta absolutismos
    absolutismos = FALSIDADE_INDICADORES.findall(texto)
    if absolutismos:
        alertas.append(f"absolutismos detectados: {', '.join(set(absolutismos))}")
    
    # Detecta contradições simples
    if re.search(r'\b(sim|nao)\b.*\b(nao|sim)\b', texto, re.IGNORECASE):
        alertas.append("possível contradição detectada")
    
    return {"ok": len(alertas) == 0, "alertas": alertas}


def executar_checklist_final(texto: str, relatorio: dict) -> dict:
    """Executa checklist final sistemático (CHECKLIST FINAL)."""
    checklist = {
        "clareza": {"ok": True, "itens": []},
        "conteudo": {"ok": True, "itens": []},
        "verdade": {"ok": True, "itens": []},
        "operacao": {"ok": True, "itens": []},
        "comunicacao": {"ok": True, "itens": []},
    }
    
    if not texto or not texto.strip():
        checklist["conteudo"]["ok"] = False
        checklist["conteudo"]["itens"].append("resposta vazia")
        return checklist
    
    # Clareza
    if relatorio.get("complexidade", {}).get("frase_media", 0) > 25:
        checklist["clareza"]["ok"] = False
        checklist["clareza"]["itens"].append("frases muito longas")
    
    # Conteúdo
    if relatorio.get("score_pt", 0) < 30:
        checklist["conteudo"]["ok"] = False
        checklist["conteudo"]["itens"].append("idioma não validado")
    
    # Verdade
    if relatorio.get("fatos_estados", {}).get("estado") == "predominantemente_hipotese":
        checklist["verdade"]["ok"] = False
        checklist["verdade"]["itens"].append("predominância de hipóteses")
    
    if relatorio.get("veracidade", {}).get("alertas"):
        checklist["verdade"]["ok"] = False
        checklist["verdade"]["itens"].extend(relatorio["veracidade"]["alertas"])
    
    # Comunicação
    if relatorio.get("bajulacao", {}).get("encontrados"):
        checklist["comunicacao"]["ok"] = False
        checklist["comunicacao"]["itens"].append("bajulação detectada")
    
    if relatorio.get("acoes"):
        # Se houve ações de normalização, verificar se foi bem-sucedido
        if "preambulo artificial removido" in relatorio["acoes"]:
            checklist["comunicacao"]["itens"].append("preâmbulo removido")
    
    return checklist


def normalizar_resposta(texto: str, tipo: str | None = None) -> dict:
    """Pipeline final de normalização: reusa peças + etapas próprias (SPEC 1.0 completo).

    Pipeline completo:
    INPUT -> INTENT DETECTION -> TASK CLASSIFICATION -> VALIDAÇÃO PT-BR ->
    TIPO/COMPLEXIDADE -> ANTIBAJULAÇÃO -> REDUNDÂNCIA -> EVIDÊNCIA ->
    FATOS/ESTADOS -> INCERTEZA -> LINGUAGEM -> VERACIDADE -> ESTRUTURA ->
    CHECKLIST FINAL -> FINAL RESPONSE

    Returns:
        dict com ok, texto, score_pt, tipo, complexidade, estrutura,
        evidencia, acoes, bajulacao, validacao, intencao, tarefa,
        fatos_estados, incerteza, linguagem, veracidade, checklist.
    """
    original = texto or ""
    texto_final = original
    acoes = []

    # 1. Padrão linguístico (reuso do gate pt-BR existente)
    try:
        validacao = validar_e_corrigir(texto_final)
        acoes.extend(
            [f"pt-br: {validacao.get('acao')}"] if validacao.get("acao") not in ("aprovado", "vazio")
            else []
        )
        if validacao.get("texto") and validacao.get("acao") != "vazio":
            texto_final = validacao["texto"]
        score_pt = validacao.get("score", 0)
    except Exception as e:  # fail-soft: nunca derruba a resposta
        validacao = {"ok": True, "acao": "erro_interno", "score": 0}
        score_pt = 0
        acoes.append(f"validador indisponivel ({e})")

    # 2. INTENT DETECTION (intenção do usuário)
    intencao = detectar_intencao(texto_final or original)

    # 3. TASK CLASSIFICATION (classificação da tarefa)
    tarefa = classificar_tarefa(texto_final or original)

    # 4. Tipo de interação e complexidade
    tipo_final = tipo or detectar_tipo(texto_final or original)
    complexidade = medir_complexidade(texto_final or original)

    # 5. Antibajulação (reuso do detector existente)
    try:
        bajulacao = detectar_bajulacao(texto_final or original)
        if not bajulacao.get("ok", True):
            acoes.append(f"bajulacao detectada: {', '.join(bajulacao.get('encontrados', []))}")
    except Exception:
        bajulacao = {"ok": True, "encontrados": [], "score": 0}

    # 6. Remoção de redundância
    texto_final, acoes_red = remover_redundancia(texto_final or original)
    acoes.extend(acoes_red)

    # 7. Evidência e transparência (detecção, nunca altera fatos)
    evidencia = detectar_evidencia(texto_final)

    # 8. FACT & STATE VALIDATION (validação de fatos e estados)
    fatos_estados = validar_fatos_estados(texto_final)

    # 9. UNCERTAINTY DETECTION (detecção sistemática de incerteza)
    incerteza = detectar_incerteza_sistemica(texto_final)
    if incerteza["alertas"]:
        acoes.extend(incerteza["alertas"])

    # 10. LANGUAGE SIMPLIFICATION (simplificação de linguagem ativa)
    texto_final, acoes_lang = simplificar_linguagem(texto_final)
    acoes.extend(acoes_lang)

    # 11. TRUTHFULNESS CHECK (verificação de veracidade)
    veracidade = verificar_veracidade(texto_final)
    if veracidade["alertas"]:
        acoes.extend(veracidade["alertas"])

    # 12. Estrutura adaptativa
    estrutura = selecionar_estrutura(tipo_final, complexidade["nivel"])

    # 13. CHECKLIST FINAL (verificação sistemática)
    relatorio_parcial = {
        "complexidade": complexidade,
        "score_pt": score_pt,
        "fatos_estados": fatos_estados,
        "veracidade": veracidade,
        "bajulacao": bajulacao,
        "acoes": acoes,
    }
    checklist = executar_checklist_final(texto_final, relatorio_parcial)

    return {
        "ok": True,
        "texto": texto_final,
        "original": original,
        "score_pt": round(float(score_pt), 2) if score_pt else 0.0,
        "tipo": tipo_final,
        "intencao": intencao,
        "tarefa": tarefa,
        "complexidade": complexidade,
        "estrutura": estrutura,
        "evidencia": evidencia,
        "fatos_estados": fatos_estados,
        "incerteza": incerteza,
        "bajulacao": bajulacao,
        "veracidade": veracidade,
        "acoes": acoes,
        "validacao": validacao,
        "checklist": checklist,
    }


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        try:
            data = json.loads(sys.argv[2])
        except (IndexError, json.JSONDecodeError):
            print(json.dumps({"ok": False, "erro": "JSON inválido"}, ensure_ascii=False))
            return 2
        texto = data.get("texto", "")
        tipo = data.get("tipo")
    elif len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        texto = sys.stdin.read()
        tipo = None
    elif len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
        tipo = None
    else:
        print("Uso: python response_normalizer.py \"texto\" | --stdin | --json '{\"texto\": ...}'")
        return 2

    resultado = normalizar_resposta(texto, tipo)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())