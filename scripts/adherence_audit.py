#!/usr/bin/env python3
"""
adherence_audit.py — Auditoria de Aderência à Constituição do EcoSystemUmGrau

Gera métricas PRECISAS de conformidade das regras constitucionais na prática.
Executa em @sync e antes de entregas relevantes.

Métricas coletadas (baseadas em evidência objetiva):
- Gate Persistência: % commits via persistencia.ps1 vs diretos (git log)
- Inventário Consultado: % arquivos NOVOS (git diff-filter=A) registrados no inventário
- Preflight por Entrega: % commits de entrega que rodaram preflight_check.py + preflight_etica.py ANTES
- Violações de Confiança: quebras registradas nas memórias (kind=erro + palavras-chave)
- Comunicação pt-BR + Formatação Simples: amostragem do runtime state
- Boot Completo: runtime/state.json tem projeto_ativo, objetivo, ultima_tarefa
- Aprendizado Registrado: arquivos em conhecimento/aprendizados/ vs tarefas estimadas
- @sync Executados: memórias com @sync + status sucesso
- Integridade Inventário: inventory_manager.py verify exit code
"""
import json
import sys
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
INVENTARIO = BASE / 'config' / 'inventario_estruturas.json'
RUNTIME_STATE = BASE / 'runtime' / 'state.json'
MEMORIES = BASE / 'conhecimento' / 'memoria' / 'memories.json'
APRENDIZADOS_DIR = BASE / 'conhecimento' / 'aprendizados'
PREFLIGHT_LOG = BASE / 'runtime' / 'preflight_executions.log'  # log de execuções de preflight

DEFAULT_DAYS = 30

# Thresholds para consequências no @sync
THRESHOLDS = {
    'gate_persistencia_min': 1.0,       # % mínimo commits via gate (temporário: 1% durante transição imediata, subir para 20% após 7 dias, 90% após 30 dias)
    'inventario_consultas_min': 80.0,   # % mínimo arquivos novos registrados
    'preflight_entregas_min': 90.0,     # % mínimo entregas com preflight
    'boot_completo_min': 100.0,         # boot deve ser 100%
    'comunicacao_ptbr_min': 95.0,       # pt-BR + formatação simples
}

def run_cmd(cmd: List[str], cwd: Path = BASE, timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'timeout'
    except Exception as e:
        return -1, '', str(e)

def parse_git_log(days: int) -> List[Dict[str, Any]]:
    """Parse git log para analisar commits."""
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    rc, out, err = run_cmd(['git', 'log', f'--since={since}', '--pretty=format:%H|%an|%ad|%s', '--date=short'])
    if rc != 0:
        return []
    commits = []
    for line in out.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0],
                'author': parts[1],
                'date': parts[2],
                'message': parts[3]
            })
    return commits

def get_arquivos_adicionados(days: int) -> List[str]:
    """Retorna lista de arquivos ADICIONADOS (novos) no período via git diff --diff-filter=A."""
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    # Compara HEAD com commit de {days} dias atrás
    rc, out, err = run_cmd(['git', 'diff', '--name-only', '--diff-filter=A', f'HEAD@{{{days} days ago}}', 'HEAD'])
    if rc != 0:
        # Fallback: arquivos em commits com mensagem de criação
        rc2, out2, _ = run_cmd(['git', 'log', f'--since={since}', '--pretty=format:', '--name-only', '--diff-filter=A'])
        if rc2 == 0:
            return [f.strip() for f in out2.strip().split('\n') if f.strip()]
        return []
    return [f.strip() for f in out.strip().split('\n') if f.strip()]

def carregar_inventario_ids() -> Set[str]:
    """Carrega todos os IDs registrados no inventário (flat set)."""
    ids = set()
    if not INVENTARIO.exists():
        return ids
    with open(INVENTARIO, encoding='utf-8') as f:
        inv = json.load(f)
    
    for chave, valor in inv.items():
        if chave in ('versao', 'atualizado_em', 'descricao'):
            continue
        if isinstance(valor, list):
            for item in valor:
                if isinstance(item, dict) and 'id' in item:
                    ids.add(item['id'])
                elif isinstance(item, str):
                    ids.add(item)
        elif isinstance(valor, dict):
            # mcp_habilidades: {dominio: [ids]}
            for habs in valor.values():
                for h in habs:
                    ids.add(h)
    return ids

