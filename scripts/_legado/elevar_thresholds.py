#!/usr/bin/env python3
"""
elevar_thresholds.py — Elevação Automática de Thresholds do @sync

Este script verifica as memórias de elevação agendadas e atualiza os thresholds
nos arquivos de configuração (adherence_audit.py e sync_ecosystem.py)
quando a data de elevação chegou.

Uso:
  python scripts/elevar_thresholds.py check    # verifica elevações pendentes
  python scripts/elevar_thresholds.py apply    # aplica elevações vencidas
  python scripts/elevar_thresholds.py status   # mostra próximo threshold a elevar
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
MEMORIES = BASE / 'conhecimento' / 'memoria' / 'memories.json'
ADHERENCE_AUDIT = BASE / 'scripts' / 'adherence_audit.py'
SYNC_ECOSYSTEM = BASE / 'scripts' / 'sync_ecosystem.py'

# Mapeamento de threshold -> (arquivo, padrão regex de substituição)
THRESHOLD_CONFIG = {
    'gate_persistencia_min': [
        (ADHERENCE_AUDIT, r"'gate_persistencia_min':\s*[\d.]+", "'gate_persistencia_min': {valor}"),
        (SYNC_ECOSYSTEM, r"'gate_persistencia_min':\s*[\d.]+", "'gate_persistencia_min': {valor}"),
    ],
    'inventario_consultas_min': [
        (ADHERENCE_AUDIT, r"'inventario_consultas_min':\s*[\d.]+", "'inventario_consultas_min': {valor}"),
        (SYNC_ECOSYSTEM, r"'inventario_consultas_min':\s*[\d.]+", "'inventario_consultas_min': {valor}"),
    ],
    'preflight_entregas_min': [
        (ADHERENCE_AUDIT, r"'preflight_entregas_min':\s*[\d.]+", "'preflight_entregas_min': {valor}"),
        (SYNC_ECOSYSTEM, r"'preflight_entregas_min':\s*[\d.]+", "'preflight_entregas_min': {valor}"),
    ],
    'boot_completo_min': [
        (ADHERENCE_AUDIT, r"'boot_completo_min':\s*[\d.]+", "'boot_completo_min': {valor}"),
        (SYNC_ECOSYSTEM, r"'boot_completo_min':\s*[\d.]+", "'boot_completo_min': {valor}"),
    ],
    'comunicacao_ptbr_min': [
        (ADHERENCE_AUDIT, r"'comunicacao_ptbr_min':\s*[\d.]+", "'comunicacao_ptbr_min': {valor}"),
        (SYNC_ECOSYSTEM, r"'comunicacao_ptbr_min':\s*[\d.]+", "'comunicacao_ptbr_min': {valor}"),
    ],
}

def carregar_memories():
    if not MEMORIES.exists():
        return []
    with open(MEMORIES, encoding='utf-8') as f:
        return json.load(f)

def extrair_elevacoes_pendentes():
    """Extrai memórias de elevação de thresholds que ainda não foram aplicadas."""
    memories = carregar_memories()
    elevacoes = []
    
    for m in memories:
        titulo = m.get('task', '')
        if 'Elevação threshold' in titulo:
            # Extrai threshold, valor atual, valor novo, data
            # Formato: "Elevação threshold gate_persistencia: 1% → 20%"
            match = re.search(r'Elevação threshold (\w+):\s*([\d.]+)%\s*→\s*([\d.]+)%', titulo)
            if match:
                threshold = match.group(1)
                atual = float(match.group(2))
                novo = float(match.group(3))
                
                # Extrai data do resumo (formato: "após 7 dias (2026-08-22)")
                resumo = m.get('summary', '')
                data_match = re.search(r'\((\d{4}-\d{2}-\d{2})\)', resumo)
                data_elevacao = None
                if data_match:
                    try:
                        data_elevacao = datetime.strptime(data_match.group(1), '%Y-%m-%d').date()
                    except:
                        pass
                
                elevacoes.append({
                    'id': m.get('id'),
                    'threshold': threshold,
                    'atual': atual,
                    'novo': novo,
                    'data_elevacao': data_elevacao,
                    'titulo': titulo,
                    'resumo': resumo,
                    'aplicada': 'aplicada' in (resumo.lower() + ' ' + titulo.lower())
                })
    return elevacoes

def verificar_vencidas():
    """Verifica quais elevações estão vencidas (data <= hoje) e não aplicadas."""
    elevacoes = extrair_elevacoes_pendentes()
    hoje = datetime.now().date()
    vencidas = []
    for e in elevacoes:
        if not e['aplicada'] and e['data_elevacao'] and e['data_elevacao'] <= hoje:
            vencidas.append(e)
    return vencidas

def aplicar_elevacao(threshold: str, novo_valor: float):
    """Atualiza o valor do threshold nos dois arquivos de configuração."""
    if threshold not in THRESHOLD_CONFIG:
        print(f'[ERRO] Threshold desconhecido: {threshold}')
        return False
    
    padrao_valor = f"{novo_valor:.1f}" if novo_valor != int(novo_valor) else str(int(novo_valor))
    alterado = False
    
    for arquivo, padrao_regex, substituicao in THRESHOLD_CONFIG[threshold]:
        if not arquivo.exists():
            print(f'[AVISO] Arquivo não encontrado: {arquivo}')
            continue
        
        with open(arquivo, encoding='utf-8') as f:
            conteudo = f.read()
        
        novo_conteudo = re.sub(padrao_regex, substituicao.format(valor=padrao_valor), conteudo)
        
        if novo_conteudo != conteudo:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(novo_conteudo)
            print(f'[OK] {arquivo.name}: {threshold} = {padrao_valor}')
            alterado = True
        else:
            print(f'[INFO] {arquivo.name}: já estava com {threshold} = {padrao_valor}')
    
    return alterado

def marcar_como_aplicada(threshold: str, novo_valor: float):
    """Adiciona nota na memória indicando que a elevação foi aplicada."""
    memories = carregar_memories()
    for m in memories:
        if 'Elevação threshold' in m.get('task', '') and threshold in m.get('task', ''):
            if f'{novo_valor}%' in m.get('task', ''):
                m['summary'] = m.get('summary', '') + ' [APLICADA EM ' + datetime.now().strftime('%Y-%m-%d') + ']'
                m['task'] = m.get('task', '') + ' [APLICADA]'
    with open(MEMORIES, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def cmd_check():
    vencidas = verificar_vencidas()
    if vencidas:
        print(f'[INFO] {len(vencidas)} elevação(ões) vencida(s) pendente(s):')
        for e in vencidas:
            print(f'  - {e["threshold"]}: {e["atual"]}% → {e["novo"]}% (desde {e["data_elevacao"]})')
    else:
        print('[OK] Nenhuma elevação vencida pendente.')
    return 0

def cmd_status():
    elevacoes = extrair_elevacoes_pendentes()
    hoje = datetime.now().date()
    print('PRÓXIMAS ELEVAÇÕES AGENDADAS:')
    for e in sorted(elevacoes, key=lambda x: x['data_elevacao'] or datetime.max.date()):
        if not e['aplicada']:
            dias = (e['data_elevacao'] - hoje).days if e['data_elevacao'] else 'N/A'
            status = 'VENCIDA' if e['data_elevacao'] and e['data_elevacao'] <= hoje else f'em {dias} dias'
            print(f'  {e["threshold"]}: {e["atual"]}% → {e["novo"]}% — {status} ({e["data_elevacao"]})')
    return 0

def cmd_apply():
    vencidas = verificar_vencidas()
    if not vencidas:
        print('[OK] Nenhuma elevação vencida para aplicar.')
        return 0
    
    print(f'[INFO] Aplicando {len(vencidas)} elevação(ões)...')
    for e in vencidas:
        if aplicar_elevacao(e['threshold'], e['novo']):
            marcar_como_aplicada(e['threshold'], e['novo'])
            print(f'[OK] Elevação aplicada: {e["threshold"]} = {e["novo"]}%')
        else:
            print(f'[ERRO] Falha ao aplicar: {e["threshold"]}')
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    cmd = sys.argv[1]
    if cmd == 'check':
        return cmd_check()
    elif cmd == 'apply':
        return cmd_apply()
    elif cmd == 'status':
        return cmd_status()
    else:
        print(f'[ERRO] Comando desconhecido: {cmd}')
        print(__doc__)
        return 1

if __name__ == '__main__':
    sys.exit(main())