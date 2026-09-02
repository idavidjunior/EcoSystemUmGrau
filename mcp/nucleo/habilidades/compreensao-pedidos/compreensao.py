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
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
SCRIPTS = os.path.join(BASE, 'scripts')
MCP_DIR = os.path.join(BASE, 'mcp')
PROJETOS_DIR = os.path.join(BASE, 'Projetos')
SPECS_DIR = os.path.join(BASE, 'specs')

# Ações explícitas (radicais cobrem infinitivo e imperativo: explicar/explique;
# inclui variantes c→qu da conjugação: explic/expliqu, verific/verifiqu...)
ACOES = [
    (r'\b(commit|push|public|subir|enviar|sincroniz)\w*', 'sincronizar'),
    (r'\b(criar|cri|montar|construir|desenvolver|escrever|gerar|implementar)\w*', 'construir'),
    (r'\b(atualiz|melhor|aprimor|evolu|upgrade)\w*', 'evoluir'),
    (r'\b(corrig|consert|arrum|resolv|ajust|repar)\w*', 'corrigir'),
    (r'\b(verific|verifiqu|chec|chequ|audit|valid|test|inspecion)\w*', 'verificar'),
    (r'\b(analis|entend|explic|expliqu|diagnostic|diagnostiqu|investig)\w*', 'analisar'),
    (r'\b(instal|deploy|implant)\w*', 'implantar'),
    (r'\b(apag|exclu|remov|delet|limpa|organiz|mover|renome)\w*', 'manipular'),
    (r'\b(otimiz|refin|polir|enxug)\w*', 'otimizar'),
    (r'\b(aprend|trein|estud|registr|document)\w*', 'aprender'),
    (r'\b(backup|salv|guard|persist)\w*', 'persistir'),
    (r'\b(consult|busc|busqu|pesquis|procur|localiz)\w*', 'consultar'),
    (r'\b(execut|realiz|faz|faca|faça|rode|roda)\w*', 'executar'),
]

NON_VERBOS = {'geral', 'gerencia', 'gerente', 'crise', 'fixo', 'política', 'policia',
              'polícia', 'movimento', 'removível', 'removivel', 'gerador', 'criação',
              'criacao', 'salvo', 'salva'}

STOP_TERMOS = {
    'quero', 'vou', 'preciso', 'poderia', 'pode', 'faça', 'fazer', 'me', 'eu',
    'você', 'voce', 'então', 'sobre', 'agora', 'também', 'depois', 'aquela', 'aquele',
    'uma', 'um', 'qualquer', 'todo', 'toda', 'todos', 'todas', 'como', 'quando', 'onde',
    'seja', 'ser', 'está', 'estao', 'foi', 'sao', 'vamos', 'gostaria', 'precisaria', 'queria',
}

VAGOS = re.compile(r'\b(fazer|coisa|isso|aquilo|qualquer|tudo|etc|deixa)\b', re.I)
RESTRICOES = re.compile(
    r'(n[aã]o\w*\s+\w+|nunca|evite|evitar|sem\s+\w+|exceto|somente|apenas|'
    r'cuidado|importante|obrigat[oó]rio|proibido|n[aã]o toque|n[aã]o altere)', re.I)
ESCOPO_CREEP = re.compile(r'\b(tamb[eé]m|de quebra|j[aá] que|aproveitando|e mais|ainda)\b', re.I)
PERGUNTAS = re.compile(r'^(o que|como|quando|onde|por que|porque|existe|est[aá]|voc[eê]|qual|quais|quanto|quantos)\b', re.I)

DESPERDICIO_SEM_ENTREGAVEL = re.compile(r'\b(melhorar|deixar|arrumar|ver depois|um dia|talvez)\b', re.I)