def arquivo_relacionado_a_estrutura(arquivo: str) -> bool:
    """Heurística: o arquivo corresponde a uma 'estrutura' rastreável no inventário?"""
    # Ignora arquivos de configuração de IDE, docs, logs, etc.
    ignorar_padroes = [
        '.git/', '.vscode/', '.idea/', '__pycache__/', 'node_modules/',
        '_legado/', 'backups/',
        '.log', '.txt', '.md', '.json', '.yaml', '.yml', '.toml', '.ini',
        'runtime/', 'conhecimento/aprendizados/', 'conhecimento/memoria/',
        'screenshots/', 'assets/', 'docs/', 'specs/',
        'test_', '_test.', 'test-', '-test.', '.bak', '.tmp'
    ]
    arq_lower = arquivo.lower()
    for pad in ignorar_padroes:
        if pad in arq_lower:
            return False
    
    # Considera estruturas: scripts/, config/agents/, config/*.jsonc, mcp/*/habilidades/*/ (diretório da skill, não arquivos internos)
    estrutura_dirs = ['scripts/', 'config/agents/', 'config/']
    if any(arq_lower.startswith(d) for d in estrutura_dirs):
        return True
    
    # MCP: considera apenas o diretório da skill (mcp/*/habilidades/<skill>/), não arquivos .py internos
    if arq_lower.startswith('mcp/') and '/habilidades/' in arq_lower:
        # Verifica se é o diretório da skill (termina com / ou é um diretório)
        partes = arq_lower.split('/habilidades/')
        if len(partes) == 2:
            resto = partes[1]
            # Se tem mais de um nível depois de /habilidades/, é arquivo interno da skill
            if resto.count('/') >= 1:
                return False  # Arquivo interno da skill, não estrutura separada
            return True  # É o diretório da skill em si
    
    return False

def check_gate_persistencia(commits: List[Dict]) -> Dict[str, Any]:
    """Verifica % de commits via persistencia.ps1 vs diretos."""
    total = len(commits)
    if total == 0:
        return {'total': 0, 'via_gate': 0, 'diretos': 0, 'percentual_gate': 100.0}
    
    via_gate = 0
    diretos = 0
    for c in commits:
        msg = c['message'].lower()
        if ('persistencia.ps1' in msg or 'gate persist' in msg or 'run-sync' in msg or 
            '[gate]' in msg or 'gate]' in msg):
            via_gate += 1
        else:
            diretos += 1
    
    return {
        'total': total,
        'via_gate': via_gate,
        'diretos': diretos,
        'percentual_gate': round((via_gate / total) * 100, 1) if total > 0 else 100.0
    }

def check_inventario_consultas(days: int) -> Dict[str, Any]:
    """
    Métrica PRECISA: % de arquivos NOVOS (git diff-filter=A) que estão registrados no inventário.
    """
    arquivos_novos = get_arquivos_adicionados(days)
    ids_inventario = carregar_inventario_ids()
    
    estruturas_novas = []
    estruturas_registradas = 0
    
    for arq in arquivos_novos:
        if not arquivo_relacionado_a_estrutura(arq):
            continue
        estruturas_novas.append(arq)
        # Tenta extrair ID do caminho do arquivo
        # Ex: scripts/meu_script.py -> meu_script
        #     config/agents/00-novo.md -> 00-novo
        #     mcp/desenvolvimento/habilidades/minha-hab/ -> minha-hab
        nome_base = Path(arq).stem
        if nome_base in ids_inventario:
            estruturas_registradas += 1
        else:
            # Tenta variações
            for id_inv in ids_inventario:
                if id_inv in nome_base or nome_base in id_inv:
                    estruturas_registradas += 1
                    break
    
    total = len(estruturas_novas)
    return {
        'arquivos_novos_totais': len(arquivos_novos),
        'estruturas_novas_detectadas': total,
        'estruturas_registradas_no_inventario': estruturas_registradas,
        'estruturas_nao_registradas': total - estruturas_registradas,
        'percentual': round((estruturas_registradas / total) * 100, 1) if total > 0 else 100.0,
        'detalhes_nao_registrados': [e for e in estruturas_novas if Path(e).stem not in ids_inventario][:10]
    }

