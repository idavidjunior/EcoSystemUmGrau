#!/usr/bin/env python3
"""
inventory_manager.py — Gerenciador do Inventário de Estruturas Ativas do EcoSystemUmGrau

Uso:
  python scripts/inventory_manager.py list                    # lista tudo
  python scripts/inventory_manager.py list --tipo agentes     # filtra por tipo
  python scripts/inventory_manager.py add --tipo mcp_habilidade --dominio desenvolvimento --id nova-habilidade --responsabilidade "Descrição"
  python scripts/inventory_manager.py remove --tipo agentes --id 00-novo-agente
  python scripts/inventory_manager.py verify                  # verifica integridade (arquivos existem)
  python scripts/inventory_manager.py sync                    # sincroniza com realidade do disco (scan)
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
INVENTARIO_PATH = BASE / 'config' / 'inventario_estruturas.json'

TIPOS_VALIDOS = [
    'agentes', 'skills_opencode', 'mcp_servidores', 'mcp_habilidades',
    'scripts_core', 'scripts_android', 'scripts_flutter', 'scripts_monitoramento',
    'scripts_memoria_conhecimento', 'scripts_audio_voz', 'scripts_teste_validacao',
    'scripts_utilitarios', 'configuracoes', 'memoria_persistente', 'runtime_estado',
    'documentacao', 'projetos_externos', 'padroes_fluxos', 'indices_referencia'
]

def carregar() -> Dict[str, Any]:
    with open(INVENTARIO_PATH, encoding='utf-8') as f:
        return json.load(f)

def salvar(data: Dict[str, Any]) -> None:
    data['atualizado_em'] = datetime.now().isoformat()
    with open(INVENTARIO_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def listar(tipo: Optional[str] = None) -> None:
    data = carregar()
    if tipo:
        if tipo in data:
            print(json.dumps(data[tipo], ensure_ascii=False, indent=2))
        else:
            print(f'[ERRO] Tipo desconhecido: {tipo}. Tipos válidos: {", ".join(TIPOS_VALIDOS)}')
            sys.exit(1)
    else:
        for k, v in data.items():
            if k in ('versao', 'atualizado_em', 'descricao'):
                continue
            count = len(v) if isinstance(v, list) else (len(v) if isinstance(v, dict) else 1)
            print(f'{k}: {count} itens')

def adicionar(tipo: str, **kwargs) -> None:
    if tipo not in TIPOS_VALIDOS:
        print(f'[ERRO] Tipo inválido: {tipo}')
        sys.exit(1)
    data = carregar()
    if tipo == 'mcp_habilidades':
        dominio = kwargs.get('dominio')
        if not dominio:
            print('[ERRO] Para mcp_habilidades, informe --dominio')
            sys.exit(1)
        if dominio not in data[tipo]:
            data[tipo][dominio] = []
        data[tipo][dominio].append(kwargs.get('id'))
        print(f'[OK] Habilidade {kwargs.get("id")} adicionada ao domínio {dominio}')
    else:
        item = {k: v for k, v in kwargs.items() if v is not None}
        if 'id' not in item:
            print('[ERRO] Campo "id" é obrigatório')
            sys.exit(1)
        # evitar duplicata
        existente = next((x for x in data[tipo] if isinstance(x, dict) and x.get('id') == item['id']), None)
        if existente:
            print(f'[AVISO] Item com id {item["id"]} já existe. Atualizando...')
            idx = data[tipo].index(existente)
            data[tipo][idx] = item
        else:
            data[tipo].append(item)
            print(f'[OK] Item {item["id"]} adicionado a {tipo}')
    salvar(data)

def remover(tipo: str, id_item: str) -> None:
    if tipo not in TIPOS_VALIDOS:
        print(f'[ERRO] Tipo inválido: {tipo}')
        sys.exit(1)
    data = carregar()
    if tipo == 'mcp_habilidades':
        removido = False
        for dominio, habs in data[tipo].items():
            if id_item in habs:
                habs.remove(id_item)
                removido = True
                print(f'[OK] Habilidade {id_item} removida do domínio {dominio}')
                break
        if not removido:
            print(f'[AVISO] Habilidade {id_item} não encontrada')
    else:
        original_len = len(data[tipo])
        data[tipo] = [x for x in data[tipo] if not (isinstance(x, dict) and x.get('id') == id_item)]
        if len(data[tipo]) < original_len:
            print(f'[OK] Item {id_item} removido de {tipo}')
        else:
            print(f'[AVISO] Item {id_item} não encontrado em {tipo}')
    salvar(data)

def verificar_integridade() -> int:
    """Verifica se arquivos/diretórios listados no inventário existem no disco."""
    data = carregar()
    erros = 0
    avisos = 0

    def checar_caminho(caminho_rel: str, descricao: str) -> bool:
        nonlocal erros, avisos
        path = BASE / caminho_rel
        if not path.exists():
            print(f'[FALTA] {descricao}: {caminho_rel}')
            erros += 1
            return False
        return True

    # Agentes
    for ag in data.get('agentes', []):
        checar_caminho(ag['arquivo'], f"Agente {ag['id']}")

    # Skills opencode
    for sk in data.get('skills_opencode', []):
        if sk.get('status') == 'externo_opencode':
            print(f'[INFO] Skill {sk["id"]} é externa ao opencode (não verifica disco local)')
            continue
        caminho = sk['diretorio']
        if caminho.startswith('~'):
            caminho = str(Path.home() / caminho[2:])
        checar_caminho(caminho, f"Skill {sk['id']}")

    # MCP servidores
    for mcp in data.get('mcp_servidores', []):
        checar_caminho(mcp['arquivo'], f"MCP Server {mcp['id']}")

    # Scripts core
    for sc in data.get('scripts_core', []):
        checar_caminho(sc['arquivo'], f"Script core {sc['id']}")

    # Configurações
    for cfg in data.get('configuracoes', []):
        caminho = cfg['arquivo']
        if caminho.startswith('~'):
            caminho = str(Path.home() / caminho[2:])
        checar_caminho(caminho, f"Config {cfg['id']}")

    # Memória persistente
    for mem in data.get('memoria_persistente', []):
        if 'arquivo' in mem:
            checar_caminho(mem['arquivo'], f"Memória {mem['id']}")
        if 'diretorio' in mem:
            checar_caminho(mem['diretorio'], f"Dir memória {mem['id']}")

    # Runtime estado
    for rt in data.get('runtime_estado', []):
        if 'arquivo' in rt:
            checar_caminho(rt['arquivo'], f"Runtime {rt['id']}")
        if 'diretorio' in rt:
            checar_caminho(rt['diretorio'], f"Dir runtime {rt['id']}")

    # Documentação
    for doc in data.get('documentacao', []):
        if 'arquivo' in doc:
            checar_caminho(doc['arquivo'], f"Doc {doc['id']}")
        if 'diretorio' in doc:
            checar_caminho(doc['diretorio'], f"Dir doc {doc['id']}")

    # Projetos externos
    for proj, info in data.get('projetos_externos', {}).items():
        if 'diretorio' in info:
            checar_caminho(info['diretorio'], f"Projeto {proj}")
        if 'config' in info:
            checar_caminho(info['config'], f"Config projeto {proj}")

    print(f'\nResultado: {erros} erro(s), {avisos} aviso(s)')
    return 1 if erros > 0 else 0

def sincronizar_disco() -> int:
    """Escaneia o disco e atualiza o inventário com o que existe de fato."""
    data = carregar()
    atualizados = 0

    # Scan agentes
    agentes_dir = BASE / 'config' / 'agents'
    if agentes_dir.exists():
        ids_existentes = {f.stem for f in agentes_dir.glob('*.md') if f.is_file()}
        ids_inventario = {a['id'] for a in data['agentes']}
        novos = ids_existentes - ids_inventario
        for nid in sorted(novos):
            data['agentes'].append({
                'id': nid,
                'arquivo': f'config/agents/{nid}.md',
                'tipo': 'desconhecido',
                'responsabilidade': 'PENDENTE: classificar responsabilidade'
            })
            atualizados += 1
            print(f'[NOVO] Agente detectado: {nid}')

    # Scan skills opencode
    skills_dir = BASE / '.opencode' / 'skill'
    if skills_dir.exists():
        ids_existentes = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        ids_inventario = {s['id'] for s in data['skills_opencode']}
        novos = ids_existentes - ids_inventario
        for nid in sorted(novos):
            data['skills_opencode'].append({
                'id': nid,
                'diretorio': f'.opencode/skill/{nid}',
                'responsabilidade': 'PENDENTE: classificar responsabilidade'
            })
            atualizados += 1
            print(f'[NOVO] Skill opencode detectada: {nid}')

    # Scan MCP habilidades (varre todos os domínios)
    mcp_base = BASE / 'mcp'
    if mcp_base.exists():
        for dominio_dir in mcp_base.iterdir():
            if not dominio_dir.is_dir():
                continue
            hab_dir = dominio_dir / 'habilidades'
            if hab_dir.exists():
                for hab in hab_dir.iterdir():
                    if hab.is_dir():
                        hid = hab.name
                        # verifica se já existe em algum domínio
                        existe = any(hid in habs for habs in data['mcp_habilidades'].values())
                        if not existe:
                            if dominio_dir.name not in data['mcp_habilidades']:
                                data['mcp_habilidades'][dominio_dir.name] = []
                            data['mcp_habilidades'][dominio_dir.name].append(hid)
                            atualizados += 1
                            print(f'[NOVO] MCP habilidade detectada: {dominio_dir.name}/{hid}')

    # Scan scripts core (heurística: arquivos .py/.ps1 em scripts/ que não estão em subdirs _legado, __pycache__, keys)
    scripts_dir = BASE / 'scripts'
    if scripts_dir.exists():
        ids_inventario = {s['id'] for s in data['scripts_core']}
        for f in scripts_dir.iterdir():
            if f.is_file() and f.suffix in ('.py', '.ps1') and not f.name.startswith('_'):
                sid = f.stem
                if sid not in ids_inventario and sid not in [s for cat in [
                    'scripts_android', 'scripts_flutter', 'scripts_monitoramento',
                    'scripts_memoria_conhecimento', 'scripts_audio_voz',
                    'scripts_teste_validacao', 'scripts_utilitarios'
                ] for s in data[cat]]:
                    data['scripts_core'].append({
                        'id': sid,
                        'arquivo': f'scripts/{f.name}',
                        'funcao': 'PENDENTE: descrever função'
                    })
                    atualizados += 1
                    print(f'[NOVO] Script core detectado: {sid}')

    if atualizados > 0:
        salvar(data)
        print(f'\n[OK] Inventário sincronizado: {atualizados} nova(s) estrutura(s) adicionada(s)')
    else:
        print('[OK] Inventário já reflete o disco (nenhuma estrutura nova)')
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'list':
        tipo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '--tipo' else None
        if '--tipo' in sys.argv:
            idx = sys.argv.index('--tipo')
            if idx + 1 < len(sys.argv):
                tipo = sys.argv[idx + 1]
        listar(tipo)

    elif cmd == 'add':
        if '--tipo' not in sys.argv:
            print('[ERRO] Informe --tipo')
            sys.exit(1)
        idx = sys.argv.index('--tipo')
        tipo = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        kwargs = {}
        for i in range(idx + 2, len(sys.argv), 2):
            if i + 1 < len(sys.argv):
                key = sys.argv[i].lstrip('-')
                kwargs[key] = sys.argv[i + 1]
        adicionar(tipo, **kwargs)

    elif cmd == 'remove':
        if '--tipo' not in sys.argv or '--id' not in sys.argv:
            print('[ERRO] Informe --tipo e --id')
            sys.exit(1)
        tipo = sys.argv[sys.argv.index('--tipo') + 1]
        id_item = sys.argv[sys.argv.index('--id') + 1]
        remover(tipo, id_item)

    elif cmd == 'verify':
        sys.exit(verificar_integridade())

    elif cmd == 'sync':
        sys.exit(sincronizar_disco())

    else:
        print(f'[ERRO] Comando desconhecido: {cmd}')
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()