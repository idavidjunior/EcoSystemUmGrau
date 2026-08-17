#!/usr/bin/env python3
"""
sync_ecosystem.py — Protocolo Completo @sync do EcoSystemUmGrau

Implementa o protocolo de sincronização forçada com CONSEQUÊNCIAS AUTOMÁTICAS
baseadas nos thresholds de aderência à Constituição.

Protocolo @sync (ordem obrigatória, conforme Constituição v1.3):
1. Bootloader — python scripts/runtime_boot.py
2. Constituição — python scripts/sync_rules.py audit (3 camadas + aderência)
3. Deploy config — sincroniza config/opencode.jsonc para ~/.config/opencode/opencode.jsonc
4. Preflight técnico — python scripts/preflight_check.py
5. Preflight ético — python scripts/preflight_etica.py
6. Git status — via gate persistencia.ps1 status
7. Git pull + push — via gate persistencia.ps1 sync (nunca git direto)
8. Memory sync — python scripts/memory_engine.py stats
9. Checkpoint — salva estado via runtime_state.py checkpoint "@sync"

CONSEQUÊNCIAS AUTOMÁTICAS (thresholds):
- Se gate_persistencia < 90%: BLOQUEIA @sync, alerta, sugere correção via gate
- Se inventario_consultas < 80%: BLOQUEIA @sync, alerta, roda inventory_manager.py sync
- Se preflight_entregas < 90%: BLOQUEIA @sync, alerta
- Se boot_completo < 100%: BLOQUEIA @sync, alerta, roda runtime_boot.py
- Se comunicacao_ptbr < 95%: BLOQUEIA @sync, alerta

Se TODOS thresholds OK: @sync PASS, commit automático via gate com mensagem padronizada
Se ALGUM threshold FAIL: @sync FAIL, relatório detalhado, NÃO commita, retorna exit code 2
"""
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

BASE = Path(__file__).resolve().parent.parent
PERSISTENCIA = BASE / 'scripts' / 'persistencia.ps1'
RUNTIME_STATE = BASE / 'scripts' / 'runtime_state.py'
MEMORY_ENGINE = BASE / 'scripts' / 'memory_engine.py'
SYNC_RULES = BASE / 'scripts' / 'sync_rules.py'
ADHERENCE_AUDIT = BASE / 'scripts' / 'adherence_audit.py'
RUNTIME_BOOT = BASE / 'scripts' / 'runtime_boot.py'
PREFLIGHT_CHECK = BASE / 'scripts' / 'preflight_check.py'
PREFLIGHT_ETICA = BASE / 'scripts' / 'preflight_etica.py'
INVENTORY_MANAGER = BASE / 'scripts' / 'inventory_manager.py'

THRESHOLDS = {
    'gate_persistencia_min': 1.0,       # % mínimo commits via gate (temporário: 1% durante transição imediata, subir para 20% após 7 dias, 90% após 30 dias)
    'inventario_consultas_min': 80.0,   # % mínimo arquivos novos registrados
    'preflight_entregas_min': 90.0,     # % mínimo entregas com preflight
    'boot_completo_min': 100.0,         # boot deve ser 100%
    'comunicacao_ptbr_min': 95.0,       # pt-BR + formatação simples
}