def get_preflight_executions(days: int) -> Dict[str, List[datetime]]:
    """Lê log de execuções de preflight (se existir)."""
    execucoes = {'tecnico': [], 'etico': []}
    if PREFLIGHT_LOG.exists():
        cutoff = datetime.now() - timedelta(days=days)
        with open(PREFLIGHT_LOG, encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    dt = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    if dt >= cutoff:
                        if entry.get('tipo') == 'tecnico':
                            execucoes['tecnico'].append(dt)
                        elif entry.get('tipo') == 'etico':
                            execucoes['etico'].append(dt)
                except:
                    pass
    return execucoes

def check_preflight_por_entrega(days: int) -> Dict[str, Any]:
    """
    Métrica PRECISA: % de commits de ENTREGA que executaram preflight técnico + ético ANTES.
    Entrega = commit com mensagem feat/fix/refactor/impl/entrega/delivery que toca código de produção.
    """
    commits = parse_git_log(days)
    preflight_execs = get_preflight_executions(days)
    
    # Identifica commits de entrega
    entregas = []
    for c in commits:
        msg = c['message'].lower()
        if any(kw in msg for kw in ['feat:', 'fix:', 'refactor:', 'impl:', 'entrega', 'delivery:', 'release:']):
            # Verifica se toca arquivos de produção (não testes, não docs, não configs apenas)
            rc, out, _ = run_cmd(['git', 'show', '--name-only', '--pretty=format:', c['hash']])
            if rc == 0:
                arquivos = [f.strip() for f in out.strip().split('\n') if f.strip()]
                if any(arquivo_relacionado_a_estrutura(a) for a in arquivos):
                    try:
                        commit_dt = datetime.strptime(c['date'], '%Y-%m-%d')
                        entregas.append({'hash': c['hash'], 'date': commit_dt, 'message': c['message']})
                    except:
                        pass
    
    total_entregas = len(entregas)
    if total_entregas == 0:
        return {
            'entregas_total': 0,
            'entregas_com_preflight_tecnico': 0,
            'entregas_com_preflight_etico': 0,
            'entregas_com_ambos': 0,
            'percentual_tecnico': 100.0,
            'percentual_etico': 100.0,
            'percentual_ambos': 100.0
        }
    
    # Para cada entrega, verifica se houve preflight técnico e ético ANTES do commit
    com_tecnico = 0
    com_etico = 0
    com_ambos = 0
    
    for e in entregas:
        has_tecnico = any(p < e['date'] for p in preflight_execs['tecnico'])
        has_etico = any(p < e['date'] for p in preflight_execs['etico'])
        if has_tecnico:
            com_tecnico += 1
        if has_etico:
            com_etico += 1
        if has_tecnico and has_etico:
            com_ambos += 1
    
    return {
        'entregas_total': total_entregas,
        'entregas_com_preflight_tecnico': com_tecnico,
        'entregas_com_preflight_etico': com_etico,
        'entregas_com_ambos': com_ambos,
        'percentual_tecnico': round((com_tecnico / total_entregas) * 100, 1),
        'percentual_etico': round((com_etico / total_entregas) * 100, 1),
        'percentual_ambos': round((com_ambos / total_entregas) * 100, 1),
        'preflight_execucoes_tecnico': len(preflight_execs['tecnico']),
        'preflight_execucoes_etico': len(preflight_execs['etico'])
    }

def check_violacoes_confianca(days: int) -> Dict[str, Any]:
    violacoes = []
    if MEMORIES.exists():
        with open(MEMORIES, encoding='utf-8') as f:
            memories = json.load(f)
        cutoff = datetime.now() - timedelta(days=days)
        for m in memories:
            if m.get('kind') == 'erro':
                content = json.dumps(m).lower()
                if any(kw in content for kw in ['quebra de confiança', 'quebra confiança', 'violação', 'violacao', 'trust break', 'confiança quebrada']):
                    try:
                        m_date = datetime.fromisoformat(m.get('created_at', '').replace('Z', '+00:00'))
                        if m_date >= cutoff:
                            violacoes.append({
                                'titulo': m.get('task', ''),
                                'resumo': m.get('summary', '')[:200],
                                'data': m.get('created_at', '')
                            })
                    except:
                        pass
    return {
        'total_periodo': len(violacoes),
        'detalhes': violacoes[:10]
    }

def check_comunicacao_ptbr() -> Dict[str, Any]:
    ptbr_ok = 0
    ptbr_total = 0
    formatacao_ok = 0
    formatacao_total = 0
    
    if RUNTIME_STATE.exists():
        with open(RUNTIME_STATE, encoding='utf-8') as f:
            state = json.load(f)
        textos = []
        if state.get('last_task'):
            textos.append(state['last_task'])
        if state.get('notes'):
            textos.extend(state['notes'] if isinstance(state['notes'], list) else [state['notes']])
        
        for texto in textos:
            ptbr_total += 1
            formatacao_total += 1
            ptbr_indicators = ['o ', 'a ', 'e ', 'de ', 'do ', 'da ', 'em ', 'para ', 'com ', 'por ', 'que ', 'como ', 'mais ', 'muito ', 'bem ', 'já ', 'não ', 'sim ', 'este ', 'essa ', 'isso ', 'aquilo ']
            if any(ind in texto.lower() for ind in ptbr_indicators):
                ptbr_ok += 1
            if not re.search(r'(#{1,6}\s|\*{2,}|\|.*\||\d+\.\s|\[.*\]\(.*\))', texto):
                formatacao_ok += 1
    
    return {
        'amostras_verificadas': ptbr_total,
        'pt_br_ok': ptbr_ok,
        'percentual_pt_br': round((ptbr_ok / ptbr_total) * 100, 1) if ptbr_total > 0 else 100.0,
        'formatacao_simples_ok': formatacao_ok,
        'percentual_formatacao': round((formatacao_ok / formatacao_total) * 100, 1) if formatacao_total > 0 else 100.0,
        'percentual_combinado': round(((ptbr_ok + formatacao_ok) / max(ptbr_total + formatacao_total, 1)) * 100, 1)
    }

def check_boot_completo() -> Dict[str, Any]:
    boot_ok = 0
    boot_total = 0
    if RUNTIME_STATE.exists():
        with open(RUNTIME_STATE, encoding='utf-8') as f:
            state = json.load(f)
        required = ['projeto_ativo', 'objetivo', 'ultima_tarefa']
        boot_total = 1
        if all(state.get(k) for k in required):
            boot_ok = 1
    return {
        'sessoes_verificadas': boot_total,
        'boot_completo': boot_ok,
        'percentual': 100.0 if boot_ok == boot_total else 0.0,
        'campos_presentes': {k: bool(RUNTIME_STATE.exists() and json.load(open(RUNTIME_STATE, encoding='utf-8')).get(k)) for k in required} if RUNTIME_STATE.exists() else {}
    }

def check_aprendizado_registrado(days: int) -> Dict[str, Any]:
    tarefas_com_aprendizado = 0
    if APRENDIZADOS_DIR.exists():
        cutoff = datetime.now() - timedelta(days=days)
        for f in APRENDIZADOS_DIR.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime >= cutoff:
                    tarefas_com_aprendizado += 1
            except:
                pass
    
    commits = parse_git_log(days)
    tarefas_total = len([c for c in commits if any(kw in c['message'].lower() for kw in ['feat', 'fix', 'add', 'create', 'implement', 'refactor'])])
    
    percentual = min(100.0, round((tarefas_com_aprendizado / max(tarefas_total, 1)) * 100, 1))
    
    return {
        'tarefas_com_aprendizado': tarefas_com_aprendizado,
        'tarefas_estimadas': max(tarefas_total, tarefas_com_aprendizado),
        'percentual': percentual
    }

def check_sync_executados(days: int) -> Dict[str, Any]:
    sync_ok = 0
    sync_total = 0
    if MEMORIES.exists():
        with open(MEMORIES, encoding='utf-8') as f:
            memories = json.load(f)
        cutoff = datetime.now() - timedelta(days=days)
        for m in memories:
            title = m.get('task', '').lower()
            summary = m.get('summary', '').lower()
            if '@sync' in title or 'sincronização' in summary or ('sync' in title and 'sincron' in summary):
                sync_total += 1
                try:
                    m_date = datetime.fromisoformat(m.get('created_at', '').replace('Z', '+00:00'))
                    if m_date >= cutoff:
                        if any(kw in summary for kw in ['ok', 'sucesso', 'concluído', 'concluido', 'consistente']):
                            sync_ok += 1
                except:
                    pass
    return {
        'sync_registrados': sync_total,
        'sync_sucesso': sync_ok,
        'percentual': round((sync_ok / sync_total) * 100, 1) if sync_total > 0 else 100.0
    }

def check_inventario_integridade() -> Dict[str, Any]:
    rc, out, err = run_cmd([sys.executable, 'scripts/inventory_manager.py', 'verify'])
    return {
        'exit_code': rc,
        'output': out.strip(),
        'erro': err.strip() if err else None,
        'ok': rc == 0
    }

def avaliar_thresholds(metricas: Dict[str, Any]) -> Dict[str, Any]:
    """Avalia se métricas atendem aos thresholds mínimos para @sync passar."""
    resultados = {}
    todos_ok = True
    
    # Gate Persistência
    gp = metricas['gate_persistencia']['percentual_gate']
    resultados['gate_persistencia'] = {
        'valor': gp,
        'threshold': THRESHOLDS['gate_persistencia_min'],
        'ok': gp >= THRESHOLDS['gate_persistencia_min']
    }
    if not resultados['gate_persistencia']['ok']:
        todos_ok = False
    
    # Inventário Consultas
    ic = metricas['inventario_consultas']['percentual']
    resultados['inventario_consultas'] = {
        'valor': ic,
        'threshold': THRESHOLDS['inventario_consultas_min'],
        'ok': ic >= THRESHOLDS['inventario_consultas_min']
    }
    if not resultados['inventario_consultas']['ok']:
        todos_ok = False
    
    # Preflight por Entrega (ambos)
    pe = metricas['preflight_por_entrega']['percentual_ambos']
    resultados['preflight_entregas'] = {
        'valor': pe,
        'threshold': THRESHOLDS['preflight_entregas_min'],
        'ok': pe >= THRESHOLDS['preflight_entregas_min'] if metricas['preflight_por_entrega']['entregas_total'] > 0 else True
    }
    if not resultados['preflight_entregas']['ok']:
        todos_ok = False
    
    # Boot Completo
    bc = metricas['boot_completo']['percentual']
    resultados['boot_completo'] = {
        'valor': bc,
        'threshold': THRESHOLDS['boot_completo_min'],
        'ok': bc >= THRESHOLDS['boot_completo_min']
    }
    if not resultados['boot_completo']['ok']:
        todos_ok = False
    
    # Comunicação pt-BR + Formatação
    cb = metricas['comunicacao_ptbr']['percentual_combinado']
    resultados['comunicacao_ptbr'] = {
        'valor': cb,
        'threshold': THRESHOLDS['comunicacao_ptbr_min'],
        'ok': cb >= THRESHOLDS['comunicacao_ptbr_min']
    }
    if not resultados['comunicacao_ptbr']['ok']:
        todos_ok = False
    
    return {
        'todos_ok': todos_ok,
        'detalhes': resultados,
        'thresholds_usados': THRESHOLDS
    }

def gerar_relatorio(days: int = DEFAULT_DAYS) -> Dict[str, Any]:
    print(f'[INFO] Gerando auditoria de aderência (últimos {days} dias)...')
    
    relatorio = {
        'metadata': {
            'gerado_em': datetime.now().isoformat(),
            'periodo_dias': days,
            'versao_constituicao': '1.3'
        },
        'metricas': {
            'gate_persistencia': check_gate_persistencia(parse_git_log(days)),
            'inventario_consultas': check_inventario_consultas(days),
            'preflight_por_entrega': check_preflight_por_entrega(days),
            'violacoes_confianca': check_violacoes_confianca(days),
            'comunicacao_ptbr': check_comunicacao_ptbr(),
            'boot_completo': check_boot_completo(),
            'aprendizado_registrado': check_aprendizado_registrado(days),
            'sync_executados': check_sync_executados(days),
            'inventario_integridade': check_inventario_integridade()
        }
    }
    
    # Avaliação de thresholds (consequências)
    relatorio['thresholds'] = avaliar_thresholds(relatorio['metricas'])
    
    # Score geral (média ponderada)
    pesos = {
        'gate_persistencia': 0.20,
        'inventario_consultas': 0.15,
        'preflight_por_entrega': 0.15,
        'violacoes_confianca': 0.15,
        'comunicacao_ptbr': 0.10,
        'boot_completo': 0.10,
        'aprendizado_registrado': 0.10,
        'sync_executados': 0.05
    }
    
    scores = {}
    for key, peso in pesos.items():
        m = relatorio['metricas'][key]
        if key == 'gate_persistencia':
            scores[key] = m['percentual_gate']
        elif key == 'inventario_consultas':
            scores[key] = m['percentual']
        elif key == 'preflight_por_entrega':
            scores[key] = m['percentual_ambos'] if m['entregas_total'] > 0 else 100.0
        elif key == 'violacoes_confianca':
            scores[key] = max(0, 100 - m['total_periodo'] * 10)
        elif key == 'comunicacao_ptbr':
            scores[key] = m['percentual_combinado']
        elif key == 'boot_completo':
            scores[key] = m['percentual']
        elif key == 'aprendizado_registrado':
            scores[key] = m['percentual']
        elif key == 'sync_executados':
            scores[key] = m['percentual']
    
    score_geral = sum(scores[k] * pesos[k] for k in pesos)
    relatorio['score_geral'] = round(score_geral, 1)
    relatorio['scores_detalhados'] = {k: round(v, 1) for k, v in scores.items()}
    
    if score_geral >= 90:
        relatorio['classificacao'] = 'EXCELENTE'
    elif score_geral >= 75:
        relatorio['classificacao'] = 'BOM'
    elif score_geral >= 60:
        relatorio['classificacao'] = 'ATENCAO'
    else:
        relatorio['classificacao'] = 'CRITICO'
    
    # Status @sync (baseado em thresholds, não apenas score)
    relatorio['sync_status'] = 'PASS' if relatorio['thresholds']['todos_ok'] else 'FAIL'
    
    return relatorio

def imprimir_relatorio(relatorio: Dict[str, Any]) -> None:
    m = relatorio['metricas']
    th = relatorio['thresholds']
    print('\n' + '='*70)
    print('RELATÓRIO DE ADERÊNCIA À CONSTITUIÇÃO v1.3 — MÉTRICAS PRECISAS')
    print('='*70)
    print(f"Gerado em: {relatorio['metadata']['gerado_em'][:19].replace('T', ' ')}")
    print(f"Período: {relatorio['metadata']['periodo_dias']} dias")
    print(f"Score Geral: {relatorio['score_geral']}/100 — {relatorio['classificacao']}")
    print(f"@sync Status: {relatorio['sync_status']} (thresholds: {'OK' if th['todos_ok'] else 'FALHA'})")
    print('-'*70)
    
    for nome, label, threshold_key in [
        ('gate_persistencia', 'Gate Persistência (commits via gate)', 'gate_persistencia_min'),
        ('inventario_consultas', 'Inventário: Estruturas Novas Registradas', 'inventario_consultas_min'),
        ('preflight_por_entrega', 'Preflight por Entrega (técnico + ético antes)', 'preflight_entregas_min'),
        ('violacoes_confianca', 'Violações de Confiança (menos é melhor)', None),
        ('comunicacao_ptbr', 'Comunicação pt-BR + Formatação Simples', 'comunicacao_ptbr_min'),
        ('boot_completo', 'Boot Completo do Runtime', 'boot_completo_min'),
        ('aprendizado_registrado', 'Aprendizado Registrado por Tarefa', None),
        ('sync_executados', '@sync Executados com Sucesso', None)
    ]:
        met = m[nome]
        score = relatorio['scores_detalhados'][nome]
        th_info = th['detalhes'].get(nome, {}) if nome in th['detalhes'] else {}
        
        if nome == 'gate_persistencia':
            status = '✓' if th_info.get('ok', True) else '✗'
            print(f"  {status} {label}: {score}% ({met['via_gate']}/{met['total']} via gate, threshold: {THRESHOLDS[threshold_key]}%)")
        elif nome == 'inventario_consultas':
            status = '✓' if th_info.get('ok', True) else '✗'
            print(f"  {status} {label}: {score}% ({met['estruturas_registradas_no_inventario']}/{met['estruturas_novas_detectadas']} registradas, threshold: {THRESHOLDS[threshold_key]}%)")
            if met['detalhes_nao_registrados']:
                print(f"      Não registrados: {', '.join([Path(e).name for e in met['detalhes_nao_registrados'][:5]])}")
        elif nome == 'preflight_por_entrega':
            status = '✓' if th_info.get('ok', True) else '✗'
            print(f"  {status} {label}: {score}% ({met['entregas_com_ambos']}/{met['entregas_total']} com ambos, threshold: {THRESHOLDS[threshold_key]}%)")
            print(f"      Técnico: {met['entregas_com_preflight_tecnico']}/{met['entregas_total']} ({met['percentual_tecnico']}%) | Ético: {met['entregas_com_preflight_etico']}/{met['entregas_total']} ({met['percentual_etico']}%)")
        elif nome == 'violacoes_confianca':
            print(f"  {label}: {score}% ({met['total_periodo']} violações no período)")
        elif nome == 'comunicacao_ptbr':
            status = '✓' if th_info.get('ok', True) else '✗'
            print(f"  {status} {label}: {score}% (pt-BR: {met['percentual_pt_br']}%, formatação: {met['percentual_formatacao']}%, threshold: {THRESHOLDS[threshold_key]}%)")
        elif nome == 'boot_completo':
            status = '✓' if th_info.get('ok', True) else '✗'
            print(f"  {status} {label}: {score}% (threshold: {THRESHOLDS[threshold_key]}%)")
        elif nome == 'aprendizado_registrado':
            print(f"  {label}: {score}% ({met['tarefas_com_aprendizado']}/{met['tarefas_estimadas']})")
        elif nome == 'sync_executados':
            print(f"  {label}: {score}% ({met['sync_sucesso']}/{met['sync_registrados']})")
    
    print('-'*70)
    print('INTEGRIDADE DO INVENTÁRIO:')
    inv = m['inventario_integridade']
    status = 'OK' if inv['ok'] else 'FALHA'
    print(f"  Status: {status}")
    if inv['output']:
        for line in inv['output'].split('\n'):
            print(f"    {line}")
    
    if m['violacoes_confianca']['detalhes']:
        print('-'*70)
        print('VIOLAÇÕES RECENTES:')
        for v in m['violacoes_confianca']['detalhes'][:5]:
            print(f"  - {v['data'][:10]}: {v['titulo']} — {v['resumo']}")
    
    # Resumo thresholds
    print('-'*70)
    print('THRESHOLDS (@sync consequences):')
    for k, v in th['detalhes'].items():
        status = 'PASS' if v['ok'] else 'FAIL'
        print(f"  {k}: {v['valor']}% (min: {v['threshold']}%) — {status}")

def main():
    days = DEFAULT_DAYS
    if len(sys.argv) > 1:
        if sys.argv[1] in ('-h', '--help'):
            print(__doc__)
            return
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    relatorio = gerar_relatorio(days)
    imprimir_relatorio(relatorio)
    
    # Salva JSON para histórico
    historico_dir = BASE / 'runtime' / 'auditoria_aderencia'
    historico_dir.mkdir(parents=True, exist_ok=True)
    arquivo = historico_dir / f"aderencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(f'\n[OK] Relatório salvo em: {arquivo}')
    
    # Exit code: 0=PASS, 1=ATENCAO, 2=CRITICO/FAIL thresholds
    if relatorio['sync_status'] == 'FAIL':
        sys.exit(2)
    elif relatorio['classificacao'] == 'CRITICO':
        sys.exit(2)
    elif relatorio['classificacao'] == 'ATENCAO':
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()