# ---------------------------------------------------------------------------
# .env (chaves de LLM ficam no scripts/.env)
# ---------------------------------------------------------------------------
def _carregar_env():
    # Fonte única de chaves: scripts/.env (NUNCA .env.example — só placeholders).
    arq = os.path.join(SCRIPTS, '.env')
    if not os.path.exists(arq):
        return
    try:
        with open(arq, encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith('#') or '=' not in linha:
                    continue
                k, v = linha.split('=', 1)
                v = v.strip().strip('"').strip("'")
                if not v or re.search(r'your[-_ ]|example|xxxx|sk-replace|^<.*>$', v, re.I):
                    continue
                os.environ.setdefault(k.strip(), v)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Extração heurística (estática, sem LLM)
# ---------------------------------------------------------------------------
def _extrair_acoes(pedido):
    matches = []
    for padrao, categoria in ACOES:
        for m in re.finditer(padrao, pedido, re.I):
            matches.append((m.start(), m, categoria))
    matches.sort(key=lambda t: t[0])  # ordem de aparição no texto
    # verbo auxiliar genérico ("faça o backup", "faz a análise") imediatamente
    # antes de outra ação real não é uma ação própria
    matches = [m for m in matches
               if not (m[2] == 'executar' and
                       any(j != m and 0 <= j[0] - m[1].end() <= 12 for j in matches))]
    vistos = set()
    acoes = []
    for _, m, categoria in matches:
        verbo = m.group(0).lower()
        if verbo in vistos or verbo in NON_VERBOS:
            continue
        vistos.add(verbo)
        # objeto = palavras após o verbo até o próximo verbo de ação
        resto = pedido[m.end():]
        fim = len(resto)
        for p2, _ in ACOES:
            prox = re.search(p2, resto, re.I)
            if prox and prox.start() < fim:
                fim = prox.start()
        objeto = ' '.join(re.findall(r'\b[\wÀ-ÿ]+[\wÀ-ÿ\-\./]*\b', resto[:fim]))
        # corta conectores que iniciam sub-oração (para/quando/sem/e/com/então...)
        objeto = re.sub(r'\s+(para|quando|sem|com|então|depois|também|se|após|antes|porque|e|em|ou)\s*$',
                        '', objeto, flags=re.I).strip()
        # corta "e <verbo>" que inicia a próxima ação (ex.: "... X e faca o backup")
        partes = re.split(r'\s+e\s+', objeto)
        objeto = partes[0]
        for p in partes[1:]:
            primeira = (p.strip().split()[0] if p.strip() else '')
            if primeira and (primeira.lower() in STOP_TERMOS or
                             any(re.search(padrao, primeira, re.I) for padrao, _ in ACOES)):
                break
            objeto += ' e ' + p
        acoes.append({'verbo': verbo, 'categoria': categoria, 'objeto': objeto[:120] or '—'})
    return acoes[:6]


def _extrair_conceitos(pedido):
    # entidades conhecidas: nomes de projetos, skills, scripts
    conhecidos = []
    baixo = pedido.lower()
    if os.path.isdir(PROJETOS_DIR):
        for nome in os.listdir(PROJETOS_DIR):
            if re.search(r'\b' + re.escape(nome.lower()) + r'\b', baixo):
                conhecidos.append(nome)
    if os.path.isdir(MCP_DIR):
        for dominio in os.listdir(MCP_DIR):
            hab = os.path.join(MCP_DIR, dominio, 'habilidades')
            if os.path.isdir(hab):
                for skill in os.listdir(hab):
                    if re.search(r'\b' + re.escape(skill.replace('-', ' ').lower()) + r'\b', baixo):
                        conhecidos.append(f'skill:{skill}')
    if os.path.isdir(SCRIPTS):
        for nome in os.listdir(SCRIPTS):
            nome_py = nome[:-3] if nome.endswith('.py') else nome
            if re.search(r'\b' + re.escape(nome_py.lower().replace('_', ' ')) + r'\b', baixo):
                conhecidos.append(f'script:{nome_py}')
    # termos capitulizados genéricos (sem stopwords e sem duplicar conhecidos)
    termos = []
    for t in re.findall(r'\b[A-ZÀ-Ý][A-Za-zÀ-ÿ]{3,}\b', pedido):
        if t.lower() in STOP_TERMOS:
            continue
        if any(t.lower() == c.lower() for c in conhecidos):
            continue
        if any(re.search(p, t, re.I) for p, _ in ACOES):  # verbo capitalizado (início de frase)
            continue
        termos.append(t.lower())
    return sorted(set(conhecidos + termos))[:12]


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
        alvos = os.listdir(PROJETOS_DIR) if os.path.isdir(PROJETOS_DIR) else []
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
        plano = ['Interpretar o pedido como pergunta/resposta objetiva',
                 'Verificar se já há resposta no conhecimento/memória antes de executar']
    plano.append('Validar entrega no Kernel (contrato de saída) antes de responder')
    return plano


# ---------------------------------------------------------------------------
# Checklist de entrega + gate de veto (Fase 1)
# Capricho: entregável verificável ("pronto e finalizado") + o que está
# PROIBIDO/BLOQUEADO antes de executar. Não toca no Kernel: é um gate
# consultável (a LLM ou um agente o consulta antes de executar).
# ---------------------------------------------------------------------------
VETOS = [
    ('SINCRONIZAR_GIT', re.compile(r'\b(git add|git commit|git push|push direto|commitar direto|commit direto|fazer commit|push sem o gate)\b', re.I),
     'Persistência em git passa EXCLUSIVAMENTE pelo gate scripts/persistencia.ps1. Proibido git add/commit/push direto.'),
    ('DESTRUICAO', re.compile(r'\b(apagar|deletar|remover|excluir|rm -rf|formatar|destruir)\b', re.I),
     'Operação destrutiva irreversível exige backup e confirmação humana antes de qualquer ação.'),
    ('SECRETOS', re.compile(r'\b(senha em|código-fonte\b.*\bchave|token de api|api key|segredo no código|chave privada)\b', re.I),
     'Nunca colocar chaves, senhas ou tokens em código-fonte. Validar exposição antes de persistir.'),
    ('DESKTOP', re.compile(r'\b(fechar o opencode desktop|matar o opencode|encerrar o opencode|fechar o opencode)\b', re.I),
     'O OpenCode desktop NUNCA pode ser fechado ou morto por automação.'),
]


def _checklist_entrega(pedido, entendimento):
    """Monta checklist de entrega verificável a partir da compreensão.

    Itens = "pronto e finalizado" observável (ações + critérios de sucesso).
    Vetos = o que está PROIBIDO dentro do escopo do pedido (gate de veto).
    """
    check = []
    for a in entendimento.get('acoes', [])[:6]:
        check.append(f"Concluir: {a['verbo']} — {a['objeto'][:60] or a['verbo']}")
    for c in entendimento.get('criterios_sucesso', [])[:4]:
        if not any(c[:38] in item for item in check):
            check.append(f"Validar: {c}")
    if not check:
        check.append('Entregar resposta objetiva conforme a intenção do pedido')
    elif not entendimento.get('acoes'):
        check.append('Confirmar se o pedido é informativo (não requer execução)')

    vetos = []
    for nome, padrao, msg in VETOS:
        if padrao.search(pedido):
            vetos.append({'regra': nome, 'proibido': True, 'detalhe': msg})
    # Vetos implícitos derivados de ambigüidades/riscos (bloqueiam se perigosos)
    for risco in entendimento.get('riscos', []):
        if risco.get('tipo') == 'SEM_ENTREGAVEL_CLARO':
            vetos.append({'regra': 'SEM_ENTREGAVEL', 'proibido': True,
                          'detalhe': 'Sem entregável observável — bloqueado até definir o que será entregue.'})
        if risco.get('tipo') == 'ACAO_INDEFINIDA':
            vetos.append({'regra': 'ACAO_INDEFINIDA', 'proibido': True,
                          'detalhe': 'Sem ação identificada — confirmar o que deve ser feito antes de executar.'})

    return {'itens': check, 'vetos': vetos,
            'status': 'BLOQUEADO' if vetos else 'APROVADO'}


def gerar_checklist(pedido):
    """Gera o gate consultável de entrega/veto para um pedido (Fase 1)."""
    entendimento = compreender(pedido)
    return _checklist_entrega(pedido, entendimento)


def _score_clareza(pedido, entendimento):
    pontos = 100
    if not entendimento.get('acoes'):
        pontos -= 30
    if entendimento.get('ambiguidades'):
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
    memoria = ''
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, 'memory_engine.py'), 'search', ' '.join(str(a) for a in alvos[:4])],
            capture_output=True, text=True, timeout=25, encoding='utf-8', errors='replace')
        if proc.returncode == 0:
            memoria = proc.stdout.strip()[:800]
    except (OSError, subprocess.TimeoutExpired):
        pass
    skills = []
    if os.path.isdir(MCP_DIR):
        for dominio in os.listdir(MCP_DIR):
            hab = os.path.join(MCP_DIR, dominio, 'habilidades')
            if os.path.isdir(hab):
                for s in os.listdir(hab):
                    skills.append(f'mcp/{dominio}/habilidades/{s}')
    for c in alvos:
        entrada = {'conceito': str(c), 'referencias': []}
        nome = str(c)
        if nome.startswith('skill:'):
            nome_skill = nome.split(':', 1)[1]
            for s in skills:
                if s.endswith('/' + nome_skill):
                    entrada['referencias'].append({'tipo': 'skill', 'local': s})
                    break
        elif nome.startswith('script:'):
            nome_script = nome.split(':', 1)[1]
            entrada['referencias'].append({'tipo': 'script', 'local': os.path.join('scripts', nome_script + '.py')})
        for p in (os.listdir(PROJETOS_DIR) if os.path.isdir(PROJETOS_DIR) else []):
            if nome.lower() == p.lower():
                entrada['referencias'].append({'tipo': 'projeto', 'local': os.path.join('Projetos', p)})
        entrada['memoria'] = memoria[:300] if memoria else ''
        resultados.append(entrada)
    return resultados