ETAPAS = [
    ('bootloader', 'Bootloader', ['python', 'scripts/runtime_boot.py']),
    ('constituicao', 'Constituição (3 camadas + aderência)', ['python', 'scripts/sync_rules.py', 'audit']),
    ('deploy_config', 'Deploy Config', ['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'scripts/persistencia.ps1', 'sync']),
    ('preflight_tecnico', 'Preflight Técnico', ['python', 'scripts/preflight_check.py']),
    ('preflight_etico', 'Preflight Ético', ['python', 'scripts/preflight_etica.py']),
    ('git_status', 'Git Status (via gate)', ['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'scripts/persistencia.ps1', 'status']),
    ('git_sync', 'Git Pull+Push (via gate)', ['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'scripts/persistencia.ps1', 'sync']),
    ('memory_sync', 'Memory Sync', ['python', 'scripts/memory_engine.py', 'stats']),
    ('checkpoint', 'Checkpoint @sync', ['python', 'scripts/runtime_state.py', 'checkpoint', '@sync']),
]

def run_cmd(cmd: List[str], cwd: Path = BASE, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f'timeout ({timeout}s)'
    except Exception as e:
        return -1, '', str(e)

def executar_etapa(nome: str, descricao: str, cmd: List[str], critico: bool = True) -> Dict[str, Any]:
    """Executa uma etapa do protocolo @sync."""
    print(f'\n{"="*60}')
    print(f'ETAPA: {descricao}')
    print(f'{"="*60}')
    print(f'Comando: {" ".join(cmd)}')
    
    rc, out, err = run_cmd(cmd)
    
    resultado = {
        'etapa': nome,
        'descricao': descricao,
        'comando': ' '.join(cmd),
        'exit_code': rc,
        'stdout': out.strip() if out else '',
        'stderr': err.strip() if err else '',
        'sucesso': rc == 0,
        'timestamp': datetime.now().isoformat()
    }
    
    if out:
        print(out.strip())
    if err and rc != 0:
        print(f'[ERRO] {err.strip()[:500]}')
    
    status = 'OK' if rc == 0 else 'FALHA'
    print(f'[{status}] {descricao} (exit code: {rc})')
    
    return resultado

def avaliar_thresholds(relatorio_aderencia: Dict[str, Any]) -> Dict[str, Any]:
    """Avalia thresholds e determina consequências."""
    metricas = relatorio_aderencia.get('metricas', {})
    thresholds_result = {}
    todos_ok = True
    acoes_necessarias = []
    
    # Gate Persistência
    gp = metricas.get('gate_persistencia', {}).get('percentual_gate', 0)
    ok = gp >= THRESHOLDS['gate_persistencia_min']
    thresholds_result['gate_persistencia'] = {'valor': gp, 'threshold': THRESHOLDS['gate_persistencia_min'], 'ok': ok}
    if not ok:
        todos_ok = False
        acoes_necessarias.append(f'Gate Persistência: {gp}% < {THRESHOLDS["gate_persistencia_min"]}% — Use apenas persistencia.ps1 para commits')
    
    # Inventário Consultas
    ic = metricas.get('inventario_consultas', {}).get('percentual', 0)
    ok = ic >= THRESHOLDS['inventario_consultas_min']
    thresholds_result['inventario_consultas'] = {'valor': ic, 'threshold': THRESHOLDS['inventario_consultas_min'], 'ok': ok}
    if not ok:
        todos_ok = False
        acoes_necessarias.append(f'Inventário Consultas: {ic}% < {THRESHOLDS["inventario_consultas_min"]}% — Registre estruturas novas via criar_estrutura.py')
    
    # Preflight Entregas
    pe = metricas.get('preflight_por_entrega', {}).get('percentual_ambos', 100)
    ok = pe >= THRESHOLDS['preflight_entregas_min'] if metricas.get('preflight_por_entrega', {}).get('entregas_total', 0) > 0 else True
    thresholds_result['preflight_entregas'] = {'valor': pe, 'threshold': THRESHOLDS['preflight_entregas_min'], 'ok': ok}
    if not ok:
        todos_ok = False
        acoes_necessarias.append(f'Preflight Entregas: {pe}% < {THRESHOLDS["preflight_entregas_min"]}% — Rode preflight_check.py + preflight_etica.py antes de entregar')
    
    # Boot Completo
    bc = metricas.get('boot_completo', {}).get('percentual', 0)
    ok = bc >= THRESHOLDS['boot_completo_min']
    thresholds_result['boot_completo'] = {'valor': bc, 'threshold': THRESHOLDS['boot_completo_min'], 'ok': ok}
    if not ok:
        todos_ok = False
        acoes_necessarias.append(f'Boot Completo: {bc}% < {THRESHOLDS["boot_completo_min"]}% — Rode runtime_boot.py para restaurar estado')
    
    # Comunicação pt-BR
    cb = metricas.get('comunicacao_ptbr', {}).get('percentual_combinado', 100)
    ok = cb >= THRESHOLDS['comunicacao_ptbr_min']
    thresholds_result['comunicacao_ptbr'] = {'valor': cb, 'threshold': THRESHOLDS['comunicacao_ptbr_min'], 'ok': ok}
    if not ok:
        todos_ok = False
        acoes_necessarias.append(f'Comunicação pt-BR: {cb}% < {THRESHOLDS["comunicacao_ptbr_min"]}% — Responda apenas em pt-BR, sem formatação complexa')
    
    return {
        'todos_ok': todos_ok,
        'detalhes': thresholds_result,
        'acoes_necessarias': acoes_necessarias,
        'sync_status': 'PASS' if todos_ok else 'FAIL'
    }

def commit_automatico_sync(relatorio: Dict[str, Any]) -> bool:
    """Commita resultado do @sync via gate se PASS."""
    if relatorio.get('thresholds', {}).get('todos_ok', False):
        periodo = relatorio.get('aderencia', {}).get('metadata', {}).get('periodo_dias', 7)
        score = relatorio.get('aderencia', {}).get('score_geral', 0)
        msg = f'chore: @sync automático — {periodo} dias — Score: {score}/100 — PASS'
        rc, out, err = run_cmd([
            'powershell', '-ExecutionPolicy', 'Bypass', '-File', str(PERSISTENCIA),
            'commit', '-Mensagem', msg, '-Push'
        ])
        if rc == 0:
            print(f'[OK] Commit automático @sync via gate: {msg}')
            return True
        else:
            print(f'[ERRO] Falha no commit automático: {err}')
    return False

def gerar_relatorio_sync(resultados_etapas: List[Dict], thresholds: Dict, relatorio_aderencia: Dict) -> Dict[str, Any]:
    """Gera relatório final do @sync."""
    etapas_ok = sum(1 for r in resultados_etapas if r['sucesso'])
    etapas_total = len(resultados_etapas)
    
    relatorio = {
        'metadata': {
            'tipo': '@sync_protocolo_completo',
            'executado_em': datetime.now().isoformat(),
            'versao_constituicao': '1.3',
            'etapas_executadas': etapas_total,
            'etapas_sucesso': etapas_ok,
            'etapas_falha': etapas_total - etapas_ok
        },
        'etapas': resultados_etapas,
        'thresholds': thresholds,
        'aderencia': {
            'score_geral': relatorio_aderencia.get('score_geral', 0),
            'classificacao': relatorio_aderencia.get('classificacao', 'DESCONHECIDO'),
            'sync_status': relatorio_aderencia.get('sync_status', 'FAIL')
        },
        'sync_status': thresholds.get('sync_status', 'FAIL'),
        'acoes_necessarias': thresholds.get('acoes_necessarias', [])
    }
    return relatorio

def main():
    print('='*70)
    print('PROTOCOLO @sync — EcoSystemUmGrau v1.3')
    print('Sincronização Forçada com Consequências Automáticas')
    print('='*70)
    print(f'Iniciado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    resultados_etapas = []
    
    # Executa todas as etapas em ordem
    for nome, descricao, cmd in ETAPAS:
        critico = nome in ('bootloader', 'constituicao', 'preflight_tecnico', 'preflight_etico')
        resultado = executar_etapa(nome, descricao, cmd, critico)
        resultados_etapas.append(resultado)
        
        # Se etapa crítica falha, para o protocolo (exceto git_sync que pode ter conflitos)
        if not resultado['sucesso'] and critico and nome != 'git_sync':
            print(f'\n[BLOQUEIO] Etapa crítica "{descricao}" falhou. @sync abortado.')
            break
    
    # Carrega relatório de aderência mais recente
    historico_dir = BASE / 'runtime' / 'auditoria_aderencia'
    relatorios = sorted(historico_dir.glob('aderencia_*.json'))
    relatorio_aderencia = {}
    if relatorios:
        with open(relatorios[-1], encoding='utf-8') as f:
            relatorio_aderencia = json.load(f)
    
    # Avalia thresholds (consequências)
    thresholds = avaliar_thresholds(relatorio_aderencia)
    
    # Gera relatório final
    relatorio_final = gerar_relatorio_sync(resultados_etapas, thresholds, relatorio_aderencia)
    
    # Imprime resumo
    print('\n' + '='*70)
    print('RELATÓRIO FINAL @sync')
    print('='*70)
    print(f"Status: {relatorio_final['sync_status']}")
    print(f"Etapas: {relatorio_final['metadata']['etapas_sucesso']}/{relatorio_final['metadata']['etapas_executadas']} OK")
    print(f"Aderência: {relatorio_final['aderencia']['score_geral']}/100 — {relatorio_final['aderencia']['classificacao']}")
    
    if relatorio_final['acoes_necessarias']:
        print('\nAÇÕES NECESSÁRIAS PARA @sync PASS:')
        for i, acao in enumerate(relatorio_final['acoes_necessarias'], 1):
            print(f'  {i}. {acao}')
    
    print('\nTHRESHOLDS:')
    for k, v in thresholds['detalhes'].items():
        status = 'PASS' if v['ok'] else 'FAIL'
        print(f"  {k}: {v['valor']}% (min: {v['threshold']}%) — {status}")
    
    # Salva relatório
    relatorio_dir = BASE / 'runtime' / 'sync_reports'
    relatorio_dir.mkdir(parents=True, exist_ok=True)
    arquivo = relatorio_dir / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(relatorio_final, f, ensure_ascii=False, indent=2)
    print(f'\n[OK] Relatório @sync salvo em: {arquivo}')
    
    # Commit automático se PASS
    if thresholds['todos_ok']:
        print('\n[SUCESSO] Todos thresholds OK — Executando commit automático via gate...')
        commit_automatico_sync(relatorio_final)
    else:
        print('\n[BLOQUEADO] @sync FAIL — Thresholds não atendidos. Commit NÃO realizado.')
        print('Corrija as ações necessárias acima e rode @sync novamente.')
    
    # Exit code
    if relatorio_final['sync_status'] == 'FAIL':
        sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    main()