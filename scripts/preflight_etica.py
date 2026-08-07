#!/usr/bin/env python3
"""
Pre-flight Ético do EcoSystemUmGrau.
Cláusula Pétrea de Deveres Externos: se qualquer cheque falhar, BLOQUEIA a entrega.

Usado como gate obrigatório antes de toda entrega que toque dados, usuários,
decisões automatizadas ou impacto externo.

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

BASE = str(Path(__file__).resolve().parent.parent)
REPORT_DIR = os.path.join(BASE, 'conhecimento', 'etica')
os.makedirs(REPORT_DIR, exist_ok=True)

ERRORS = []
WARNS = []

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
    'criancas': ['crian', 'menor', 'infant'],
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
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in skip]
        for fname in files:
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
        return 0 if not ERRORS else 1
    if '--data-inventory' in sys.argv:
        data_inventory()
        return 0

    target = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            target = arg
            break

    print('=== Preflight Ético - EcoSystemUmGrau ===')
    print(f'Verificando: {target or "working dir"}')

    if target:
        if os.path.isdir(target):
            for f in os.listdir(target):
                if f.endswith(('.py', '.js', '.ts', '.json')):
                    scan_file(os.path.join(target, f))
        elif os.path.isfile(target):
            scan_file(target)
    else:
        scan_repo()

    # Cheques de conformidade estrutural (independentes do scan)
    print('\n--- Conformidade estrutural ---')
    const = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')
    check('Constituicao contem Clausula de Deveres Externos',
          _const_has_deveres(const),
          'adicione a Clausula Petrea de Deveres Externos')

    const_deployed = os.path.join(Path.home(), '.config', 'opencode', 'agents', '00-system-rules.md')
    check('Constituicao deployada sincronizada',
          os.path.exists(const_deployed) and _file_eq(const, const_deployed),
          'rode python scripts/sync_rules.py update')

    # Lacuna 1: decisao etica registrada na memoria
    mem = os.path.join(BASE, 'conhecimento', 'memoria', 'memories.json')
    check('Memoria registra decisoes eticas',
          _mem_has_etica(mem),
          'registre decisoes eticas com memory_engine.py (tipo decisao)')

    # Lacuna 4: politica de retencao existente
    ret = os.path.join(REPORT_DIR, 'POLITICA_RETENCAO.md')
    check('Politica de retencao/exclusao existe',
          os.path.exists(ret),
          'crie conhecimento/etica/POLITICA_RETENCAO.md')

    print('\n=== RESULTADO ===')
    if ERRORS:
        print(f'BLOQUEADO: {len(ERRORS)} bloqueio(s) etico(s)')
        for e in ERRORS:
            print(f'  [BLOQUEIO] {e}')
        registrar_avaliacao('bloqueado', 'entrega bloqueada pelo preflight etico')
        return 1

    print(f'APROVADO com {len(WARNS)} alerta(s) de revisao.')
    registrar_avaliacao('aprovado', 'entrega aprovada no preflight etico')
    return 0


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