# ---------------------------------------------------------------------------
# Detecção de desperdício (repetição, escopo, atalho)
# ---------------------------------------------------------------------------
def detectar_desperdicio(pedido):
    analise = {'riscos': [], 'sugestoes': [], 'repeticao': {'possivel': False, 'fonte': ''}}
    state_path = os.path.join(BASE, 'runtime', 'state.json')
    try:
        if os.path.exists(state_path):
            with open(state_path, encoding='utf-8') as f:
                state = json.load(f)
            ultima = str(state.get('last_task', ''))
            if ultima and ultima.strip():
                pedido_n = set(pedido.lower())
                ultima_n = set(ultima.lower())
                n = max(len(pedido_n) | len(ultima_n), 1)
                if len(pedido_n & ultima_n) / n > 0.55:
                    analise['repeticao'] = {'possivel': True, 'fonte': f'last_task (runtime/state.json): "{ultima[:80]}"'}
    except (OSError, ValueError):
        pass
    conceitos = _extrair_conceitos(pedido)
    for c in conceitos:
        if str(c).startswith(('skill:', 'script:')):
            analise['sugestoes'].append(f'Usar a capacidade existente "{c}" em vez de reinventar')
    analise['riscos'] = _riscos_desperdicio(pedido, {'acoes': _extrair_acoes(pedido)})
    return analise


