"""Compreensão de Pedidos — núcleo.

Converte um pedido (fala/texto/comando) do usuário em um entendimento estruturado:
objetivo, ações esperadas, contexto, conceitos, restrições, ambiguidades,
critérios de sucesso, riscos de desperdício e plano sugerido.

Princípios:
  - Rápido e estático por padrão (stdlib, sem LLM para o núcleo).
  - Refino com LLM é OPCIONAL e fail-soft (usa a LLM que estiver disponível).
  - Resolve conceitos no acervo do ecossistema (memória, skills, projetos, scripts).

Uso CLI:
  python compreensao.py "<pedido>" [--refinar] [--json]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
SCRIPTS = os.path.join(BASE, 'scripts')
MCP_DIR = os.path.join(BASE, 'mcp')
PROJETOS_DIR = os.path.join(BASE, 'Projetos')

# Ações explícitas comuns (verbo -> categoria de ação)
ACOES = [
    (r'\b(commit|commitar|publicar|push|enviar|subir)\w*', 'sincronizar'),
    (r'\b(criar|montar|construir|desenvolver|escrever|gerar)\w*', 'construir'),
    (r'\b(atualizar|melhorar|aprimorar|evoluir|upgrade)\w*', 'evoluir'),
    (r'\b(corrigir|consertar|arrumar|resolver|ajustar|fixar)\w*', 'corrigir'),
    (r'\b(verificar|checar|auditar|validar|testar|inspecionar)\w*', 'verificar'),
    (r'\b(analisar|entender|explicar|diagnosticar|investigar)\w*', 'analisar'),
    (r'\b(instalar|deploy|deployar|implantar|publicar)\w*', 'implantar'),
    (r'\b(apagar|excluir|remover|deletar|limpar|organizar|mover|renomear)\w*', 'manipular'),
    (r'\b(otimizar|refinar|polir|enxugar)\w*', 'otimizar'),
    (r'\b(aprender|treinar|estudar|registrar|documentar)\w*', 'aprender'),
    (r'\b(backup|salvar|guardar|persistir)\w*', 'persistir'),
    (r'\b(consultar|buscar|pesquisar|procurar|localizar)\w*', 'consultar'),
]

VAGOS = re.compile(r'\b(fazer|coisa|isso|aquilo|qualquer|tudo|etc|deixa)\b', re.I)
RESTRICOES = re.compile(
    r'(n[aã]o\w*\s+\w+|nunca|evite|evitar|sem\s+\w+|exceto|somente|apenas|apenas|'
    r'cuidado|importante|obrigat[oó]rio|proibido|n[aã]o toque|n[aã]o altere)', re.I)
ESCOPO_CREEP = re.compile(r'\b(tamb[eé]m|de quebra|j[aá] que|aproveitando|e mais|ainda)\b', re.I)
PERGUNTAS = re.compile(r'^(o que|como|quando|onde|por que|porque|existe|est[aá]|voc[eê]|qual|quais|quanto|quantos)\b', re.I)

DESPERDICIO_SEM_ENTREGAVEL = re.compile(r'\b(melhorar|deixar|arrumar|ver depois|um dia|talvez)\b', re.I)


# ---------------------------------------------------------------------------
# .env (chaves de LLM ficam no scripts/.env)
# ---------------------------------------------------------------------------
def _carregar_env():
    for arq in (os.path.join(SCRIPTS, '.env'), os.path.join(BASE, '.env.example')):
        if not os.path.exists(arq):
            continue
        try:
            with open(arq, encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha or linha.startswith('#') or '=' not in linha:
                        continue
                    k, v = linha.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Extração heurística (estática, sem LLM)
# ---------------------------------------------------------------------------
def _extrair_acoes(pedido):
    acoes = []
    for padrao, categoria in ACOES:
        for m in re.finditer(padrao, pedido, re.I):
            # evita repetir o mesmo verbo
            verbo = m.group(0).lower()
            if any(a['verbo'] == verbo for a in acoes):
                continue
            # objeto = palavras após o verbo até o próximo verbo de ação
            resto = pedido[m.end():]
            fim = len(resto)
            for p2, _ in ACOES:
                prox = re.search(p2, resto, re.I)
                if prox and prox.start() < fim:
                    fim = prox.start()
            objeto = ' '.join(re.findall(r'\b[\wÀ-ÿ]+[\wÀ-ÿ\-\./]*\b', resto[:fim]))[:120]
            acoes.append({'verbo': verbo, 'categoria': categoria, 'objeto': objeto or '—'})
    return acoes[:6]


def _extrair_conceitos(pedido):
    # entidades conhecidas: nomes de projetos, skills, scripts e termos em maiúscula
    conhecidos = set()
    for raiz in (PROJETOS_DIR,):
        if os.path.isdir(raiz):
            for nome in os.listdir(raiz):
                if re.search(r'\b' + re.escape(nome.lower()) + r'\b', pedido.lower()):
                    conhecidos.add(nome)
    if os.path.isdir(MCP_DIR):
        for dominio in os.listdir(MCP_DIR):
            hab = os.path.join(MCP_DIR, dominio, 'habilidades')
            if os.path.isdir(hab):
                for skill in os.listdir(hab):
                    if re.search(r'\b' + re.escape(skill.replace('-', ' ').lower()) + r'\b', pedido.lower()):
                        conhecidos.add(f'skill:{skill}')
    for nome in os.listdir(SCRIPTS) if os.path.isdir(SCRIPTS) else []:
        nome = nome[:-3] if nome.endswith('.py') else nome
        if re.search(r'\b' + re.escape(nome.lower().replace('_', ' ')) + r'\b', pedido.lower()):
            conhecidos.add(f'script:{nome}')
    termos = [t.lower() for t in re.findall(r'\b[A-ZÀ-Ý][A-Za-zÀ-ÿ]{3,}\b', pedido)]
    return sorted(set(list(conhecidos) + termos))[:12]


def _extrair_objetivo(pedido):
    acoes = _extrair_acoes(pedido)
    if acoes:
        a = acoes[0]
        return f"{a['categoria']}: {a['verbo']} {a['objeto']}".strip()
    if PERGUNTAS.match(pedido.strip()):
        return f"responder: {pedido.strip()[:140]}"
    return pedido.strip()[:160]


def _extrair_restricoes(pedido):
    out = []
    for m in RESTRICOES.finditer(pedido):
        frag = m.group(0).strip()
        if frag and frag not in out:
            out.append(frag[:80])
    return out[:5]


def _detectar_ambiguidades(pedido):
    amb = []
    acoes = _extrair_acoes(pedido)
    if not acoes:
        amb.append({'tipo': 'SEM_ACAO', 'custo': 'medio',
                    'msg': 'Nenhuma ação explícita detectada — o que exatamente deve ser feito?'})
    if len(acoes) > 2:
        amb.append({'tipo': 'MULTIPLOS_OBJETIVOS', 'custo': 'medio',
                    'msg': f'{len(acoes)} ações distintas detectadas — qual é a prioridade/escopo?'})
    if VAGOS.search(pedido):
        amb.append({'tipo': 'LINGUAGEM_VAGA', 'custo': 'medio',
                    'msg': 'Termos vagos ("fazer", "coisa", "isso") — defina o alvo concreto.'})
    if 'projeto' in pedido.lower() or 'app' in pedido.lower():
        alvos = [n for n in (os.listdir(PROJETOS_DIR) if os.path.isdir(PROJETOS_DIR) else [])]
        achados = [a for a in alvos if a.lower() in pedido.lower()]
        if not achados:
            amb.append({'tipo': 'ALVO_NAO_ESPECIFICADO', 'custo': 'alto',
                        'msg': 'Menção a projeto/app sem nomear qual — errar aqui custa caro.'})
    if re.search(r'\b(se possível|se der|sem pressa|quando der)\b', pedido, re.I):
        amb.append({'tipo': 'URGENCIA_AMBIGUA', 'custo': 'baixo',
                    'msg': 'Urgência indefinida — agora ou pode aguardar?'})
    return amb[:5]


def _criterios_sucesso(pedido, entendimento):
    c = []
    for a in entendimento.get('acoes', [])[:3]:
        c.append(f"{a['verbo']} de '{a['objeto'][:40]}' concluído e verificado")
    if not c:
        c.append('Resposta entregue conforme objetivo e validada pelo Kernel')
    if 'commitar' in pedido.lower() or 'push' in pedido.lower():
        c.append('Sincronizado no GitHub (commit + push)')
    return c[:4]


def _riscos_desperdicio(pedido, entendimento):
    riscos = []
    if ESCOPO_CREEP.search(pedido):
        riscos.append({'tipo': 'ESCOPO_CREEP', 'nivel': 'medio',
                       'msg': 'Pedido carrega escopo extra ("também", "de quebra") — combine antes de ampliar.'})
    if DESPERDICIO_SEM_ENTREGAVEL.search(pedido):
        riscos.append({'tipo': 'SEM_ENTREGAVEL_CLARO', 'nivel': 'alto',
                       'msg': 'Sem entregável observável — risco de trabalho sem resultado.'})
    if not entendimento.get('acoes'):
        riscos.append({'tipo': 'ACAO_INDEFINIDA', 'nivel': 'alto',
                       'msg': 'Sem ação identificada — provável desperdício ou pedido informativo.'})
    return riscos[:4]


def _plano_sugerido(entendimento):
    plano = []
    for a in entendimento.get('acoes', [])[:4]:
        plano.append(f"{a['categoria'].capitalize()} — {a['objeto'][:60] or a['verbo']}")
    if not plano:
        plano = ['Interpretar o pedido como pergunta/resposta objetiva', 'Verificar se já há resposta no conhecimento/memória antes de executar']
    plano.append('Validar entrega no Kernel (contrato de saída) antes de responder')
    return plano


def _score_clareza(pedido, entendimento):
    pontos = 100
    if not entendimento.get('acoes'):
        pontos -= 30
    if len(entendimento.get('ambiguidades', [])):
        pontos -= 15 * len(entendimento['ambiguidades'])
    if VAGOS.search(pedido):
        pontos -= 10
    if len(pedido) < 8:
        pontos -= 20
    if ESCOPO_CREEP.search(pedido):
        pontos -= 10
    return max(0, min(100, pontos))


def _julgamento(score, ambiguidades):
    if not ambiguidades and score >= 80:
        return 'CLARO'
    if score >= 60:
        return 'PARCIALMENTE_CLARO'
    return 'AMBIGUO'


# ---------------------------------------------------------------------------
# Resolução de conceitos no acervo (memória + conhecimento)
# ---------------------------------------------------------------------------
def resolver_conceitos(conceitos):
    """Para cada conceito, busca referências em memória/skills/projetos/scripts."""
    resultados = []
    alvos = list(conceitos)
    if not alvos:
        return resultados
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, 'memory_engine.py'), 'search', ' '.join(alvos[:4])],
            capture_output=True, text=True, timeout=25, encoding='utf-8', errors='replace')
        memoria = proc.stdout.strip()[:800] if proc.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        memoria = ''
    # acervo de skills: cada skill conhecida vira referência
    skills = []
    if os.path.isdir(MCP_DIR):
        for dominio in os.listdir(MCP_DIR):
            hab = os.path.join(MCP_DIR, dominio, 'habilidades')
            if os.path.isdir(hab):
                for s in os.listdir(hab):
                    skills.append(f'mcp/{dominio}/habilidades/{s}')
    for c in alvos:
        entrada = {'conceito': c, 'referencias': []}
        if 'skill:' in str(c):
            nome = str(c).split(':', 1)[1]
            for s in skills:
                if s.endswith('/' + nome):
                    entrada['referencias'].append({'tipo': 'skill', 'local': s})
                    break
        if 'script:' in str(c):
            entrada['referencias'].append({'tipo': 'script', 'local': os.path.join('scripts', str(c).split(':', 1)[1] + '.py')})
        for p in (os.listdir(PROJETOS_DIR) if os.path.isdir(PROJETOS_DIR) else []):
            if str(c).lower() == p.lower():
                entrada['referencias'].append({'tipo': 'projeto', 'local': os.path.join('Projetos', p)})
        entrada['memoria'] = memoria[:300] if memoria else ''
        resultados.append(entrada)
    return resultados


# ---------------------------------------------------------------------------
# Detecção de desperdício (repetição, escopo, atalho)
# ---------------------------------------------------------------------------
def detectar_desperdicio(pedido):
    analise = {'riscos': [], 'sugestoes': [], 'repeticao': {'possivel': False, 'fonte': ''}}
    # pedido repetido vs última tarefa registrada
    state_path = os.path.join(BASE, 'runtime', 'state.json')
    try:
        if os.path.exists(state_path):
            with open(state_path, encoding='utf-8') as f:
                state = json.load(f)
            ultima = str(state.get('last_task', ''))
            if ultima and ultima.strip():
                n = max(len(pedido), len(ultima))
                if n and len(set(pedido.lower()) & set(ultima.lower())) / n > 0.55:
                    analise['repeticao'] = {'possivel': True, 'fonte': f'last_task (runtime/state.json): "{ultima[:80]}"'}
    except (OSError, ValueError):
        pass
    # atalho: se o pedido menciona uma skill/script conhecido, recomendar
    conceitos = _extrair_conceitos(pedido)
    for c in conceitos:
        if str(c).startswith(('skill:', 'script:')):
            analise['sugestoes'].append(f'Usar a capacidade existente "{c}" em vez de reinventar')
    analise['riscos'] = _riscos_desperdicio(pedido, {'acoes': _extrair_acoes(pedido)})
    return analise


# ---------------------------------------------------------------------------
# Refino com LLM (fail-soft, agnóstico de fornecedor)
# ---------------------------------------------------------------------------
def _resolver_providers():
    """Devolve lista de (provedor, modelo, chave) na ordem de preferência."""
    providers = []
    modelo_nv = os.environ.get('COMPREENSAO_MODELO_NVIDIA', 'nvidia/llama-3.3-70b-instruct')
    if os.environ.get('NVIDIA_API_KEY'):
        providers.append(('nvidia', modelo_nv, os.environ['NVIDIA_API_KEY']))
    if os.environ.get('OPENAI_API_KEY'):
        providers.append(('openai', 'openai/gpt-4o-mini', os.environ['OPENAI_API_KEY']))
    if os.environ.get('ANTHROPIC_API_KEY'):
        providers.append(('anthropic', 'anthropic/claude-sonnet-4-5', os.environ['ANTHROPIC_API_KEY']))
    return providers


def refinar_com_llm(pedido, entendimento):
    """Chama UMA LLM disponível para criticar/melhorar o entendimento. Fail-soft."""
    _carregar_env()
    providers = _resolver_providers()
    if not providers:
        return {'usado': False, 'motivo': 'nenhuma chave de LLM disponível (NVIDIA/OpenAI/Anthropic)', 'entendimento': entendimento}
    try:
        import litellm
    except ImportError:
        return {'usado': False, 'motivo': 'litellm não instalado', 'entendimento': entendimento}
    prompt = (
        'Você é o módulo de Compreensão de Pedidos do EcoSystemUmGrau. O usuário pediu: '
        f'"{pedido[:1000]}"\n\n'
        f'Entendimento preliminar (heurístico): {json.dumps(entendimento, ensure_ascii=False)}\n\n'
        'Responda APENAS com JSON: {"objetivo_corrigido": "...", "lacunas": [...], '
        '"melhorias": [...], "observacao": "..."}. '
        'Corrija erros de interpretação e aponte apenas o que faltou para transformar em ação.')
    for provedor, modelo, chave in providers:
        try:
            resp = litellm.completion(
                model=modelo,
                messages=[{'role': 'user', 'content': prompt}],
                api_key=chave,
                max_tokens=500,
                timeout=30,
            )
            texto = resp['choices'][0]['message']['content']
            criticas = json.loads(re.search(r'\{.*\}', texto, re.S).group(0)) if re.search(r'\{.*\}', texto, re.S) else {'observacao': texto[:300]}
            return {'usado': True, 'provedor': provedor, 'modelo': modelo, 'critica': criticas, 'entendimento': entendimento}
        except Exception as e:
            ultimo_erro = f'{provedor}: {e}'
            continue
    return {'usado': False, 'motivo': f'falha em todos os provedores ({ultimo_erro})', 'entendimento': entendimento}


# ---------------------------------------------------------------------------
# Compreensão completa
# ---------------------------------------------------------------------------
def compreender(pedido, refinar=False):
    pedido = (pedido or '').strip()
    acoes = _extrair_acoes(pedido)
    conceitos = _extrair_conceitos(pedido)
    ambiguidades = _detectar_ambiguidades(pedido)
    entendimento = {
        'objetivo': _extrair_objetivo(pedido),
        'acoes': acoes,
        'contexto_relevante': conceitos[:6],
        'conceitos': conceitos,
        'restricoes': _extrair_restricoes(pedido),
        'ambiguidades': ambiguidades,
        'criterios_sucesso': [],
        'riscos': [],
        'plano_sugerido': [],
        'score_entendimento': 0,
        'julgamento': '',
        'llm_refino': None,
    }
    entendimento['criterios_sucesso'] = _criterios_sucesso(pedido, entendimento)
    entendimento['riscos'] = _riscos_desperdicio(pedido, entendimento)
    entendimento['plano_sugerido'] = _plano_sugerido(entendimento)
    entendimento['score_entendimento'] = _score_clareza(pedido, entendimento)
    entendimento['julgamento'] = _julgamento(entendimento['score_entendimento'], ambiguidades)
    if refinar:
        entendimento['llm_refino'] = refinar_com_llm(pedido, entendimento)
    return entendimento


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Compreensão de Pedidos do EcoSystemUmGrau')
    parser.add_argument('pedido', nargs='*', default=[])
    parser.add_argument('--refinar', action='store_true', help='refina com a LLM disponível (fail-soft)')
    parser.add_argument('--json', action='store_true', help='saída JSON')
    args = parser.parse_args()
    if not args.pedido:
        pedido = sys.stdin.read().strip() if not sys.stdin.isatty() else ''
    else:
        pedido = ' '.join(args.pedido)
    if not pedido:
        print(json.dumps({'erro': 'nenhum pedido informado'}, ensure_ascii=False))
        return 1
    out = compreender(pedido, refinar=args.refinar)
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else
          f"OBJETIVO: {out['objetivo']}\nSCORE: {out['score_entendimento']} ({out['julgamento']})\n"
          f"AÇÕES: {len(out['acoes'])} | AMBIGUIDADES: {len(out['ambiguidades'])} | CONCEITOS: {len(out['conceitos'])}")
    return 0


if __name__ == '__main__':
    _carregar_env()
    sys.exit(main())
