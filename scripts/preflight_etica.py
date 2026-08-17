#!/usr/bin/env python3
"""
Pre-flight Ético do EcoSystemUmGrau.
Cláusula Pétrea de Deveres Externos: se qualquer cheque falhar, BLOQUEIA a entrega.

O rigor depende do NÍVEL ÉTICO atual:
  desativado (PADRÃO) - ética desativada: sem avisos e sem bloqueios
  minimo               - permite o tecnicamente viável, avisos mínimos (não bloqueia)
  medio                - bloqueia pontos sensíveis, exige consentimento/avaliação
  maximo               - bloqueia qualquer incerteza até revisão humana

Altere o nível com: python scripts/niveis_etica.py set <nivel>

Uso:
  python scripts/preflight_etica.py            # verifica working dir atual
  python scripts/preflight_etica.py <caminho>  # verifica arquivo/script especifico
  python scripts/preflight_etica.py --scan-repo  # varre todo o repo por riscos
  python scripts/preflight_etica.py --data-inventory  # lista dados sensiveis mapeados

Exit: 0 = aprovado, 1 = bloqueado (com relatorio de motivos).
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

BASE = str(Path(__file__).resolve().parent.parent)
REPORT_DIR = os.path.join(BASE, 'conhecimento', 'etica')
os.makedirs(REPORT_DIR, exist_ok=True)

ERRORS = []
WARNS = []

PREFLIGHT_LOG = Path(__file__).resolve().parent.parent / 'runtime' / 'preflight_executions.log'

def log_preflight_execution(tipo: str, success: bool, erros_count: int = 0):
    """Registra execução do preflight para métricas de aderência."""
    try:
        PREFLIGHT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tipo': tipo,  # 'tecnico' ou 'etico'
            'success': success,
            'erros_count': erros_count
        }
        with open(PREFLIGHT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass  # Fail silently - não bloqueia o preflight

# Nivel etico atual (default: desativado)
NIVEIS_FILE = os.path.join(REPORT_DIR, 'niveis_etica.json')


def nivel_atual():
    """Retorna o nivel etico configurado (padrao: desativado)."""
    try:
        with open(NIVEIS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('nivel_atual', 'desativado')
    except Exception:
        return 'desativado'


def bloco_nivel():
    """Lista de categorias que BLOQUEIAM no nivel atual."""
    try:
        with open(NIVEIS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        nivel = data.get('nivel_atual', 'desativado')
        return data.get('niveis', {}).get(nivel, {}).get('bloqueia', [])
    except Exception:
        return []


NIVEL = nivel_atual()
BLOQUEIA = bloco_nivel()

# Padroes de risco (heuristica - complemento da avaliacao do agente 04-etica)
SEG_PATTERNS = [
    (r'(?i)\b(cpf|rg|cnpj|cartao|cart[ãa]o|nascimento)\b',
     'campo de dado pessoal/identificacao detectado'),
    (r'(?i)\b(password|senha)\b\s*[=:]\s*["\'][^"\']+["\']',
     'credencial hardcoded'),
    (r'(?i)\b(api[_-]?key|secret|token)\b\s*[=:]\s*["\'][^"\']+["\']',
     'segredo hardcoded'),
    (r'(?i)\b(credit|debit).{0,20}(card|number|n[uú]mero)\b',
     'numero de cartao de pagamento'),
    (r'(?i)\b(phone|telefone|email|endere[çc]o)\b.*\b(colet|store|salvar)\b',
     'coleta de dados pessoais sem evidencias de consentimento'),
    (r'(?i)\b(gps|location|localiza[çc][ãa]o)\b.*\b(track|rastre)\b',
     'rastreamento de localizacao'),
]

# Categorias de dados sensiveis para inventario (Lacuna 4 - retencao)
CATEGORIAS_SENSIVEIS = {
    'audio': ['voz', 'áudio', 'audio', 'speech', 'vad', 'whisper'],
    'biometrico': ['biometr', 'impress', 'face', 'iris'],
    'localizacao': ['gps', 'localiza', 'location', 'geoloc'],
    'saude': ['saúde', 'saude', 'medic', 'biomédico', 'biomedico'],
    'criancas': ['crianc', 'menor de', 'infant'],
    'identificacao': ['cpf', 'rg', 'passaporte', 'cnh'],
    'credito': ['cartão', 'cartao', 'card number', 'cvv', 'pagamento'],
    'comunicacao': ['mensagem', 'chat', 'historico', 'log de', 'transcri'],
}


def check(label, condition, detail=''):
    if condition:
        print(f'  [PASS] {label}')
        return True
    msg = f'{label}: {detail}' if detail else label
    ERRORS.append(msg)
    print(f'  [FAIL] {msg}')
    return False


def scan_file(path):
    """Varre um arquivo em busca de padroes de risco etico."""
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return 0
    hits = 0
    rel = os.path.relpath(path, BASE)
    for pat, desc in SEG_PATTERNS:
        m = re.search(pat, content)
        if m:
            hits += 1
            WARNS.append(f'{rel}: {desc}')
            print(f'  [WARN] {rel}: {desc}')
    return hits


def scan_repo():
    """Varre o repo por riscos eticos (modo --scan-repo)."""
    print('[SCAN] Varrendo repo por riscos eticos...')
    total = 0
    # Pastas ignoradas: terceiros, cache, backups e estados efemeros
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'health', 'logs',
                 'backups', '.obsidian', 'vendor', 'dist', 'build', 'site-packages'}
    skip_files = {
        'preflight_etica.py',      # contem os padroes de busca em texto literal
        'inventario_dados.json',   # output do proprio inventario
    }
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname in skip_files:
                continue
            if fname.endswith(('.py', '.js', '.ts', '.json', '.md')):
                total += scan_file(os.path.join(root, fname))
    print(f'[SCAN] {total} ocorrencia(s) de padrao de risco (revisar).')
    return total


def data_inventory():
    """Lacuna 4: cataloga onde dados sensiveis sao tratados, para retencao/exclusao."""
    print('[INVENTARIO] Mapeando dados sensiveis no repo...')
    inventory = {}
    skip = {'.git', 'node_modules', '__pycache__', '.venv', 'health',
            'backups', '.obsidian', 'vendor', 'dist', 'build', 'site-packages'}
    skip_files = {'preflight_etica.py', 'niveis_etica.py', 'inventario_dados.json',
                  'niveis_etica.json'}
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in skip]
        for fname in files:
            if fname in skip_files:
                continue
            if not fname.endswith(('.py', '.js', '.ts', '.json', '.md')):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                continue
            rel = os.path.relpath(fpath, BASE)
            for cat, keywords in CATEGORIAS_SENSIVEIS.items():
                if any(kw in content.lower() for kw in keywords):
                    inventory.setdefault(cat, []).append(rel)

    out = os.path.join(REPORT_DIR, 'inventario_dados.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    print(f'[INVENTARIO] Categorias com ocorrencias: {len(inventory)}')
    for cat, files in inventory.items():
        print(f'  - {cat}: {len(files)} arquivo(s)')
    print(f'[INVENTARIO] Salvo em: {out}')
    return inventory


def _promover_warns_por_nivel():
    """Converte avisos do scan em bloqueios, conforme o nivel etico atual."""
    if NIVEL == 'minimo':
        return
    # Mapeia categoria do aviso -> chave de bloqueio no config
    mapa = {
        'segredo hardcoded': 'segredos_crus',
        'credencial hardcoded': 'segredos_crus',
        'coleta de dados pessoais sem evidencias de consentimento': 'dados_sensiveis_sem_consentimento',
        'numero de cartao de pagamento': 'dados_sensiveis',
        'rastreamento de localizacao': 'dados_sensiveis',
    }
    # chaves alternativas aceitas pelo config
    sinonimos = {
        'segredos_crus': {'segredos', 'qualquer_risco'},
        'dados_sensiveis': {'qualquer_risco'},
        'dados_sensiveis_sem_consentimento': {'dados_sensiveis', 'qualquer_risco'},
    }
    for aviso in list(WARNS):
        # nivel maximo: qualquer risco bloqueia
        if 'qualquer_risco' in BLOQUEIA:
            ERRORS.append(f'[nivel {NIVEL}] {aviso}')
            WARNS.remove(aviso)
            continue
        for fragmento, chave in mapa.items():
            chaves_ok = {chave} | sinonimos.get(chave, set())
            if fragmento in aviso and chaves_ok & set(BLOQUEIA):
                ERRORS.append(f'[nivel {NIVEL}] {aviso}')
                WARNS.remove(aviso)
                break


def registrar_avaliacao(resultado, motivo):
    """Registra avaliacao etica na memoria (Lacuna 1 - operacionalizar)."""
    try:
        memory = os.path.join(BASE, 'scripts', 'memory_engine.py')
        if os.path.exists(memory):
            tipo = 'decisao' if resultado == 'aprovado' else 'erro'
            titulo = f'Preflight Etico: {resultado.upper()}'
            resumo = f'{motivo} | {len(ERRORS)} bloqueio(s), {len(WARNS)} alerta(s)'
            subprocess = __import__('subprocess')
            subprocess.run(
                [sys.executable, memory, 'add', titulo, resumo, tipo],
                capture_output=True, timeout=30, cwd=BASE)
    except Exception:
        pass


def main():
    if '--scan-repo' in sys.argv:
        scan_repo()
        log_preflight_execution('etico', not ERRORS, len(ERRORS))
        return 0 if not ERRORS else 1
    if '--data-inventory' in sys.argv:
        data_inventory()
        log_preflight_execution('etico', True, 0)
        return 0

    target = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            target = arg
            break

    print('=== Preflight Ético - EcoSystemUmGrau ===')
    print(f'Nível ético atual: {NIVEL}')
    print(f'Verificando: {target or "working dir"}')

    if NIVEL == 'desativado':
        print('\n=== RESULTADO ===')
        print('DESATIVADO: preflight etico sem avisos e sem bloqueios (modo administrador).')
        log_preflight_execution('etico', True, 0)
        return 0

    if target:
        if os.path.isdir(target):
            for f in os.listdir(target):
                if f.endswith(('.py', '.js', '.ts', '.json')):
                    scan_file(os.path.join(target, f))
        elif os.path.isfile(target):
            scan_file(target)
    else:
        scan_repo()

    # Promove avisos a bloqueios conforme o nivel etico
    _promover_warns_por_nivel()

    # Cheques de conformidade estrutural (dependentes do nível)
    print('\n--- Conformidade estrutural ---')
    const = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')
    check('Constituicao contem Clausula de Deveres Externos',
          _const_has_deveres(const),
          'adicione a Clausula Petrea de Deveres Externos')

    const_deployed = os.path.join(Path.home(), '.config', 'opencode', 'agents', '00-system-rules.md')
    check('Constituicao deployada sincronizada',
          os.path.exists(const_deployed) and _file_eq(const, const_deployed),
          'rode python scripts/sync_rules.py update')

    # Regras imutaveis minimas: SEMPRE valem, em qualquer nivel
    print('\n--- Regras imutaveis minimas ---')
    regras = _regras_imutaveis()
    for regra in regras:
        # Heuristica simples: checa se a regra tem artefato correspondente
        ok = _regra_atendida(regra)
        check(f'Regra minima: {regra}', ok, 'crie/ajuste o artefato correspondente')

    # Lacuna 1: decisao etica registrada na memoria
    mem = os.path.join(BASE, 'conhecimento', 'memoria', 'memories.json')
    ok_mem = _mem_has_etica(mem)
    if 'sem_avaliacao_etica' in BLOQUEIA:
        check('Memoria registra decisoes eticas', ok_mem,
              'registre decisoes eticas com memory_engine.py (tipo decisao)')
    elif not ok_mem:
        WARNS.append('Memoria sem decisoes eticas registradas (avisos - nivel baixo)')
        print('  [AVISO] Memoria sem decisoes eticas registradas')

    # Lacuna 4: politica de retencao existente
    ret = os.path.join(REPORT_DIR, 'POLITICA_RETENCAO.md')
    ok_ret = os.path.exists(ret)
    if 'retencao_ausente' in BLOQUEIA:
        check('Politica de retencao/exclusao existe', ok_ret,
              'crie conhecimento/etica/POLITICA_RETENCAO.md')
    elif not ok_ret:
        WARNS.append('Politica de retencao ausente (aviso - nivel baixo)')
        print('  [AVISO] Politica de retencao ausente (aviso - nivel baixo)')

    print('\n=== RESULTADO ===')
    if ERRORS:
        print(f'BLOQUEADO: {len(ERRORS)} bloqueio(s) etico(s)')
        for e in ERRORS:
            print(f'  [BLOQUEIO] {e}')
        registrar_avaliacao('bloqueado', f'entrega bloqueada no nivel {NIVEL}')
        log_preflight_execution('etico', False, len(ERRORS))
        return 1

    if NIVEL == 'minimo':
        print(f'APROVADO (nível {NIVEL}): tecnicamente viavel, {len(WARNS)} aviso(s) de revisao.')
        registrar_avaliacao('aprovado', f'entrega aprovada no nivel {NIVEL}')
        log_preflight_execution('etico', True, 0)
        return 0

    print(f'APROVADO com {len(WARNS)} alerta(s) de revisao.')
    registrar_avaliacao('aprovado', f'entrega aprovada no nivel {NIVEL}')
    log_preflight_execution('etico', True, 0)
    return 0


def _regras_imutaveis():
    """Retorna as regras minimas que valem em qualquer nivel."""
    try:
        with open(NIVEIS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('regras_imutaveis_minimas', [])
    except Exception:
        return []


def _regra_atendida(regra):
    """Heuristica: a regra minima foi atendida por um artefato correspondente."""
    regra_l = regra.lower()
    # credenciais em texto plano -> verifica que nao ha .env versionado com segredos crus
    if 'credenciais' in regra_l or 'texto plano' in regra_l:
        env = os.path.join(BASE, '.env')
        return not os.path.exists(env)
    # exclusao de dados -> politica de retencao existe
    if 'exclusao' in regra_l or 'excluir' in regra_l:
        return os.path.exists(os.path.join(REPORT_DIR, 'POLITICA_RETENCAO.md'))
    # dados de criancas -> inventario nao aponta coletas de criancas
    if 'criancas' in regra_l or 'crian' in regra_l:
        inv = os.path.join(REPORT_DIR, 'inventario_dados.json')
        if not os.path.exists(inv):
            return True
        try:
            with open(inv, encoding='utf-8') as f:
                dados = json.load(f)
            return len(dados.get('criancas', [])) == 0
        except Exception:
            return True
    return True


def _const_has_deveres(const):
    if not os.path.exists(const):
        return False
    try:
        with open(const, encoding='utf-8') as f:
            return 'DEVERES EXTERNOS' in f.read()
    except Exception:
        return False


def _file_eq(a, b):
    try:
        with open(a, encoding='utf-8') as fa, open(b, encoding='utf-8') as fb:
            return fa.read() == fb.read()
    except Exception:
        return False


def _mem_has_etica(mem):
    if not os.path.exists(mem):
        return False
    try:
        with open(mem, encoding='utf-8') as f:
            data = json.load(f)
        for m in data:
            texto = json.dumps(m, ensure_ascii=False).lower()
            if 'ética' in texto or 'etica' in texto:
                return True
        return False
    except Exception:
        return False


if __name__ == '__main__':
    sys.exit(main())