# ---------------------------------------------------------------------------
# Refino com LLM (fail-soft, agnóstico de fornecedor)
# Primária: LLM padrão do opencode (mesma da sessão, sem chave extra).
# Backup: NVIDIA → OpenAI → Anthropic (chaves de scripts/.env). Quando a
# primária não responde, o backup entra em ação — resiliência.
# ---------------------------------------------------------------------------
def _modelo_opencode():
    """Modelo da LLM do opencode usado no refino. Configurável, default = modelo da sessão."""
    return (os.environ.get('COMPREENSAO_MODELO_OPENCODE')
            or os.environ.get('LLM_MODEL')
            or 'opencode/big-pickle')


def _refinar_via_opencode(prompt, timeout=90):
    """Chama a LLM padrão do opencode via `opencode run` (headless). Fail-soft: '' em qualquer falha.

    Guarda de recursão: o agente headless carrega a Constituição e poderia chamar a
    própria tool `refinar_entendimento` (recursão). Um flag de ambiente quebra a cadeia
    no primeiro nível. Rodamos em cwd neutro (sem AGENTS.md) e ordenamos "sem ferramentas".
    """
    if os.environ.get('COMPREENSAO_EM_REFINO') == '1':
        return ''
    exe = shutil.which('opencode') or shutil.which('opencode.cmd') or shutil.which('opencode.exe')
    if not exe:
        return ''
    env = dict(os.environ)
    env['COMPREENSAO_EM_REFINO'] = '1'
    cwd = os.path.join(BASE, 'runtime', 'refino')
    try:
        os.makedirs(cwd, exist_ok=True)
        proc = subprocess.run(
            [exe, 'run', '--agent', 'compreensao-refino', '-m', _modelo_opencode(), '--format', 'json',
             prompt + ' Nao use nenhuma ferramenta. Responda somente em texto.'],
            capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace',
            env=env, cwd=cwd,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except (OSError, subprocess.TimeoutExpired):
        return ''
    if proc.returncode != 0:
        return ''
    texto = []
    for linha in proc.stdout.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            evt = json.loads(linha)
        except ValueError:
            continue
        if evt.get('type') == 'error':
            return ''
        if evt.get('type') == 'text':
            parte = evt.get('part', {}) or {}
            t = parte.get('text', '')
            if t:
                texto.append(t)
    return '\n'.join(texto).strip()


def _extrair_critica(texto):
    m = re.search(r'\{.*\}', texto, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except ValueError:
            pass
    return {'observacao': texto[:300]}


def _resolver_providers():
    """Devolve lista de (provedor, modelo_litellm, chave, api_base) na ordem de preferência (backups)."""
    providers = []
    modelo_nv = os.environ.get('COMPREENSAO_MODELO_NVIDIA', 'meta/llama-3.3-70b-instruct')
    if os.environ.get('NVIDIA_API_KEY'):
        providers.append(('nvidia', 'openai/' + modelo_nv, os.environ['NVIDIA_API_KEY'],
                          'https://integrate.api.nvidia.com/v1'))
    if os.environ.get('OPENAI_API_KEY'):
        providers.append(('openai', 'openai/gpt-4o-mini', os.environ['OPENAI_API_KEY'], None))
    if os.environ.get('ANTHROPIC_API_KEY'):
        providers.append(('anthropic', 'anthropic/claude-sonnet-4-5', os.environ['ANTHROPIC_API_KEY'], None))
    return providers


def refinar_com_llm(pedido, entendimento):
    """Chama a LLM do opencode (primária); se não responder, cai para os backups. Fail-soft."""
    _carregar_env()
    prompt = (
        'Você é o módulo de Compreensão de Pedidos do EcoSystemUmGrau. O usuário pediu: '
        f'"{pedido[:1000]}"\n\n'
        f'Entendimento preliminar (heurístico): {json.dumps(entendimento, ensure_ascii=False)}\n\n'
        'Responda APENAS com JSON: {"objetivo_corrigido": "...", "lacunas": [...], '
        '"melhorias": [...], "observacao": "..."}. '
        'Corrija erros de interpretação e aponte apenas o que faltou para transformar em ação.')
    # 1) LLM padrão do opencode — mesma da sessão, sem chave extra
    texto = _refinar_via_opencode(prompt)
    if texto:
        return {'usado': True, 'provedor': 'opencode', 'modelo': _modelo_opencode(),
                'critica': _extrair_critica(texto),
                'resumo': {'objetivo': entendimento.get('objetivo'), 'score': entendimento.get('score_entendimento')}}
    # 2) Backup: NVIDIA → OpenAI → Anthropic (litellm)
    providers = _resolver_providers()
    if not providers:
        return {'usado': False, 'motivo': 'LLM do opencode indisponível e nenhuma chave de backup (NVIDIA/OpenAI/Anthropic)'}
    try:
        import litellm
    except ImportError:
        return {'usado': False, 'motivo': 'opencode indisponível e litellm não instalado'}
    ultimo_erro = 'desconhecido'
    for provedor, modelo, chave, api_base in providers:
        try:
            kwargs = {'api_base': api_base} if api_base else {}
            resp = litellm.completion(
                model=modelo,
                messages=[{'role': 'user', 'content': prompt}],
                api_key=chave,
                max_tokens=500,
                timeout=25,
                **kwargs,
            )
            texto = resp['choices'][0]['message']['content']
            return {'usado': True, 'provedor': provedor, 'modelo': modelo,
                    'critica': _extrair_critica(texto),
                    'resumo': {'objetivo': entendimento.get('objetivo'), 'score': entendimento.get('score_entendimento')}}
        except Exception as e:
            ultimo_erro = f'{provedor}: {e}'
            continue
    return {'usado': False, 'motivo': f'opencode indisponível; falha nos backups ({ultimo_erro})'}


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
    entendimento['checklist'] = _checklist_entrega(pedido, entendimento)
    if refinar:
        entendimento['llm_refino'] = refinar_com_llm(pedido, entendimento)
    return entendimento


# ---------------------------------------------------------------------------
# Geração de spec (SDD) — formato specs/<componente>.spec.md
# Produz só texto (markdown); quem chama decide persistir via salvar_spec().
# ---------------------------------------------------------------------------
def _slug(texto, max_len=60):
    """kebab-case a partir de qualquer texto; fallback determinístico."""
    s = texto.strip().lower()
    s = ''.join(c for c in s if not (0x0300 <= ord(c) <= 0x036F))  # remove marcas (acentos)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = re.sub(r'-{2,}', '-', s)
    if not s:
        return 'componente'
    return s[:max_len].rstrip('-')


def _componente_para(pedido, entendimento):
    """Heurística de componente: script:/skill:/projeto → caminho; palavra 'script' sem
    prefixo → scripts/<slug>.py (caminho convencional do que será criado); senão slug do objetivo."""
    baixo = pedido.lower()
    if os.path.isdir(SCRIPTS):
        for c in sorted(entendimento.get('conceitos', []), key=len, reverse=True):
            if str(c).startswith('script:'):
                nome = str(c).split(':', 1)[1]
                caminho = os.path.join('scripts', nome + '.py')
                if os.path.exists(os.path.join(BASE, caminho)):
                    return caminho.replace(os.sep, '/')
            elif str(c).startswith('skill:'):
                nome = str(c).split(':', 1)[1]
                for dominio in (os.listdir(MCP_DIR) if os.path.isdir(MCP_DIR) else []):
                    caminho = os.path.join('mcp', dominio, 'habilidades', nome)
                    if os.path.isdir(os.path.join(BASE, caminho)):
                        return caminho.replace(os.sep, '/')
    for nome in (os.listdir(PROJETOS_DIR) if os.path.isdir(PROJETOS_DIR) else []):
        if nome.lower() in baixo:
            return os.path.join('Projetos', nome).replace(os.sep, '/')
    # Menção sem prefixo a tipo de componente conhecido → caminho convencional
    if 'script' in baixo:
        slug = _slug(entendimento.get('objetivo', pedido) or pedido)
        return os.path.join('scripts', slug + '.py').replace(os.sep, '/')
    return _slug(entendimento.get('objetivo', pedido) or pedido)


def spec_markdown(pedido, entendimento=None):
    """Gera o markdown de uma spec (SDD) a partir do entendimento do pedido."""
    if entendimento is None:
        entendimento = compreender(pedido)
    componente = _componente_para(pedido, entendimento)
    slug = _slug(os.path.splitext(os.path.basename(componente))[0])
    requisitos = [f"- {a['verbo']}: {a['objeto']}" for a in entendimento.get('acoes', [])[:6]] or \
        ["- _definir_ (ação explícita a derivar do objetivo)"]
    dependencias = [f"- `{c}`" for c in entendimento.get('conceitos', [])
                    if str(c).startswith(('script:', 'skill:'))] or ["- _nenhuma declarada_"]
    premissas = []
    if entendimento.get('julgamento'):
        premissas.append(f"- Entendimento julgado {entendimento['julgamento']} "
                         f"(score {entendimento.get('score_entendimento', 0)}/100)")
    if not premissas:
        premissas = ["- _a definir_"]
    criterios = [f"- [ ] {c}" for c in entendimento.get('criterios_sucesso', [])] or \
        ["- [ ] _critério observável de aceitação_"]
    riscos = [f"- {r.get('msg', '')} — nível {r.get('nivel', 'medio')}"
              for r in entendimento.get('riscos', [])] or ["- _nenhum risco declarado_"]
    restricoes = [f"- {r}" for r in entendimento.get('restricoes', [])] or ["- _nenhuma declarada_"]
    tags = ['compreensao', slug]
    return (
        "---\n"
        f"id: spec-{slug}\n"
        "versao: 0.1.0\n"
        "status: proposta\n"
        f"componente: {componente}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"data: {datetime.now().strftime('%Y-%m-%d')}\n"
        "---\n\n"
        f"# Spec — {slug}\n\n"
        "## Objetivo\n"
        f"{entendimento.get('objetivo', pedido)}\n\n"
        "## Requisitos\n"
        + "\n".join(requisitos) + "\n\n"
        "## Restrições\n"
        + "\n".join(restricoes) + "\n\n"
        "## Dependências\n"
        + "\n".join(dependencias) + "\n\n"
        "## Premissas\n"
        + "\n".join(premissas) + "\n\n"
        "## Entradas e Saídas\n"
        "- Entrada: _definir_\n"
        "- Saída: _definir_\n\n"
        "## Casos de Borda\n"
        "- _definir_ (condições-limite da análise, ver princípio do teste adversarial).\n\n"
        "## Critérios de Aceitação\n"
        + "\n".join(criterios) + "\n\n"
        "## Definition of Done\n"
        "- [ ] Requisito implementado\n"
        "- [ ] Testes executados e passando\n"
        "- [ ] Critérios de aceitação satisfeitos\n"
        "- [ ] Regressão verificada\n\n"
        "## Riscos\n"
        + "\n".join(riscos) + "\n\n"
        "## Testes Relacionados\n"
        "- _definir_ (testes que validam esta spec).\n"
    )


def salvar_spec(pedido, destino=None, entendimento=None):
    """Gera e persiste (escrita atômica) a spec em specs/<slug>.spec.md."""
    texto = spec_markdown(pedido, entendimento)
    componente = _componente_para(pedido, entendimento)
    slug = _slug(os.path.splitext(os.path.basename(componente))[0])
    if not destino:
        destino = os.path.join(SPECS_DIR, slug + '.spec.md')
    os.makedirs(os.path.dirname(destino) or SPECS_DIR, exist_ok=True)
    tmp = destino + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(texto)
    os.replace(tmp, destino)
    return {'arquivo': os.path.basename(destino),
            'caminho': os.path.relpath(destino, BASE).replace(os.sep, '/'),
            'escrita': True,
            'componente': componente}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description='Compreensão de Pedidos do EcoSystemUmGrau')
    parser.add_argument('pedido', nargs='*', default=[])
    parser.add_argument('--refinar', action='store_true', help='refina com a LLM disponível (fail-soft)')
    parser.add_argument('--json', action='store_true', help='saída JSON')
    parser.add_argument('--spec', action='store_true', help='gera e salva a spec em specs/ (escrita atômica)')
    parser.add_argument('--checklist', action='store_true', help='exibe o checklist de entrega + status de veto do pedido')
    args = parser.parse_args()
    if not args.pedido:
        pedido = sys.stdin.read().strip() if not sys.stdin.isatty() else ''
    else:
        pedido = ' '.join(args.pedido)
    if not pedido:
        print(json.dumps({'erro': 'nenhum pedido informado'}, ensure_ascii=False))
        return 1
    out = compreender(pedido, refinar=args.refinar)
    if args.spec:
        out['spec'] = salvar_spec(pedido, entendimento=out)
    if args.checklist:
        cl = out.get('checklist', {})
        linhas = [f"STATUS: {cl.get('status')}", "CHECKLIST:"]
        linhas += [f"  - {i}" for i in cl.get('itens', [])]
        linhas += [f"VETO ({v['regra']}): {v['detalhe']}" for v in cl.get('vetos', [])]
        print("\n".join(linhas))
        return 0
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else
          f"OBJETIVO: {out['objetivo']}\nSCORE: {out['score_entendimento']} ({out['julgamento']})\n"
          f"AÇÕES: {len(out['acoes'])} | AMBIGUIDADES: {len(out['ambiguidades'])} | CONCEITOS: {len(out['conceitos'])}"
          + (f"\nSPEC: {out['spec']['caminho']}" if args.spec else ""))
    return 0


if __name__ == '__main__':
    _carregar_env()
    sys.exit(main())
