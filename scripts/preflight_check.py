"""Pre-flight check: valida config, MCP e plugins ANTES de deployar.
Clausula Petrea: se falhar, NAO aplica a alteracao."""
import json, os, sys, subprocess, traceback
import re
from pathlib import Path
from datetime import datetime

USERPROFILE = str(Path.home())
BASE = str(Path(__file__).resolve().parent.parent)
DEPLOYED = os.path.join(USERPROFILE, '.config', 'opencode', 'opencode.jsonc')
BACKUP = DEPLOYED + '.bak'
AUTH_FILE = os.path.join(USERPROFILE, '.local', 'share', 'opencode', 'auth.json')

# Prefixos de segredo bruto que NUNCA devem constar crus em config/auth (NVIDIA mascarada, OpenAI, GitHub PAT, etc.)
SECRET_PREFIXES = ('nvapi-', 'sk-', 'sk-or-', 'ghp_', 'gho_', 'ghu_', 'gh_', 'gpt-', 'api_')
# Chaves de login OAuth oficial do OpenCode (shape de estado, nao segredos de provider)
OAUTH_LOGIN_KEYS = ('token', 'type', 'expires', 'refresh_token', 'scope')
# Heuristica: valor com este prefixo em provider != "nvidia" = chave mascarada (o bug sessao_limpeza_auth)
NVAPI_DONO_LEGITIMO = 'nvidia'

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

def check(label, condition, detail=''):
    if condition:
        print(f'  [PASS] {label}')
        return True
    else:
        msg = f'{label}: {detail}' if detail else label
        ERRORS.append(msg)
        print(f'  [FAIL] {msg}')
        return False

def check_json(path, label='JSON'):
    try:
        with open(path, encoding='utf-8-sig') as f:
            data = json.load(f)
        return check(f'{label} JSON valido', True), data
    except Exception as e:
        check(f'{label} JSON valido', False, str(e))
        return False, None

def expand_path(path_str):
    """Expand {env:USERPROFILE} and legacy {{USERPROFILE}} template vars."""
    result = path_str.replace('{env:USERPROFILE}', USERPROFILE.replace('\\', '/'))
    result = result.replace('{{USERPROFILE}}', USERPROFILE.replace('\\', '/'))
    return result

def test_mcp_server(server_name, command, args):
    """Test an MCP server: initialize + tools/list must complete in 5s."""
    print(f'  Testing MCP: {server_name}...')
    try:
        # Expand template vars if present
        cmd_expanded = expand_path(command)
        args_expanded = [expand_path(a) for a in args]
        proc = subprocess.Popen(
            [cmd_expanded] + args_expanded,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=BASE)
        init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        tools = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
        stdout, stderr = proc.communicate(input=init + tools, timeout=5)
        proc.kill()
        if stderr and 'Error' in stderr:
            return check(f'MCP {server_name}', False, stderr[:200])
        # Aceita os dois protocolos de resposta: JSON por linha (servidores
        # legados) e framing MCP oficial (Content-Length: n\r\n\r\n<body>).
        for l in stdout.split('\n'):
            l = l.strip()
            if not l or not l.startswith('{'):
                continue
            try:
                obj = json.loads(l)
            except json.JSONDecodeError:
                continue
            result = obj.get('result') or {}
            if isinstance(result, dict) and 'tools' in result:
                n_tools = len(result['tools'])
                return check(f'MCP {server_name}', True, f'{n_tools} tools')
        return check(f'MCP {server_name}', False, 'No valid tools/list response')
    except subprocess.TimeoutExpired:
        proc.kill()
        return check(f'MCP {server_name}', False, 'Timeout (5s)')
    except Exception as e:
        return check(f'MCP {server_name}', False, str(e)[:200])

def check_mcp_servers(cfg, label='Config', test_servers=True):
    """Validate MCP server configs in a given config dict.

    Suporta o formato novo (opencode 1.x): mcp.<nome> com "command" sendo lista
    [cmd, arg1, ...], e o formato legado: mcp.servers.<nome> com command + args.
    """
    mcp = cfg.get('mcp')
    if not mcp:
        WARNS.append(f'{label}: sem servidor MCP configurado (opcional)')
        print(f'  [WARN] {label}: sem servidor MCP configurado (opcional)')
        return
    servers = mcp.get('servers', mcp) if isinstance(mcp, dict) else {}
    if not servers:
        WARNS.append(f'{label}: sem servidor MCP configurado (opcional)')
        print(f'  [WARN] {label}: sem servidor MCP configurado (opcional)')
        return
    check(f'{label}: {len(servers)} MCP servidor(es)', True)
    for sname, sconfig in servers.items():
        if not isinstance(sconfig, dict):
            continue
        cmd = sconfig.get('command', '')
        args = sconfig.get('args', [])
        if isinstance(cmd, list):
            args = cmd[1:] + (list(args) if isinstance(args, list) else [])
            cmd = cmd[0] if cmd else ''
        if not cmd:
            check(f'{label}: MCP {sname} sem command', False)
            continue
        if 'npx' in str(cmd).lower():
            check(f'{label}: MCP {sname} npx proibido', False,
                  'Servidores npx travam inicializacao do OpenCode. Use Python puro.')
            continue
        if test_servers:
            test_mcp_server(sname, cmd, args)

def obscure(v, attrs=(8, 4)):
    """Mascara um segredo para logs/erros SEM expor o valor."""
    s = str(v)
    if not s:
        return '(vazio)'
    if len(s) <= int(attrs[0]) + int(attrs[1]):
        return '*' * len(s)
    return s[:int(attrs[0])] + '*' * 6 + s[-int(attrs[1]):]

def eh_segredo_bruto(v):
    """True se o valor comeca com prefixo de chave API/PAT cru."""
    s = str(v)
    return any(s.startswith(p) for p in SECRET_PREFIXES)

def guard_auth_json():
    """auth.json deve conter apenas login OAuth oficial do OpenCode, nunca chaves de provider.
    Reflete o bug 'sessao_limpeza_auth': chaves nvapi camufladas como outros providers."""
    if not os.path.exists(AUTH_FILE):
        check('Secrets: auth.json neutro (inexistente)', True)
        return
    try:
        with open(AUTH_FILE, encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        check('Secrets: auth.json JSON valido', False, str(e)[:120])
        return
    if not isinstance(data, dict):
        check('Secrets: auth.json shape', False, 'esperado objeto')
        return

    segredos = 0
    mascaradas = 0
    for provider, val in (data or {}).items():
        if not isinstance(val, dict):
            continue
        for k, v in val.items():
            s = str(v)
            if eh_segredo_bruto(s):
                # chave nvapi em provider != nvidia = mascara (o bug historico)
                if s.startswith(NVAPI_DONO_LEGITIMO + '-') and provider.lower() != NVAPI_DONO_LEGITIMO:
                    mascaradas += 1
                    check(f'Secrets: auth.json chave mascarada em "{provider}"', False,
                          f'{k}={obscuro(s)} (bloqueado)')
                else:
                    segredos += 1
                    check(f'Secrets: auth.json segredo cru em "{provider}"', False,
                          f'{k} (bloqueio - chaves devem usar env vars)')
    if mascaradas or segredos:
        return
    # sem segredos crus: OK (auth.json com shape OAuth/{} e seguro)
    check('Secrets: auth.json sem chaves mascaradas', mascaradas == 0)
    check('Secrets: auth.json sem segredos crus', segredos == 0)

def guard_env_vars(cfg, label):
    """Toda {env:VAR} referenciada na config deve estar definida no ambiente."""
    # coleta todas as refs {env:...} do template + deployed
    refs = set()
    for path in (os.path.join(BASE, 'config', 'opencode.jsonc'), DEPLOYED):
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8-sig') as f:
                    t = f.read()
                refs |= set(re.findall(r'\{env:([A-Z0-9_]+)\}', t))
            except Exception:
                pass
    if not refs:
        check(f'Secrets: env vars referenciadas ({label})', True, 'nenhuma')
        return
    for var in sorted(refs):
        v = os.environ.get(var, '').strip()
        legend = 'DEFINIDA' if v else 'AUSENTE'
        check(f'Secrets: env {var} {legend}', bool(v), 'nao definida no ambiente')

def guard_literal_keys(cfg, label):
    """Nenhuma apiKey/token/secret literal na config; so {env:...} permitido."""
    def scan(obj, path=''):
        hits = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                np = f'{path}.{k}' if path else k
                lk = k.lower()
                if lk in ('apikey', 'api_key', 'token', 'secret', 'password'):
                    if isinstance(v, str) and not v.startswith('{env:'):
                        hits.append((np, v))
                elif isinstance(v, (dict, list)):
                    hits += scan(v, np)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                hits += scan(v, f'{path}[{i}]')
        return hits
    for path, val in scan(cfg):
        v = str(val)
        if eh_segredo_bruto(v) or not v.startswith('{env:'):
            env_uso = '{env:VAR}'
            check(f'Secrets: apiKey literal em {path}', False,
                  f'{path} nao usa {env_uso}. Todo segredo deve vir de env var.')
            return
    check(f'Secrets: sem apiKey literal ({label})', True)

def run():
    print('========================================')
    print('  PRE-FLIGHT CHECK - Clausula Petrea')
    print('========================================\n')

    # 1. Template config (estrutura, sem testar servers pq tem {{USERPROFILE}})
    print('[1] Template config (estrutura)')
    template_path = os.path.join(BASE, 'config', 'opencode.jsonc')
    ok, cfg = check_json(template_path, 'Template')
    if ok and cfg:
        required_keys = ['plugin', 'provider', 'instructions']
        for key in required_keys:
            check(f'Config tem: {key}', key in cfg)
        check_mcp_servers(cfg, 'Template', test_servers=False)

    # 2. Deployed config (estrutura + testar servers)
    print('\n[2] Deployed config (estrutura + MCP real)')
    if os.path.exists(DEPLOYED):
        ok2, cfg2 = check_json(DEPLOYED, 'Deployed')
        if ok2 and cfg2:
            check('Deployed tem: instructions', 'instructions' in cfg2)
            for opt in ['plugin', 'provider', 'mcp']:
                if cfg2.get(opt) is None:
                    WARNS.append(f'Deployed sem {opt} (opcional)')
                    print(f'  [WARN] Deployed sem {opt} (opcional)')
            with open(DEPLOYED, encoding='utf-8-sig') as f:
                content = f.read()
            check('Deployed sem npx', 'npx' not in content, 'npx encontrado!')
            check_mcp_servers(cfg2, 'Deployed', test_servers=True)
    else:
        check('Deployed config existe', False, f'{DEPLOYED} nao encontrado')

    # 3. Rollback capability
    print('\n[3] Rollback capability')
    if os.path.exists(BACKUP):
        check('Backup disponivel', True)
    else:
        WARNS.append('Sem backup (opencode.jsonc.bak). Crie backup antes de alterar.')
        print('  [WARN] Sem backup. Crie backup antes de alterar.')

    # 4. Agents integrity
    print('\n[4] Agents')
    agents_dir = os.path.join(BASE, 'config', 'agents')
    if os.path.isdir(agents_dir):
        agent_files = [f for f in os.listdir(agents_dir) if f.endswith('.md')]
        check(f'{len(agent_files)} agent files', len(agent_files) >= 15)
    else:
        check('Agents dir', False)

    # 5. Regras 3 camadas (AGENTS.md + opencode.jsonc instructions + constituicao deployed)
    print('\n[5] Regras do ecossistema (3 camadas)')
    try:
        import subprocess as sp
        r = sp.run([sys.executable, os.path.join(BASE, 'scripts', 'sync_rules.py'), 'check'],
                   capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).strip()
        for line in out.splitlines():
            if line.startswith('[DIVERGENCIA]'):
                check(f'Regras consistentes', False, line.replace('[DIVERGENCIA] ', ''))
        if not any(l.startswith('[DIVERGENCIA]') for l in out.splitlines()):
            check('Regras 3 camadas consistentes', True)
    except Exception as e:
        check('Regras 3 camadas', False, str(e)[:200])

    # 6. Secrets Guard (anti-regressao do bug 'sessao_limpeza_auth')
    print('\n[6] Secrets Guard (anti-regressao)')
    guard_auth_json()
    # env vars: usa o cfg2 se existir, senao tenta ler deployed cru
    env_cfg = None
    for p in (os.path.join(BASE, 'config', 'opencode.jsonc'), DEPLOYED):
        if os.path.exists(p):
            try:
                env_cfg = json.load(open(p, encoding='utf-8-sig'))
                break
            except Exception:
                continue
    guard_env_vars(env_cfg or {}, 'template/deployed')
    for p, label in ((os.path.join(BASE, 'config', 'opencode.jsonc'), 'Template'),
                     (DEPLOYED, 'Deployed')):
        if os.path.exists(p):
            try:
                guard_literal_keys(json.load(open(p, encoding='utf-8-sig')), label)
            except Exception as e:
                check(f'Secrets: scan {label}', False, str(e)[:120])

    # 7. Preflight Etico (Clausula Petrea de Deveres Externos)
    print('\n[7] Preflight Etico (Deveres Externos)')
    try:
        import subprocess as sp
        r = sp.run([sys.executable, os.path.join(BASE, 'scripts', 'preflight_etica.py')],
                   capture_output=True, text=True, timeout=120, cwd=BASE)
        out = (r.stdout + r.stderr).strip()
        for line in out.splitlines():
            if line.startswith('[BLOQUEIO]') or 'BLOQUEADO' in line:
                check('Preflight etico', False, line.strip())
        if 'APROVADO' in out or 'DESATIVADO' in out:
            check('Preflight etico aprovado', True)
        else:
            check('Preflight etico aprovado', False, 'saida sem APROVADO/DESATIVADO')
    except Exception as e:
        check('Preflight etico', False, str(e)[:200])

    # 8. JSON Sanitization (hardcoded paths regression)
    print('\n[8] JSON Sanitization (hardcoded paths)')
    try:
        import subprocess as sp
        r = sp.run([sys.executable, os.path.join(BASE, 'scripts', 'test_json_sanitization.py')],
                   capture_output=True, text=True, timeout=60, cwd=BASE)
        out = (r.stdout + r.stderr).strip()
        for line in out.splitlines():
            if '[FAIL]' in line:
                check('JSON sanitization', False, line.strip())
        if r.returncode == 0:
            # Extract pass count from output
            import re
            m = re.search(r'Pass:\s*(\d+)', out)
            total = re.search(r'Total.*?:\s*(\d+)', out)
            if m and total:
                check(f'JSON sanitization ({m.group(1)}/{total.group(1)} clean)', True)
            else:
                check('JSON sanitization', True)
        else:
            check('JSON sanitization', False, f'exit code {r.returncode}')
    except Exception as e:
        check('JSON sanitization', False, str(e)[:200])

    # 9. Voz Guarda (fixed temp audio paths regression)
    print('\n[9] Voz Guarda (temp audio paths)')
    try:
        r = sp.run([sys.executable, os.path.join(BASE, 'scripts', 'voz_guarda.py'), '--check'],
                   capture_output=True, text=True, timeout=60, cwd=BASE)
        try:
            data = json.loads(r.stdout)
            ok = data.get('ok', False)
            violacoes = data.get('violacoes', [])
            n = len(violacoes)
            if ok:
                check('Voz Guarda (0 violacoes, speech_pipeline com mkstemp)', True)
            elif n:
                primeira = violacoes[0]
                check('Voz Guarda', False,
                      f'{n} violacao(es), ex: {primeira.get("arquivo")}:{primeira.get("linha")} {primeira.get("fixado")}')
            else:
                check('Voz Guarda', False, 'speech_pipeline sem mkstemp (correcao revertida)')
        except Exception:
            if r.returncode == 0:
                check('Voz Guarda', True)
            else:
                check('Voz Guarda', False, f'exit code {r.returncode}')
    except Exception as e:
        check('Voz Guarda', False, str(e)[:200])

    # Summary
    print('\n========================================')
    if not ERRORS:
        print('  RESULTADO: TODOS TESTES PASSARAM')
        print('  Pode aplicar a alteracao com seguranca.')
    else:
        print(f'  RESULTADO: {len(ERRORS)} ERRO(S)')
        for e in ERRORS:
            print(f'    [ERR] {e}')
        print('  ALTERACAO BLOQUEADA. Corrija os erros antes de aplicar.')
    print('========================================')
    
    # Log execução para métricas de aderência
    log_preflight_execution('tecnico', len(ERRORS) == 0, len(ERRORS))
    
    return len(ERRORS) == 0

if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)
